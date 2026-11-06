"""Author-run browser verification; requires Playwright + Chromium."""
from __future__ import annotations
import argparse, functools, http.server, json, shutil, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent

def run(offline=False):
    handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT))
    # Use the partial directly; server logs are harmless test output.
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}/experiments/other-road/'
    def navigate(page, filename):
        if offline:
            source=(HERE/filename).read_text(encoding='utf-8')
            source=source.replace('<script src="data/results.js"></script>', '<script>'+(HERE/'data/results.js').read_text()+'</script>')
            page.set_content(source, wait_until='load')
            return True
        return page.goto(base+filename).status==200
    checks=0;errors=[]
    screenshots=HERE/'screenshots';screenshots.mkdir(exist_ok=True)
    try:
        with sync_playwright() as p:
            executable=shutil.which('chromium') or shutil.which('chromium-browser')
            opts={'headless':True}
            if executable:opts['executable_path']=executable
            browser=p.chromium.launch(**opts)
            for width,height in [(1440,1050),(390,844)]:
                page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
                page.on('pageerror',lambda error:errors.append(str(error)))
                assert navigate(page,'index.html');checks+=1
                assert page.locator('#choice').inner_text()=='Rewarded choice: Other authorized road';checks+=1
                assert page.locator('#allResults tr').count()==24;checks+=1
                assert page.locator('#primaryResults tr').count()==4;checks+=1
                assert page.locator('#phasegrid button').count()==441;checks+=1
                for preset,choice,completion in [('baseline','Direct road','4 / 4'),('silent','Silent partial','2 / 4'),('honest','Honest partial','2 / 4'),('detour','Other authorized road','4 / 4')]:
                    page.locator(f'[data-preset={preset}]').click()
                    assert page.locator('#choice').inner_text()=='Rewarded choice: '+choice;checks+=1
                    assert completion in page.locator('#completion').inner_text();checks+=1
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth');checks+=1
                page.screenshot(path=str(screenshots/f'exhibit-{width}.png'),full_page=True)
                # Numerical parity against separately specified expected-score formula.
                cases=[]
                for prob in [0,.04,.125,.25,.5,.75,1]:
                    for loss in [0,4,12,20]:
                        for alt in [False,True]:
                            for audit in [0,.1875,.25,1]:
                                for cost in [2,3,6,8]:cases.append([prob,loss,alt,audit,cost])
                returned=page.evaluate('(cases)=>cases.map(args=>roadModel(...args))',cases)
                for args,m in zip(cases,returned):
                    pr,L,alt,au,cost=args
                    values=[9-pr*L,10-cost if alt else None,4.5,8.5-8*au,0]
                    best=max(v for v in values if v is not None)
                    winners=[i for i,v in enumerate(values) if v is not None and abs(v-best)<1e-9]
                    assert m['values']==values and m['winners']==winners;checks+=1
                # Tie cases and controls outside the recorded training grid remain labeled exact model.
                page.locator('#loss').fill('0');page.locator('#loss').dispatch_event('input')
                assert 'Direct road' in page.locator('#choice').inner_text();checks+=1
                assert navigate(page,'method.html');checks+=1
                assert 'not an external preregistration' in page.locator('body').inner_text();checks+=1
                page.close()
            page=browser.new_page(java_script_enabled=False)
            assert navigate(page,'index.html')
            assert 'interactive controls need JavaScript' in page.locator('noscript').inner_text();checks+=1
            page.close();browser.close()
        assert not errors,errors
    finally:server.shutdown();server.server_close()
    return {'status':'PASS','checks':checks,'viewports':['1440x1050','390x844'],'page_errors':errors,'independent_review':False,'transport':'in-memory offline rendering' if offline else 'HTTP'}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--offline',action='store_true');args=parser.parse_args()
    summary=run(args.offline);(HERE/'browser-verification.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
