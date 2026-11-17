#!/usr/bin/env python3
import argparse
import functools
import http.server
import json
import shutil
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
EXHIBIT = ROOT / 'experiments/check-use-gap'


def require(ok, message):
    if not ok: raise RuntimeError(message)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_): pass


def main(standalone=False):
    checks = []
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    out = EXHIBIT / 'checks'; out.mkdir(exist_ok=True)
    errors = []
    try:
        with sync_playwright() as p:
            executable = shutil.which('chromium')
            options = {'headless': True}
            if executable: options['executable_path'] = executable
            browser = p.chromium.launch(**options)
            page = browser.new_page(viewport={'width':1440,'height':1000}, color_scheme='dark')
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(base + '/experiments/check-use-gap/index.html')
            page.wait_for_function("document.querySelector('#solver-status').textContent.startsWith('PASS')")
            text = page.locator('#comparison').inner_text()
            require(all(s in text for s in ('3 / 10','9 / 10','10 / 10')), 'default exact comparison')
            checks.append('default_frontier_matches_frozen_table')
            page.locator('#show-all').click()
            require('No completion' in page.locator('#outcome').inner_text(), 'snapshot all-granted history should stop')
            checks.append('all_granted_actual_world_not_leaked_into_policy')
            page.locator('[data-mode=atomic]').click();page.locator('#show-all').click()
            require('Authorized completion after 1 tick' in page.locator('#outcome').inner_text(), 'atomic initial grant')
            page.locator('details.operator summary').click();page.locator('#schedule').select_option('10001')
            page.locator('[data-mode=compare]').click();page.locator('#show-all').click()
            require('No completion' in page.locator('#outcome').inner_text(), 'compare final grant')
            page.locator('[data-mode=atomic]').click();page.locator('#show-all').click()
            require('Authorized completion after 4 ticks' in page.locator('#outcome').inner_text(), 'atomic final grant')
            checks.append('late_restored_grant_distinguishes_interface_contracts')
            page.locator('#reveal').check();require(page.locator('.truth').count()>0, 'evaluator truth toggle')
            page.locator('#reveal').uncheck();require(page.locator('.truth').count()==0, 'evaluator truth hidden')
            checks.append('evaluator_only_trace_toggle')
            page.locator('#horizon').select_option('8');page.locator('#switches').select_option('8');page.locator('#main-cost').select_option('4')
            require(page.locator('#comparison').inner_text().count('256 / 256')==3, 'long-budget completions')
            require('2.13' in page.locator('#comparison').inner_text(), 'display rounding')
            checks.append('controls_recompute_long_budget_cost_frontier')
            page.locator('#horizon').select_option('1');page.locator('#switches').select_option('0');page.locator('#initial').select_option('0');page.locator('#main-cost').select_option('8')
            require(page.locator('#feasible').inner_text()=='0', 'impossible cell')
            require('NaN' not in page.locator('#comparison').inner_text(), 'zero-feasible rendering')
            checks.append('zero_feasible_histories_not_misreported_as_failures')
            page.locator('#horizon').select_option('4');page.locator('#switches').select_option('2');page.locator('#main-cost').select_option('6');page.locator('#initial').select_option('1');page.locator('[data-mode=snapshot]').click()
            page.locator('details.operator summary').click()
            page.evaluate("document.documentElement.dataset.theme='dark'")
            page.screenshot(path=str(out/'desktop-dark.png'),full_page=True)
            page.locator('#theme').click();require(page.evaluate('document.documentElement.dataset.theme')=='light','theme toggle')
            page.screenshot(path=str(out/'desktop-light.png'),full_page=True)
            checks.append('reading_theme_toggle')
            for width,height in ((390,844),(832,384)):
                page.set_viewport_size({'width':width,'height':height})
                require(page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'overflow at {width}')
                page.screenshot(path=str(out/f'viewport-{width}.png'),full_page=True)
            checks.append('mobile_and_landscape_no_document_overflow')
            for path in ('method.html','protocol.json','results/frontier.csv','results/minimal_witness.json','results/mutation_summary.json'):
                response=page.request.get(base+'/experiments/check-use-gap/'+path)
                require(response.status==200, 'missing public resource '+path)
            page.goto(base+'/experiments/check-use-gap/method.html')
            require(page.locator('h1').count()==1,'methods readable')
            page.set_viewport_size({'width':390,'height':844})
            require(page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'methods mobile overflow')
            checks.append('methods_and_data_routes')
            if not standalone:
                page.goto(base+'/index.html')
                require(page.locator('#check-use-gap a.open').count()==1,'homepage card')
                page.locator('#check-use-gap a.open').click()
                page.wait_for_function("document.querySelector('#solver-status').textContent.startsWith('PASS')")
                checks.append('real_gallery_navigation')
            require(not errors,'browser errors: '+repr(errors))
            checks.append('no_uncaught_browser_errors')
            browser.close()
    finally:
        server.shutdown();server.server_close()
    result={'status':'PASS','scope':'standalone exhibit' if standalone else 'exhibit and integrated repository gallery',
            'checks':checks,'count':len(checks),'uncaught_errors':errors}
    (out/'browser.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    return result


if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('--standalone',action='store_true');main(cli.parse_args().standalone)
