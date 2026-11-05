"""Optional Chromium checks and full-support Python/JS parity.

Setup: pip install playwright && playwright install chromium
Run: python browser_checks.py
An existing browser may be selected with --chromium /path/to/chromium.
This serves ONLY this exhibit locally. It does not access a signed-in browser.
"""
from __future__ import annotations
import argparse, csv, gzip, json, threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from fractions import Fraction as F
from playwright.sync_api import sync_playwright
import engine as E

HERE=Path(__file__).resolve().parent
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

def main(browser_path=None, output=HERE/'verification'/'browser.json', inline=False):
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(HERE)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    checks=[]
    def check(condition,label):
        checks.append({'check':label,'passed':bool(condition)})
        if not condition: raise AssertionError(label)
    try:
      with sync_playwright() as pw:
        opts={'headless':True,'args':['--no-sandbox']}
        if browser_path: opts['executable_path']=browser_path
        browser=pw.chromium.launch(**opts)
        context=browser.new_context(viewport={'width':1365,'height':1000},device_scale_factor=1)
        page=context.new_page();errors=[];requests=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:requests.append(r.url))
        base=f'http://127.0.0.1:{server.server_port}/'
        def load(target, name):
            if not inline:
                target.goto(base+name,wait_until='networkidle')
                return
            # Render our own local files as an inline document; no URL access.
            doc=(HERE/name).read_text(encoding='utf-8')
            doc=doc.replace('<link rel="stylesheet" href="style.css">','<style>'+(HERE/'style.css').read_text()+'</style>')
            for src in ('engine.js','results-data.js','app.js'):
                doc=doc.replace('<script src="'+src+'"></script>','<script>'+(HERE/src).read_text().replace('</script',r'<\/script')+'</script>')
            target.set_content(doc,wait_until='load')
        load(page, 'index.html')
        check(page.evaluate('window.BREAD_UI_READY===true'),'UI initialized')
        check(page.locator('#reports .goblin').count()==10,'ten displayed reports')
        check(not page.locator('#receipts').is_visible(),'receipts initially hidden')
        page.locator('#trace').click()
        check(page.locator('#receipts').is_visible(),'trace reveals provenance')
        check(page.locator('#reports .origin').all_text_contents()==['Source A']*10,'all copied reports traced to A')
        page.screenshot(path=str(output.parent/'desktop.png'),full_page=True)
        page.locator('[data-action="buy"]').click()
        check('do not support' in page.locator('#feedback h4').inner_text(),'overconfident purchase flagged')
        check('-9' in page.locator('#feedback').inner_text(),'realized wrong-purchase payoff shown')
        check(page.locator('[data-action]:disabled').count()==3,'choice locked after outcome')
        for n,action in [(2,'hold'),(3,'hold'),(4,'buy'),(5,'buy'),(1,'hold')]:
            page.locator('#next-round').click()
            check(f'{n:02d} / 05' in page.locator('#round-count').inner_text(),f'round {n} navigates')
            page.locator(f'[data-action="{action}"]').click()
            check('model-supported decision' in page.locator('#feedback h4').inner_text(),f'round {n} expected action supported')
        for topo,weights in E.TOPOLOGIES.items():
            page.locator('#topology').select_option(topo)
            check(page.locator('#roots button').count()==len(weights),f'{topo}: root controls count')
            before=page.locator('#roots button').first.get_attribute('aria-pressed')
            page.locator('#roots button').first.click()
            check(page.locator('#roots button').first.get_attribute('aria-pressed')!=before,f'{topo}: root toggles')
            page.locator('#all-fresh').click()
        page.locator('#topology').select_option('loud_minority')
        page.locator('[data-root="1"]').click();page.locator('[data-root="2"]').click()
        check(page.locator('[data-rule="receipts"] .prob').inner_text()=='20.00%','loud minority receipt estimate is 20%')
        page.locator('#topology').select_option('ten_roots')
        page.locator('#shared').focus();page.locator('#shared').press('End')
        check('85.00%' in page.locator('[data-rule="shared_cause"] .prob').inner_text(),'shared-cause ceiling visible')
        check('HOLD' in page.locator('[data-rule="shared_cause"] .verdict').inner_text(),'shared-cause rule holds')
        for acc in ('90','80','70'):
          page.locator('#result-accuracy').select_option(acc)
          for shared in ('0','25','50','75'):
            page.locator('#result-shared').select_option(shared)
            for metric in ('brier','coverage','decisive_accuracy','wrong_mass','payoff'):
              page.locator('#metric').select_option(metric)
              check(page.locator('#results-body tr').count()==6,f'results render {acc}/{shared}/{metric}')
        page.locator('#result-accuracy').select_option('80');page.locator('#result-shared').select_option('75');page.locator('#metric').select_option('decisive_accuracy')
        check(page.locator('#results-body tr').last.locator('td').last.inner_text()=='—','no-decision accuracy is a dash')
        cm={c.id:c for c in E.cells()};parity=[]
        with gzip.open(HERE/'histories.csv.gz','rt',encoding='utf-8') as f:
          for row in csv.DictReader(f):
            c=cm[row['cell']]
            parity.append([[int(b) for b in row['root_bits']],c.copies,float(c.marginal),float(c.shared),[float(F(row['p_'+r])) for r in E.RULES],[row['action_'+r] for r in E.RULES]])
        total=0;max_error=0
        for start in range(0,len(parity),4000):
          result=page.evaluate('''rows=>{let max=0;for(const [bits,weights,r,q,ps,acts] of rows){const p=BreadEngine.predict(bits,weights,r,q);BreadEngine.rules.forEach((rule,i)=>{const err=Math.abs(p[rule]-ps[i]);max=Math.max(max,err);if(err>1e-12 || BreadEngine.decide(p[rule])!==acts[i])throw Error('Parity mismatch');});}return {count:rows.length,max};}''',parity[start:start+4000])
          total+=result['count'];max_error=max(max_error,result['max'])
        check(total==45612,'full recorded support checked in Chromium')
        check(page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'no desktop horizontal page overflow')
        mobile=context.new_page();mobile.set_viewport_size({'width':375,'height':812});mobile.on('pageerror',lambda e:errors.append(str(e)))
        load(mobile, 'index.html')
        check(mobile.evaluate('document.documentElement.scrollWidth<=innerWidth'),'no 375px horizontal page overflow')
        mobile.locator('#trace').click();mobile.locator('[data-action="hold"]').click()
        check('model-supported' in mobile.locator('#feedback h4').inner_text(),'mobile trace and decision work')
        mobile.screenshot(path=str(output.parent/'mobile.png'),full_page=True)
        mobile.set_viewport_size({'width':320,'height':700})
        check(mobile.evaluate('document.documentElement.scrollWidth<=innerWidth'),'no 320px horizontal page overflow')
        load(mobile, 'method.html')
        check(mobile.locator('h1').count()==1,'methods page renders')
        check(mobile.evaluate('document.documentElement.scrollWidth<=innerWidth'),'methods page fits 320px')
        check(not errors,'no JavaScript page errors')
        check(all(url.startswith(base) for url in requests),'exhibit makes only same-origin local requests')
        context.close();browser.close()
      receipt={'status':'PASS','ui_checks':len(checks),'checks':checks,'browser_parity_histories':total,
               'browser_probability_and_action_comparisons':total*3,'max_absolute_probability_error':max_error,
               'viewports':[[1365,1000],[375,812],[320,700]],'page_errors':errors,'render_mode':'inline_local_document' if inline else 'local_http', 'scope':'Local Chromium only. No live deployment checked. Inline mode renders generated local content without URL navigation.'}
      output.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
      print(json.dumps({k:v for k,v in receipt.items() if k not in ('checks',)},indent=2))
    finally: server.shutdown();server.server_close()
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--chromium');ap.add_argument('--inline',action='store_true',help='Render authored local files inline without HTTP navigation');ap.add_argument('--output',type=Path,default=HERE/'verification'/'browser.json');a=ap.parse_args();main(a.chromium,a.output,a.inline)
