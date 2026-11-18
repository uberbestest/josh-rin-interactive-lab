#!/usr/bin/env python3
"""Render and operate the published section locally or at its public Pages URL."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]
SECTION = REPO / "rin-self-evaluation"
LABELS = ["What we tested", "What happened", "Outliers"]
VIEWPORTS = {"desktop": {"width": 1440, "height": 1000}, "phone": {"width": 390, "height": 844}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@contextmanager
def local_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(REPO)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def verify_bytes(base, revision, wait_seconds):
    paths = [Path("index.html")]
    paths.extend(p.relative_to(REPO) for p in SECTION.rglob("*")
                 if p.is_file() and p.suffix in {".html", ".css", ".json", ".pdf", ".zip", ".sha256", ".md"})
    expected = {p.as_posix(): hashlib.sha256((REPO / p).read_bytes()).hexdigest() for p in paths}
    deadline = time.monotonic() + wait_seconds
    pending = dict(expected)
    while pending:
        failures = {}
        for path, digest in pending.items():
            url = urljoin(base, path) + "?rin-publication=" + revision
            request = Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "Rin-Publication-Check"})
            try:
                with urlopen(request, timeout=20) as response:
                    actual = response.read()
                    assert response.status == 200
                assert hashlib.sha256(actual).hexdigest() == digest, "bytes do not match this commit"
            except Exception as error:
                failures[path] = str(error)
        if not failures:
            return expected
        if time.monotonic() >= deadline:
            raise AssertionError("Public resources did not match: " + json.dumps(failures))
        print("Waiting for deployment:", json.dumps(failures), flush=True)
        pending = {path: expected[path] for path in failures}
        time.sleep(10)
    return expected


def no_overflow(page):
    sizes = page.evaluate("""() => ({
      viewport: document.documentElement.clientWidth,
      document: document.documentElement.scrollWidth,
      body: document.body.scrollWidth
    })""")
    assert max(sizes["document"], sizes["body"]) <= sizes["viewport"] + 1, sizes
    return sizes


def inspect(base, output, revision, wait_seconds):
    output.mkdir(parents=True, exist_ok=True)
    hashes = verify_bytes(base, revision, wait_seconds)
    studies = json.loads((SECTION / "studies.json").read_text())["studies"]
    pages = ["index.html", "rin-self-evaluation/index.html"]
    pages += [f"rin-self-evaluation/round-{s['round']:02d}.html" for s in studies]
    observations = []
    failures = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for viewport_name, viewport in VIEWPORTS.items():
            context = browser.new_context(viewport=viewport, color_scheme="dark", reduced_motion="reduce")
            page = context.new_page()
            page.on("pageerror", lambda error: failures.append(str(error)))
            page.on("response", lambda response: failures.append(f"HTTP {response.status}: {response.url}")
                    if response.status >= 400 and urlsplit(response.url).netloc == urlsplit(base).netloc else None)
            for path in pages:
                response = page.goto(urljoin(base, path), wait_until="networkidle")
                assert response and response.status == 200, path
                assert page.locator("h1").count() == 1
                assert page.title()
                sizes = no_overflow(page)
                name = path.replace("/", "-").removesuffix(".html")
                if path == "index.html":
                    page.locator('a[href="#self-evaluation"]').click()
                    page.locator("#self-evaluation").screenshot(path=str(output / f"{viewport_name}-homepage-entry.png"))
                    page.locator('#self-evaluation a[href="rin-self-evaluation/index.html"]').click()
                    assert page.locator(".study-card").count() == len(studies)
                else:
                    page.keyboard.press("Tab")
                    assert page.locator(".skip-link").evaluate("el => el === document.activeElement")
                    page.keyboard.press("Enter")
                    assert urlsplit(page.url).fragment == "main"
                    if "round-" in path:
                        assert page.locator(".tldr dt").all_text_contents() == LABELS
                        assert page.locator(".tldr").evaluate("el => !!(el.compareDocumentPosition(document.querySelector('.content-section')) & Node.DOCUMENT_POSITION_FOLLOWING)")
                        page.get_by_text("Original artifact identities", exact=True).click()
                        assert page.locator(".hashes").is_visible()
                        no_overflow(page)
                        page.screenshot(path=str(output / f"{viewport_name}-{name}-full.png"), full_page=True)
                        page.evaluate("window.scrollTo(0, 0)")
                        page.screenshot(path=str(output / f"{viewport_name}-{name}-top.png"))
                        page.get_by_role("link", name="All evaluations", exact=True).click()
                        assert page.locator(".study-card").count() == len(studies)
                    else:
                        page.screenshot(path=str(output / f"{viewport_name}-{name}-full.png"), full_page=True)
                        for study in studies:
                            target = f"round-{study['round']:02d}.html"
                            page.locator(f'.study-card a[href="{target}"]').first.click()
                            assert page.locator("h1").inner_text() == study["title"]
                            page.get_by_role("link", name="All evaluations", exact=True).click()
                observations.append({"viewport": viewport_name, "page": path, "status": "PASS", "widths": sizes})
            context.close()
        browser.close()
    assert not failures, failures
    receipt = {
        "status": "PASS", "kind": "publication browser and byte verification", "base_url": base,
        "revision": revision, "viewports": VIEWPORTS, "pages": observations,
        "resources_sha256": hashes,
        "checks": ["commit bytes for pages and every published download", "homepage entry and navigation",
                   "opening TLDR fields", "keyboard skip link", "expanded digest disclosure", "no body overflow",
                   "no page exceptions or failed same-origin responses"],
        "scope": "Web presentation and deployment only; this is not a new scientific trial or external peer review.",
    }
    (output / "browser-check.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "pages_and_viewports": len(observations),
                      "resources_matching_commit": len(hashes), "base_url": base}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--revision", default="local")
    parser.add_argument("--wait-seconds", type=int, default=0)
    args = parser.parse_args()
    if args.base_url:
        inspect(args.base_url.rstrip("/") + "/", args.output_dir, args.revision, args.wait_seconds)
    else:
        with local_server() as base:
            inspect(base, args.output_dir, args.revision, 0)


if __name__ == "__main__":
    main()
