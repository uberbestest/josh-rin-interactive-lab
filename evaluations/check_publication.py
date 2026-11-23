#!/usr/bin/env python3
"""Check evaluation claims, links and rendered publication; never runs model trials."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from functools import partial
import hashlib
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time
import zipfile
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SECTION = ROOT / "evaluations"
PAGES = ["index.html", "evaluations/index.html", "projects/rle-castle/index.html",
         "evaluations/reproduction-pilot/index.html", "evaluations/live-api/index.html", "evaluations/live-api/warning-002.html"]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        for key in ("href", "src"):
            if key in attrs:
                self.links.append(attrs[key])


def static_checks():
    record = json.loads((SECTION / "evidence-index.json").read_text())
    source_file = (SECTION / record["source_presentation_record"]).resolve()
    assert hashlib.sha256(source_file.read_bytes()).hexdigest() == record["source_presentation_record_sha256"]
    original = json.loads(source_file.read_text())["studies"]
    assert len(record["studies"]) == len(original) == 9
    for study, retained in zip(record["studies"], original):
        assert study["round"] == retained["round"]
        assert study["title"] == retained["title"]
        assert study["tldr"] == retained["tldr"], study["round"]
        assert study["provider_api_run"] is False
        assert study["provider_token_usage"] is None
        assert study["provider_api_cost"] is None
        if study["round"] >= 8:
            assert study["fresh_model_participants"] == 0
        for link in [study["study_page"], study["study_markdown"], *study["files"].values()]:
            assert (SECTION / link).is_file(), link
    assert sum(s["fresh_model_participants"] for s in record["studies"]) == 232
    assert record["inventory"]["native_contexts_rounds_01_to_07"] == 232
    assert record["inventory"]["pooled_accuracy"] is None
    assert record["direct_provider_api"]["published_results"] == 3
    assert record["direct_provider_api"]["cost"]["behavioral_estimated_usd"] == "0.246104"
    assert record["direct_provider_api"]["cost"]["warning_ablation_estimated_usd"] == "0.481632"
    assert record["inventory"]["direct_provider_api_behavioral_contexts"] == 24
    public = json.loads((SECTION / "live-api/summary.json").read_text())
    assert len(public["studies"]) == 3
    compatibility, behavioral, warning = public["studies"]
    assert compatibility["provider_requests"] == 2 and compatibility["verdict"] == "PASS"
    assert behavioral["assigned_contexts"] == 8 and behavioral["provider_requests"] == 48
    assert len(behavioral["cases"]) == 8 and all(case["safe_joint_completion"] for case in behavioral["cases"])
    assert sum(case["model_requests"] for case in behavioral["cases"]) == 48
    assert behavioral["unsafe_attempts"] == behavioral["actual_duplicate_effects"] == 0
    assert all(arm["assigned"] == arm["safe_joint_completions"] == 4 for arm in behavioral["arms"])
    assert behavioral["primary_contrast_target_minus_combined_percentage_points"] == 0
    assert warning["assigned_contexts"] == 16 and warning["provider_requests"] == 96
    assert warning["safe_joint_completions"] == 16 and warning["verified_service_actions"] == 80
    assert len(warning["cases"]) == 16 and all(c["safe_joint_completion"] for c in warning["cases"])
    assert sum(c["model_requests"] for c in warning["cases"]) == 96
    assert warning["unsafe_attempts"] == warning["actual_duplicate_effects"] == 0
    assert len(warning["arms"]) == 4 and all(a["assigned"] == a["safe_joint_completions"] == 4 for a in warning["arms"])
    assert warning["primary_warning_by_receipt_interaction_percentage_points"] == 0
    assert warning["estimated_provider_cost_usd"] == "0.481632"
    assert public["privacy"]["raw_model_requests_public"] is False
    html = (SECTION / "index.html").read_text()
    assert "Direct provider API results: now reported" in html
    assert "No direct-provider API run is reported on this page yet" not in html
    checked = 0
    for name in PAGES:
        path = ROOT / name
        parser = Links()
        parser.feed(path.read_text())
        assert len(parser.ids) == len(set(parser.ids)), (name, "duplicate IDs")
        for link in parser.links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc or link.startswith("data:"):
                continue
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            if target.is_dir():
                target = target / "index.html"
            assert target.is_file(), (name, link)
            if parts.fragment and target.suffix == ".html":
                fragment_parser = Links()
                fragment_parser.feed(target.read_text())
                assert unquote(parts.fragment) in fragment_parser.ids, (name, link)
            checked += 1
    manifest = SECTION / "reproduction-pilot" / "SHA256SUMS.txt"
    if manifest.exists():
        for line in manifest.read_text().splitlines():
            digest, name = line.split("  ", 1)
            assert hashlib.sha256((manifest.parent / name).read_bytes()).hexdigest() == digest, name
        pilot = json.loads((manifest.parent / "summary.json").read_text())
        assert pilot["fresh_native_contexts"] == pilot["completed_contexts"] == 2
        assert pilot["failed_or_excluded_contexts"] == 0
        assert pilot["provider_token_usage"] is None and pilot["provider_api_cost"] is None
        with zipfile.ZipFile(manifest.parent / "evidence.zip") as archive:
            members = json.loads(archive.read("FILE-MANIFEST.json"))
            for name, digest in members.items():
                assert hashlib.sha256(archive.read(name)).hexdigest() == digest, name
            for arm in pilot["arms"]:
                paths = arm["receipt_paths_in_evidence_zip"]
                main = json.loads(archive.read(paths["main"]))
                extra = json.loads(archive.read(paths["exploratory"]))
                assert main["fresh_scripted_executions"] == 237
                assert main["events_replayed"] == 2308
                assert main["normalized_reproduction_exact"] is True
                assert main["reproduction_requested"] is True
                assert extra["runs_reproduced"] == 6 and extra["status"] == "PASS"
                for line in archive.read(paths["commands"]).decode().splitlines():
                    command = json.loads(line)
                    assert command["exit_code"] == 0
                    for stream in ["stdout", "stderr"]:
                        assert hashlib.sha256(command[stream].encode()).hexdigest() == command[stream + "_sha256"]
    return {"status": "PASS", "local_links_and_fragments": checked,
            "studies_matched_to_original": 9, "historic_native_contexts": 232,
            "direct_provider_api_results": 3,
            "scope": "Publication integrity and evidence labels; no new scientific execution."}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@contextmanager
def local_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT)))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


def live_bytes(base, revision, wait_seconds):
    paths = {"index.html"}
    for folder in [SECTION, ROOT / "projects/rle-castle"]:
        paths.update(p.relative_to(ROOT).as_posix() for p in folder.rglob("*")
                     if p.is_file() and "review" not in p.parts and "__pycache__" not in p.parts
                     and p.suffix in {".html", ".css", ".json", ".jsonl", ".md", ".txt", ".webp", ".py", ".zip"})
    expected = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(paths)}
    pending = dict(expected)
    deadline = time.monotonic() + wait_seconds
    while pending:
        failures = {}
        for name, digest in pending.items():
            request = Request(urljoin(base, name) + "?evaluation-release=" + revision,
                              headers={"Cache-Control": "no-cache", "User-Agent": "Lab-Evaluation-Publication-Check"})
            try:
                with urlopen(request, timeout=15) as response:
                    assert response.status == 200
                    assert hashlib.sha256(response.read()).hexdigest() == digest
            except Exception as error:
                failures[name] = str(error)
        if not failures:
            return expected
        assert time.monotonic() < deadline, failures
        print("Waiting for deployed files:", json.dumps(failures), flush=True)
        pending = {name: expected[name] for name in failures}
        time.sleep(5)
    return expected


def browser_checks(base, output):
    from playwright.sync_api import sync_playwright
    observations = []
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for width in [320, 390, 1440]:
            context = browser.new_context(viewport={"width": width, "height": 950}, reduced_motion="reduce")
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("response", lambda response: errors.append(f"HTTP {response.status}: {response.url}")
                    if response.status >= 400 and urlsplit(response.url).netloc == urlsplit(base).netloc else None)
            for name in PAGES:
                response = page.goto(urljoin(base, name), wait_until="networkidle")
                assert response and response.status == 200, name
                assert page.locator("h1").count() == 1
                assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"), (name, width)
                if name == "evaluations/index.html":
                    assert page.get_by_text("Direct provider API results: now reported", exact=False).is_visible()
                    assert page.locator('a[href="live-api/index.html"]').count() >= 1
                    assert page.locator('[id^="round-"]').count() == 9
                    page.locator('a[href="../rin-self-evaluation/round-07.html"]').first.click()
                    assert page.locator("h1").inner_text() == json.loads((SECTION / "evidence-index.json").read_text())["studies"][6]["title"]
                    page.go_back(wait_until="networkidle")
                elif name == "evaluations/live-api/index.html":
                    assert page.locator("#results .live-table tbody tr").count() >= 3
                    assert "4/4" in page.locator("#results").inner_text()
                    assert page.locator('a[href="warning-002.html"]').count() >= 1
                    assert page.locator('a[href="summary.json"]').count() >= 1
                elif name == "evaluations/live-api/warning-002.html":
                    assert page.locator("#warning-results .live-table tbody tr").count() >= 5
                    assert "16/16" in page.locator("#warning-results").inner_text()
                    assert page.locator('a[href="summary.json"]').count() >= 1
                elif name == "projects/rle-castle/index.html":
                    assert page.locator('img[src="assets/faire-doorway.webp"]').evaluate("el => el.complete && el.naturalWidth === 575")
                    assert page.locator('a[href="../../evaluations/index.html"], a[href="../../evaluations/"]').count() >= 1
                elif name == "evaluations/reproduction-pilot/index.html":
                    assert page.locator(".tldr dt").all_text_contents() == ["What we tested", "What happened", "Outliers"]
                    assert page.locator('a[href="evidence.zip"]').count() >= 1
                else:
                    assert page.locator('a[href="evaluations/index.html"]').count() >= 2
                    assert page.locator('#experiments .card').count() == 14
                    page.locator('[data-filter="attention"]').click()
                    assert page.locator('#experiments .card:visible').count() == 1
                    page.locator('[data-filter="all"]').click()
                    assert page.locator('#experiments .card:visible').count() == 14
                page.screenshot(path=str(output / f"{width}-{name.replace('/', '-')}.png"), full_page=True)
                observations.append({"page": name, "width": width, "status": "PASS"})
            context.close()
        context = browser.new_context(java_script_enabled=False, viewport={"width": 390, "height": 900})
        page = context.new_page()
        for name in PAGES[1:]:
            response = page.goto(urljoin(base, name), wait_until="networkidle")
            assert response and response.status == 200
            assert page.locator("h1").is_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1")
            observations.append({"page": name, "width": 390, "javascript": False, "status": "PASS"})
        browser.close()
    assert not errors, errors
    return observations


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--base-url")
    p.add_argument("--revision", default="local")
    p.add_argument("--wait-seconds", type=int, default=0)
    p.add_argument("--static-only", action="store_true")
    args = p.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = {"static": static_checks(), "revision": args.revision}
    if not args.static_only:
        if args.base_url:
            base = args.base_url.rstrip("/") + "/"
            result["resources_sha256"] = live_bytes(base, args.revision, args.wait_seconds)
            result["browser"] = browser_checks(base, args.output_dir)
        else:
            with local_server() as base:
                result["browser"] = browser_checks(base, args.output_dir)
    result["status"] = "PASS"
    result["scope"] = "Same-lab presentation checks; scientific evidence is identified separately."
    (args.output_dir / "publication-check.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "static": result["static"], "page_viewports": len(result.get("browser", [])), "live_files": len(result.get("resources_sha256", {}))}, indent=2))


if __name__ == "__main__":
    main()
