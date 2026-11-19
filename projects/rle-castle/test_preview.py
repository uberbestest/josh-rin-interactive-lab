"""Same-lab presentation checks, not a game-build or model-agent evaluation."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import http.server
import json
import shutil
import socketserver
import threading
from playwright.sync_api import sync_playwright

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=Path, help='Write screenshots and receipt outside the source tree.')
args = parser.parse_args()
OUT = args.output_dir.resolve() if args.output_dir else P / 'review'
OUT.mkdir(parents=True, exist_ok=True)
RECEIPT = OUT / 'BROWSER-RECEIPT.json' if args.output_dir else P / 'BROWSER-RECEIPT.json'
provenance = json.loads((P / 'provenance.json').read_text())
asset = provenance['public_asset']
assert hashlib.sha256((P / asset['path']).read_bytes()).hexdigest() == asset['sha256']
assert provenance['public_playable_build'] is False
assert provenance['build_verified_in_this_release'] is False

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def log_message(self, *args):
        pass

checks, errors, failed = [], [], []
with socketserver.TCPServer(('127.0.0.1', 0), Handler) as server:
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_address[1]}'
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True, executable_path=shutil.which('chromium'), args=['--no-sandbox'])
        for width in [320, 390, 768, 1440]:
            page = browser.new_page(viewport={'width': width, 'height': 1000}, reduced_motion='reduce')
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('response', lambda response: failed.append(
                {'url': response.url, 'status': response.status}) if response.status >= 400 else None)
            response = page.goto(base + '/projects/rle-castle/index.html', wait_until='networkidle')
            assert response.status == 200
            assert page.locator('h1').count() == 1
            assert page.locator('.capture img').evaluate(
                '(e) => e.complete && e.naturalWidth === 575 && e.naturalHeight === 200')
            assert page.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth') <= 1
            assert page.locator('a').filter(has_text='Play now').count() == 0
            duplicate_ids = page.evaluate('''() => {
                const ids = [...document.querySelectorAll('[id]')].map(e => e.id);
                return ids.filter((id, i) => ids.indexOf(id) !== i);
            }''')
            assert not duplicate_ids, duplicate_ids
            broken_anchors = page.evaluate('''() => [...document.querySelectorAll('a[href^="#"]')]
                .map(e => e.getAttribute('href').slice(1))
                .filter(id => !document.getElementById(id))''')
            assert not broken_anchors, broken_anchors
            page.locator('a[href="#preview-route"]').first.click()
            assert page.url.endswith('#preview-route')
            page.locator('summary').focus()
            page.keyboard.press('Enter')
            assert page.locator('details').evaluate('(e) => e.open')
            page.locator('summary').click()
            page.evaluate('window.scrollTo(0, 0)')
            page.screenshot(path=str(OUT / f'project-{width}.png'), full_page=True)
            checks.append({'viewport': width, 'status': 'PASS', 'image_loaded': True,
                           'horizontal_overflow': False, 'anchors_resolved': True,
                           'evidence_disclosure_keyboard': True})
            page.close()
        page = browser.new_page(java_script_enabled=False, viewport={'width': 390, 'height': 900})
        page.goto(base + '/projects/rle-castle/index.html', wait_until='networkidle')
        page.locator('summary').click()
        assert page.locator('details').evaluate('(e) => e.open')
        assert page.locator('img').evaluate('(e) => e.complete && e.naturalWidth > 0')
        assert page.locator('#research').inner_text()
        page.close()
        browser.close()
    server.shutdown()
assert not errors, errors
assert not failed, failed
receipt = {
    'status': 'PASS', 'timestamp_utc': datetime.now(timezone.utc).isoformat(),
    'presentation_version': '0.2.0',
    'scope': 'Same-lab Chromium checks of the project overview over localhost HTTP; no current game launch, API trial, homepage check or external research review',
    'image_sha256': asset['sha256'], 'checks': checks,
    'no_javascript_required': True, 'javascript_errors': errors, 'failed_http_responses': failed,
}
RECEIPT.write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
