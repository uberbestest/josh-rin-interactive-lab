"""Same-author presentation tests; not a game-build or agent evaluation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, http.server, socketserver, threading, re, shutil
from playwright.sync_api import sync_playwright
P=Path(__file__).resolve().parent
ROOT=P.parents[1]
OUT=P/'review';OUT.mkdir(exist_ok=True)
prov=json.loads((P/'provenance.json').read_text())
assert hashlib.sha256((P/prov['public_asset']['path']).read_bytes()).hexdigest()==prov['public_asset']['sha256']
html=(P/'index.html').read_text(); home=(ROOT/'index.html').read_text()
assert 'No browser-playable build is released here' in html
assert 'not proof of movement' in html
assert 'Current build verified' not in html
assert home.count('id="major-projects"')==1
assert home.count('projects/rle-castle/index.html')>=3
assert '10 instruments' in home
assert all(x not in html.lower() for x in ['purgatory','c:\\users','api_key'])
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*a,**k):super().__init__(*a,directory=str(ROOT),**k)
    def log_message(self,*a):pass
checks=[];errors=[];bad=[]
with socketserver.TCPServer(('127.0.0.1',0),Handler) as server:
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_address[1]}'
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=shutil.which('chromium'),args=['--no-sandbox'])
        for width in [320,390,768,1440]:
            page=browser.new_page(viewport={'width':width,'height':1000},reduced_motion='reduce')
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('response',lambda r:bad.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            resp=page.goto(base+'/projects/rle-castle/index.html',wait_until='networkidle')
            assert resp.status==200
            assert page.locator('h1').count()==1
            assert page.locator('.capture img').evaluate('(e)=>e.complete && e.naturalWidth===575 && e.naturalHeight===200')
            assert page.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')<=1
            assert page.locator('a').filter(has_text='Play now').count()==0
            dupe=page.evaluate('''() => {const a=[...document.querySelectorAll('[id]')].map(e=>e.id);return a.filter((x,i)=>a.indexOf(x)!==i)}''')
            assert not dupe,dupe
            page.screenshot(path=str(OUT/f'project-{width}.png'),full_page=(width in [390,1440]))
            page.locator('summary').focus(); page.keyboard.press('Enter')
            assert page.locator('details').evaluate('(e)=>e.open')
            page.locator('a[href="../../index.html#major-projects"]').click()
            assert page.locator('#major-projects').is_visible()
            assert page.locator('#experiments .card').count()==10
            assert page.locator('.castle-project img').evaluate('(e)=>e.complete && e.naturalWidth===575')
            assert page.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')<=1
            # Existing instrument filters remain separate from project presentation.
            page.locator('[data-filter="attention"]').click()
            assert page.locator('#experiments .card:visible').count()==1
            assert page.locator('#major-projects').is_visible()
            page.locator('[data-filter="all"]').click()
            assert page.locator('#experiments .card:visible').count()==10
            page.locator('#major-projects').screenshot(path=str(OUT/f'homepage-project-{width}.png'))
            checks.append({'viewport':width,'status':'PASS','image_loaded':True,'horizontal_overflow':False,'project_separate_from_10_instruments':True,'evidence_disclosure_keyboard':True})
            page.close()
        page=browser.new_page(java_script_enabled=False,viewport={'width':390,'height':900})
        page.goto(base+'/projects/rle-castle/index.html')
        page.locator('summary').click();assert page.locator('details').evaluate('(e)=>e.open')
        assert page.locator('img').evaluate('(e)=>e.complete && e.naturalWidth>0')
        page.close();browser.close()
    server.shutdown()
assert not errors, errors
assert not bad,bad
receipt={'status':'PASS','timestamp_utc':datetime.now(timezone.utc).isoformat(),'scope':'Same-author Chromium presentation checks over localhost HTTP; no current game launch or independent research review','image_sha256':prov['public_asset']['sha256'],'checks':checks,'no_javascript_required':True,'javascript_errors':errors,'failed_http_responses':bad}
(P/'BROWSER-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
