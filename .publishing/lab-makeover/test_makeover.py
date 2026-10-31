#!/usr/bin/env python3
"""Author-run real-browser presentation checks; not independent research review."""
from pathlib import Path
from datetime import datetime, timezone
import http.server
import json
import re
import socketserver
import subprocess
import threading
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'assets/lab/review'
OUT.mkdir(parents=True,exist_ok=True)
errors=[]
failures=[]
checks=[]
BASE='e9a1edc8c64b29d766b286f778fe2a553c66235f'

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def log_message(self,*args):pass

oldhub=subprocess.check_output(['git','show',BASE+':agent-attention/index.html'],cwd=ROOT).decode()
newhub=(ROOT/'agent-attention/index.html').read_text()
assert re.findall(r'<script[\s\S]*?</script>',oldhub)==re.findall(r'<script[\s\S]*?</script>',newhub)
checks.append('Agent Attention JavaScript and embedded trace unchanged byte-for-byte')

with socketserver.TCPServer(('127.0.0.1',0),Handler) as server:
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base='http://127.0.0.1:'+str(server.server_address[1])
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
        for width in [320,390,768,1440]:
            page=browser.new_page(viewport={'width':width,'height':1050},reduced_motion='reduce')
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('response',lambda r:failures.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            assert page.goto(base+'/index.html',wait_until='networkidle').status==200
            assert page.locator('h1').count()==1
            assert page.locator('.card').count()==10
            # ViewBox-only SVGs may have a 300x110 intrinsic size; verify content/aspect.
            assert page.locator('.lab-picture').evaluate('(e)=>e.complete && e.naturalWidth>0 && Math.abs(e.naturalWidth/e.naturalHeight-1200/440)<0.01')
            duplicate=page.evaluate('''() => {const a=[...document.querySelectorAll('[id]')].map(e=>e.id);return a.filter((x,i)=>a.indexOf(x)!==i)}''')
            assert not duplicate,duplicate
            assert page.locator('#agent-attention a[href="agent-attention/index.html"]').count()>=1
            overflow=page.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')
            assert overflow<=1,(width,overflow)
            page.screenshot(path=str(OUT/f'home-{width}.png'))
            if width in [390,1440]:
                page.screenshot(path=str(OUT/f'home-{width}-full.png'),full_page=True)
            page.locator('[data-filter="attention"]').click()
            assert page.locator('#experiments .card:visible').count()==1
            assert '1 of 10' in page.locator('#labFilterStatus').inner_text()
            page.locator('[data-filter="incentives"]').click()
            assert page.locator('#experiments .card:visible').count()==2
            page.locator('[data-filter="all"]').click()
            assert page.locator('#experiments .card:visible').count()==10
            evidence=page.locator('.lab-evidence').first
            evidence.locator('summary').focus()
            page.keyboard.press('Enter')
            assert evidence.evaluate('(e)=>e.open')
            page.locator('#puddleHello').click()
            assert 'receipts' in page.locator('#puddleMessage').inner_text()
            assert page.locator('.support-button').count()==1
            assert page.locator('.support-button').get_attribute('href').startswith('https://cash.app/')
            page.goto(base+'/agent-attention/index.html',wait_until='networkidle')
            assert page.locator('.lab-research-ribbon img').evaluate('(e)=>e.complete && e.naturalWidth>0')
            assert page.locator('#eventNav button').count()==15
            page.locator('#next').click()
            assert page.locator('#detailMeta').inner_text().startswith('E02')
            page.locator('#eventNav button').nth(14).click()
            assert 'N03' in page.locator('#detailNote').inner_text()
            overflow=page.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')
            assert overflow<=1,('hub',width,overflow)
            page.evaluate('window.scrollTo(0,0)')
            page.screenshot(path=str(OUT/f'attention-{width}.png'))
            checks.append(f'Width {width}: art, one h1, unique ids, 10 cards, 3 filters, keyboard evidence, Puddle, support, map controls, no overflow')
            page.close()
        nojs=browser.new_page(java_script_enabled=False,viewport={'width':390,'height':900})
        nojs.goto(base+'/index.html',wait_until='load')
        assert nojs.locator('.card:visible').count()==10
        assert nojs.locator('#labFilters').is_hidden()
        assert nojs.locator('#puddleHello').is_hidden()
        nojs.locator('.lab-evidence summary').first.click()
        assert nojs.locator('.lab-evidence').first.evaluate('(e)=>e.open')
        checks.append('No-JavaScript: all instruments available, native evidence disclosure works, optional controls hidden')
        nojs.close()
        browser.close()
    server.shutdown()
assert not errors,errors
assert not failures,failures
receipt={
    'status':'PASS',
    'timestamp_utc':datetime.now(timezone.utc).isoformat(),
    'kind':'Author-run Chromium checks, local HTTP, reduced motion',
    'checks':checks,
    'viewport_widths':[320,390,768,1440],
    'javascript_errors':errors,
    'failed_http_responses':failures,
    'independent_review':False,
    'user_visual_review':'Pending',
    'screenshots':'assets/lab/review/'
}
(ROOT/'assets/lab/BROWSER-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
