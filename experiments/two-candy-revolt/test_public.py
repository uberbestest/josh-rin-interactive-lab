#!/usr/bin/env python3
"""Real Chromium release checks plus a separate replay-to-raw comparison.
Use CHROMIUM_PATH to select a local system browser; otherwise Playwright's browser.
"""
import hashlib, json, os, re, threading
from datetime import datetime,timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import numpy as np
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent
checks=[]
def check(name,cond):
 if not cond:raise AssertionError(name)
 checks.append(name)
markup=(ROOT/'index.html').read_text()
data=json.loads(re.search(r'<script id="research-data" type="application/json">(.*?)</script>',markup,re.S).group(1))
fields=['action','accept','proposer','receiver']
with np.load(ROOT/'results/primary/evaluation_trace.npz',allow_pickle=False) as z:
 for i,k in enumerate(fields):check('every evaluation '+k,np.array_equal(np.asarray(data['replay'])[:,:,:,i],z[k][:30].reshape(30,24,64).transpose(1,2,0)))
with np.load(ROOT/'results/primary/training_trace.npz',allow_pickle=False) as z:
 for w in data['trainingWindows']:
  t=w['start_round']-1
  for i,k in enumerate(fields):check('every '+w['label']+' training '+k,np.array_equal(np.asarray(w['replay'])[:,:,:,i],z[k][t:t+30].reshape(30,24,64).transpose(1,2,0)))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
