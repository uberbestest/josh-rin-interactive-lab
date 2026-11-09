"""Publication-time HTTP presentation check; separate from original browser receipts."""
from __future__ import annotations
import datetime, functools, hashlib, http.server, json, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'experiments/test-that-watched-back'
OUT=D/'verification/publication';OUT.mkdir(parents=True,exist_ok=True)
class QuietHandler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(ROOT)))
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
base=f'http://127.0.0.1:{server.server_port}/';url=base+'experiments/test-that-watched-back/'
errors=[];outside=[];bad_responses=[];checks=[]
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  for width,height,label in [(1365,1000,'desktop'),(390,844,'mobile')]:
   page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.on('request',lambda r:outside.append(r.url) if not r.url.startswith(base) else None)
   page.on('response',lambda r:bad_responses.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
   response=page.goto(url+'index.html',wait_until='networkidle')
   if response.status!=200:raise RuntimeError('Explorer HTTP failed')
   assert page.locator('#publication-nav').count()==1
   assert page.locator('#publication-downloads').count()==1
   assert page.locator('#policy-results tbody tr').count()==6
   assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
   before=page.locator('#policy-results tbody tr').nth(3).locator('td').nth(1).inner_text()
   assert before.startswith('1') and 'Truthful' in before
   page.locator('#flip-future').click()
   after=page.locator('#policy-results tbody tr').nth(3).locator('td').nth(1).inner_text()
   assert after.startswith('0') and 'False report' in after
   assert page.locator('#policy-results tbody tr').nth(4).locator('td').nth(1).inner_text()==after
   page.locator('#suite').select_option('challenge')
   assert page.locator('#flip-future').is_disabled()
   assert page.locator('#audit option').count()==4
   page.locator('#load-witness').click()
   assert page.locator('#suite').input_value()=='primary'
   assert page.locator('#continuation').input_value()=='6'
   assert page.locator('#panel-signatures tr').count()==6
   counts=page.evaluate('''() => {
    let contexts=0,reports=0;
    for(const [id,c] of Object.entries(DATA.contexts)){
     const suite=id.startsWith('primary')?'primary':'challenge';
     document.getElementById('suite').value=suite;configure(suite,c.view);
     const rr=document.querySelectorAll('#policy-results tbody tr');
     for(let i=0;i<6;i++){
      const td=rr[i].querySelectorAll('td');
      if(td[1].querySelector('strong').textContent!==String(c.policies[i].report))throw Error('report mismatch '+id);
      if(td[2].querySelector('small').textContent!==c.policies[i].pass)throw Error('pass mismatch '+id);
      reports++;
     }contexts++;
    }return {contexts,reports};
   }''')
   assert counts=={'contexts':432,'reports':2592}
   page.locator('#load-witness').click();page.evaluate('scrollTo(0,0)')
   page.screenshot(path=str(OUT/f'{label}_top.png'),full_page=False)
   page.locator('.lab').screenshot(path=str(OUT/f'{label}_controls.png'))
   for name in ('method.html','portfolio.html'):
    r=page.goto(url+name,wait_until='networkidle');assert r.status==200
    assert page.locator('h1').count()==1
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),name+' page overflow'
   page.goto(base+'index.html',wait_until='networkidle')
   assert page.locator('#test-that-watched-back').count()==1
   assert page.locator('#test-that-watched-back h3').inner_text()=='The Test That Watched Back'
   assert page.locator('#test-that-watched-back a.open').get_attribute('href')=='experiments/test-that-watched-back/index.html'
   assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),'Gallery overflow'
   checks.append({'viewport':label,'width':width,'height':height,'http_status':200,'navigation_and_download_links_present':True,'no_page_overflow':True,'future_witness_toggle':'PASS','lookup_equality':'PASS','suite_switch':'PASS','retained_data_checks':counts,'methods_and_portfolio':'PASS','gallery_entry':'PASS'})
   page.close()
  browser.close()
finally:
 server.shutdown();server.server_close()
assert not errors,errors
assert not outside,outside
assert not bad_responses,bad_responses
receipt={'status':'PASS','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'javascript_errors':errors,'external_requests':outside,'failed_http_responses':bad_responses,'published_index_sha256':hashlib.sha256((D/'index.html').read_bytes()).hexdigest(),'qualification':'Fresh Chromium/Linux check of HTTP-served staging files in the publication runner. Not the original authored-string captures, not native Windows, not all mobile browsers, and not independent scientific validation.'}
(OUT/'browser.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps(receipt,indent=2))
