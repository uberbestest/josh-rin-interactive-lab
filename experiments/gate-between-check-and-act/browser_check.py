#!/usr/bin/env python3
"""HTTP browser checks for the actual rendered exhibit; Playwright optional."""
from __future__ import annotations
import contextlib, functools, http.server, json, os, shutil, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
import study
ROOT=Path(__file__).resolve().parent
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}'
checks=[]; errors=[]
offline=os.environ.get('OFFLINE_RENDER')=='1'
def load(page,name):
    if not offline:
        return page.goto(base+'/'+name)
    text=(ROOT/name).read_text()
    if name=='index.html':
        text=text.replace('<script src="explorer.js"></script>','<script>'+(ROOT/'explorer.js').read_text()+'</script>')
        text=text.replace("fetch('results/summary.json')","Promise.resolve({ok:true,json:()=>Promise.resolve("+(ROOT/'results/summary.json').read_text()+")})")
    page.set_content(text,wait_until='load')
    return None
def need(ok, label):
    if not ok: raise RuntimeError(label)
    checks.append(label)
try:
 with sync_playwright() as p:
    launch={'headless':True}
    path=os.environ.get('CHECK_BROWSER_PATH') or shutil.which('chromium')
    if path: launch['executable_path']=path
    browser=p.chromium.launch(**launch)
    page=browser.new_page(viewport={'width':1280,'height':950},color_scheme='light')
    page.on('pageerror',lambda err:errors.append(str(err)))
    response=load(page,'index.html');need(offline or response.status==200,'index in-memory render' if offline else 'index HTTP 200')
    page.wait_for_selector('#aggregate tbody tr');page.wait_for_function("document.querySelector('#frontier-result').textContent.includes('256/256')")
    need(page.locator('#aggregate tbody tr').count()==9,'all nine aggregate rows')
    metrics=lambda:page.locator('#outcomes b').all_text_contents()
    need(metrics()==['Yes','1','0','6'],'default blocked-race witness')
    page.click('#repair');need(metrics()==['Yes','0','0','6'],'timing-matched conditional witness')
    page.click('#repair');page.select_option('#mode','observe');need(metrics()==['No','1','1','2'],'unblocked unsafe effect witness')
    for L in range(3):
      for policy in study.POLICIES:
       for mode in ('block','observe'):
        page.select_option('#lag',str(L));page.select_option('#policy',policy);page.select_option('#mode',mode)
        c=study.Config(lag=L);w=next(w for w in study.worlds(c) if w.name=='10000000')
        cb=study.Solver(study.Config(lag=L,interface=policy[7:])).act if policy.startswith('belief_') else None
        r=study.simulate(c,w,policy,mode,cb)
        need(metrics()==['Yes' if r['legitimate_completion'] else 'No',str(r['forbidden_raw_requests']),str(r['unauthorized_effects']),str(r['terminal_tick'])],f'controls {L}/{policy}/{mode}')
    page.select_option('#H','3');page.select_option('#K','4');page.select_option('#B','1');page.select_option('#L','0')
    text=page.locator('#frontier-result').inner_text();need('0/4' in text and '3/4' in text,'tight infeasible-main frontier')
    page.select_option('#H','4');text=page.locator('#frontier-result').inner_text();need(text.count('5/5')==2 and text.count('mean terminal tick 4')==2,'exact-fit deadline frontier')
    page.select_option('#H','5');need('5/3' in page.locator('#frontier-result').inner_text(),'one-spare-tick formula')
    with page.expect_download() as dl: page.click('#download')
    download=dl.value;path=ROOT/'browser-trace.json';download.save_as(path)
    need(json.loads(path.read_text())['schedule']=='10000000','downloaded JSON trace');path.unlink()
    shots=ROOT/'screenshots';shots.mkdir(exist_ok=True)
    page.select_option('#lag','0');page.select_option('#policy','inspect_once');page.select_option('#mode','block')
    for width,theme in [(1280,'light'),(390,'light'),(390,'dark')]:
        page.set_viewport_size({'width':width,'height':950});page.evaluate('(v)=>document.documentElement.dataset.theme=v',theme)
        need(page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'no horizontal body overflow {width}/{theme}')
        page.screenshot(path=str(shots/f'index-{width}-{theme}.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':900});load(page,'method.html')
    need(page.locator('h1').count()==1,'methods title')
    need(page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'methods mobile no overflow')
    need(page.locator('#proof').count()==1 and page.locator('#sources').count()==1,'methods target anchors')
    need(not errors,'no browser JavaScript errors')
    browser.close()
finally: server.shutdown()
receipt={'status':'PASS','transport':'in-memory local render' if offline else 'HTTP','checks':len(checks),'checks_passed':checks,'errors':errors,'tested_surfaces':['1280 light','390 light','390 dark','390 methods'],'note':'Same-author browser smoke checks; not accessibility certification or independent review.'}
(ROOT/'browser-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':'PASS','checks':len(checks),'errors':errors}))