errors=[];external=[]
try:
 with sync_playwright() as p:
  kwargs={'headless':True,'args':['--no-sandbox']}
  if os.environ.get('CHROMIUM_PATH'):kwargs['executable_path']=os.environ['CHROMIUM_PATH']
  browser=p.chromium.launch(**kwargs);page=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True)
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('request',lambda r:external.append(r.url) if not r.url.startswith(('http://127.0.0.1:','blob:','data:')) else None)
  if os.environ.get('CANDY_TEST_INJECT'):
   page.set_content(markup,wait_until='load');check('injected HTML loads',page.locator('#tldr').is_visible())
  else:
   response=page.goto(f'http://127.0.0.1:{server.server_port}/index.html');check('HTTP page loads',response.status==200)
  check('TLDR precedes experiment',page.locator('#tldr').bounding_box()['y']<page.locator('#replay').bounding_box()['y'])
  check('default recorded learning',page.input_value('#replayMode')=='training')
  check('default first training window',page.input_value('#trainingWindow')=='0')
  check('default round bags',page.locator('#highBag').inner_text().startswith('3\n') and page.locator('#lowBag').inner_text().startswith('7\n'))
  page.click('#play');page.wait_for_timeout(80);page.click('#play')
  check('Play visibly changes bags',page.locator('#highBag').inner_text().startswith('0\n') and page.locator('#lowBag').inner_text().startswith('3\n'))
  paused=page.input_value('#night');page.wait_for_timeout(1500);check('pause stops timer',page.input_value('#night')==paused)
  check('cumulative replay reflects first two records',page.locator('#highCumulative').inner_text()=='3' and page.locator('#lowCumulative').inner_text()=='10')
  page.click('#prev');check('rewind resets cumulative',page.locator('#highCumulative').inner_text()=='3' and page.locator('#lowCumulative').inner_text()=='7')
  page.evaluate("goToReceipt(29)");check('last receipt says Replay',page.locator('#play').inner_text()=='Replay')
  page.click('#play');page.wait_for_timeout(60);page.click('#play');check('restart reaches first record',page.input_value('#night')=='0')
  # Read actual rendered DOM, not merely a successful counter increment.
  coverage=page.evaluate('''() => {
   let cases=0;const failures=[];
   for(let ci=0;ci<DATA.cells.length;ci++) for(const si of [0,31,63]) for(const mode of [-1,0,1,2]) for(const night of [0,14,29]){
    const c=DATA.cells[ci];for(const k of ['institution','contract','objective','outside'])$(k).value=c[k];
    $('seed').value=si;$('replayMode').value=mode===-1?'evaluation':'training';$('trainingWindow').value=mode===-1?0:mode;$('night').value=night;render();
    const seq=mode===-1?DATA.replay[ci][si]:DATA.trainingWindows[mode].replay[ci][si];const r=seq[night];
    const high=parseFloat($('highBag').textContent),low=parseFloat($('lowBag').textContent);
    const hc=seq.slice(0,night+1).reduce((a,x)=>a+x[2],0),lc=seq.slice(0,night+1).reduce((a,x)=>a+x[3],0);
    if(high!==r[2]||low!==r[3]||Number($('highCumulative').textContent)!==hc||Number($('lowCumulative').textContent)!==lc||Number($('allTotal').textContent)!==33+r[2]+r[3])failures.push([ci,si,mode,night]);cases++;
   }return {cases,failures};
  }''')
  check('864 DOM replay/cumulative/accounting cases',coverage['cases']==864 and not coverage['failures'])
  page.evaluate("$('institution').value='veto';$('contract').value='escrow';$('objective').value='personal';$('outside').value='3';$('seed').value='0';$('replayMode').value='evaluation';goToReceipt(0)")
  check('frozen evaluation repetition explained','identical' in (page.locator('#receiptNote').inner_text()+page.locator('#modeNote').inner_text()+page.locator('#replayFootnote').inner_text()).lower() or 'same bargain' in page.locator('#modeNote').inner_text().lower())
  with page.expect_download() as event:page.click('#exportReplay')
  dl=event.value;path=ROOT/'results/public-replay-export.json';dl.save_as(path)
  check('export is JSON',isinstance(json.loads(path.read_text()),dict))
  page.select_option('#manualDecision','reject');page.select_option('#manualHonor','no');page.locator('#manualOffer').fill('3');page.locator('#manualOffer').dispatch_event('input')
  veto_text=page.locator('#calcResult').inner_text();check('veto calculator returns zero proposer','0' in veto_text and '3' in veto_text)
  page.select_option('#institution','exit_only');check('exit calculator leaves proposer eight','8' in page.locator('#calcResult').inner_text())
  page.select_option('#institution','no_refusal');check('forced acceptance explained','overrid' in page.locator('#calcResult').inner_text().lower() or 'accept' in page.locator('#calcResult').inner_text().lower())
  page.evaluate("$('institution').value='veto';$('contract').value='escrow';$('objective').value='personal';$('outside').value='3';$('replayMode').value='training';$('trainingWindow').value='0';goToReceipt(0)")
  shot=ROOT/'screenshots';shot.mkdir(exist_ok=True)
  for width in [320,390,768,1440]:
   page.set_viewport_size({'width':width,'height':1000 if width>=768 else 844})
   page.evaluate("document.documentElement.style.scrollBehavior='auto';window.scrollTo(0,0)");page.wait_for_timeout(120)
   check(f'no page overflow at {width}',page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'))
   if width in [390,1440]:page.screenshot(path=str(shot/f'public-{width}.png'))
  page.locator('#replay').scroll_into_view_if_needed();page.screenshot(path=str(shot/'public-replay-desktop.png'))
  page.emulate_media(reduced_motion='reduce');check('reduced motion respected',page.evaluate("getComputedStyle(document.querySelector('.receipt-progress div')).transitionDuration==='0s'"))
  if os.environ.get('CANDY_TEST_INJECT'):
   page.set_content((ROOT/'method.html').read_text());check('injected methods load',page.locator('main').is_visible())
  else:
   methods=page.goto(f'http://127.0.0.1:{server.server_port}/method.html');check('methods load',methods.status==200)
  check('methods include negative result','negative result' in page.inner_text('body').lower())
  check('no JavaScript exceptions',not errors);check('no external runtime requests',not external)
  browser.close()
finally:server.shutdown();server.server_close()
receipt={'status':'PASS','timestamp_utc':datetime.now(timezone.utc).isoformat(),'browser':('Actual headless Chromium via Playwright; HTML injected because local navigation is restricted; not a mock DOM' if os.environ.get('CANDY_TEST_INJECT') else 'Actual headless Chromium via Playwright; localhost HTTP, not mock DOM'),'checks_passed':len(checks),'checks':checks,'raw_records_compared':184320,'dom_replay_cases':coverage['cases'],'viewport_widths':[320,390,768,1440],'javascript_errors':errors,'external_runtime_requests':external,'independent_review':False,'limits':'Author-run checks. No claim about the user app preview, every browser engine, or an independent reviewer.'}
(ROOT/'results/public-browser-tests.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
