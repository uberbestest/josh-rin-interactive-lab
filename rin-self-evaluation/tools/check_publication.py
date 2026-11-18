#!/usr/bin/env python3
"""Check this publication and replay retained evidence; never launch participants."""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit

SECTION = Path(__file__).resolve().parents[1]
REPO = SECTION.parent
LABELS = ["What we tested", "What happened", "Outliers"]


class Document(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.ids = set()
        self.links = []
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if "id" in attrs:
            assert attrs["id"] not in self.ids, "Duplicate HTML id: " + attrs["id"]
            self.ids.add(attrs["id"])
        for attr in ("href", "src"):
            if attrs.get(attr):
                self.links.append(attrs[attr])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_link(source, link):
    parsed = urlsplit(link)
    if parsed.scheme or parsed.netloc:
        assert parsed.scheme in ("https", "http", "mailto"), "Unexpected link scheme"
        return 0
    target = (source.parent / unquote(parsed.path)).resolve() if parsed.path else source
    assert target.is_relative_to(REPO), "Link escapes the repository"
    if target.is_dir():
        target /= "index.html"
    assert target.is_file(), f"Missing local link from {source.name}: {link}"
    if parsed.fragment and target.suffix == ".html":
        assert unquote(parsed.fragment) in Document(target).ids, f"Missing fragment: {link}"
    return 1


def check(output_dir):
    subprocess.run([sys.executable, str(SECTION / "build.py"), "--check"], check=True)
    data = json.loads((SECTION / "studies.json").read_text())
    studies = data["studies"]
    assert len({s["round"] for s in studies}) == len(studies), "Repeated round number"
    html_pages = list(SECTION.glob("*.html"))
    links_checked = 0
    for path in html_pages:
        doc = Document(path)
        assert sum(tag == "h1" for tag, _ in doc.elements) == 1, path.name
        assert not any(tag == "script" for tag, _ in doc.elements), "Section requires no scripts"
        for tag, attrs in doc.elements:
            if tag == "link" and attrs.get("rel") == "stylesheet":
                assert not urlsplit(attrs["href"]).scheme, "Unexpected remote stylesheet"
        for link in doc.links:
            links_checked += check_link(path, link)
    for path in SECTION.glob("*.md"):
        for link in re.findall(r"(?<!!)\[[^\]]+\]\(([^\s)]+)\)", path.read_text()):
            links_checked += check_link(path, link)

    home = (REPO / "index.html").read_text()
    assert home.count('id="self-evaluation"') == 1
    assert 'href="#self-evaluation"' in home
    assert 'href="rin-self-evaluation/index.html"' in home
    assert "rin-self-evaluation/README.md" in (REPO / "README.md").read_text()

    results = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for study in studies:
        number = f"round-{study['round']:02d}"
        assert study["status"] == "executed", "Unrun entries need an explicit planned-page format"
        assert set(study["tldr"]) == {"tested", "happened", "outliers"}
        assert all(study["tldr"].values())
        page = SECTION / (number + ".html")
        html = page.read_text()
        doc = Document(page)
        tldr_pos = next(i for i, (_, a) in enumerate(doc.elements) if "tldr" in a.get("class", "").split())
        detail_pos = next(i for i, (_, a) in enumerate(doc.elements) if "content-section" in a.get("class", "").split())
        assert tldr_pos < detail_pos, "TLDR must precede detailed methods"
        for label in LABELS:
            assert f"<dt>{label}</dt>" in html
            assert f"**{label}:**" in (SECTION / (number + ".md")).read_text()
        if study["round"] == 1:
            assert study["kind"] == "baseline" and study["selectors"] == []
        elif study["kind"] == "matched":
            assert study["selectors"] == ["gpt-6-astra", "gpt-6.2-astra"]

        files = {key: SECTION / value for key, value in study["files"].items()}
        assert sha(files["report"]) == study["original_digests"]["report_sha256"]
        archive_sha = sha(files["evidence"])
        checksum_parts = files["checksum"].read_text().strip().split()
        assert checksum_parts == [archive_sha, files["evidence"].name]
        receipt = json.loads(files["publication"].read_text())
        assert receipt["status"] == "PASS"
        assert receipt["public_archive_sha256"] == archive_sha
        assert receipt["report_sha256"] == sha(files["report"])
        assert receipt["canonical_archive"]["sha256"] == study["original_digests"]["archive_sha256"]
        assert receipt["canonical_frozen_sha256"] == study["original_digests"]["protocol_sha256"]
        assert receipt["scientific_records_byte_identical_to_canonical_at_export"] is True
        check_path = output_dir / (number + "-replay.json")
        verification_kind = study.get("verification_kind", "public-disclosure-v1")
        if verification_kind == "public-disclosure-v1":
            command = [sys.executable, str(SECTION / "tools" / "verify_public_evidence.py"),
                       str(files["evidence"]), "--output", str(check_path)]
        elif verification_kind == "consumable-key-v1":
            assert study.get("public_archive_identical_to_canonical") is True
            assert archive_sha == study["original_digests"]["archive_sha256"]
            command = [sys.executable, str(SECTION / "tools" / "verify_key_evidence.py"),
                       str(files["evidence"]), "--frozen-sha256", study["original_digests"]["protocol_sha256"],
                       "--output", str(check_path)]
        else:
            raise ValueError("Unsupported publication verification kind: " + str(verification_kind))
        subprocess.run(command, check=True)
        replay = json.loads(check_path.read_text())
        for field in ("runs_replayed", "events_replayed", "mechanical_results_exact", "final_reports_exact",
                      "preserved_scientific_record_files"):
            assert replay[field] == receipt["verification"][field], f"Receipt disagrees on {field}"
        results.append({
            "round": study["round"], "public_archive_sha256": archive_sha,
            "report_sha256": sha(files["report"]),
            "runs_replayed": replay["runs_replayed"], "events_replayed": replay["events_replayed"],
            "semantic_tests_passed": replay["semantic_tests"]["tests"],
            "scientific_files_preserved": replay["preserved_scientific_record_files"],
        })

    private_path = re.compile(rb"/workspace/scratch/[a-f0-9]{12}(?:/|\b)")
    text_paths = [p for p in SECTION.rglob("*") if p.suffix in {".html", ".md", ".json", ".py", ".css"}]
    text_paths.extend((REPO / ".publishing" / "rin-self-evaluation").glob("*"))
    for path in text_paths:
        if path.is_file():
            assert not private_path.search(path.read_bytes()), "Private session path in " + path.name
    result = {
        "status": "PASS", "kind": "post-run publication and retained-evidence check",
        "html_pages_checked": len(html_pages), "local_links_checked": links_checked,
        "studies": results,
        "scope": "Presentation, downloads and retained event replay. No new participants or external scientific review.",
    }
    (output_dir / "publication-check.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.output_dir:
        assert not args.output_dir.resolve().is_relative_to(SECTION), "Keep check receipts outside the published section"
        check(args.output_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="rin-publication-check-") as folder:
            check(Path(folder))


if __name__ == "__main__":
    main()
