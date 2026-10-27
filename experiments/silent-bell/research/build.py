"""Generate deterministic public records and a dependency-free HTML replay."""
from hashlib import sha256
from pathlib import Path
import argparse
import json

from experiment import ROOT, evaluate


def artifacts():
    results = evaluate()
    summary = {k: v for k, v in results.items() if k not in ("cases", "grid", "boundaries")}
    viewer = {k: v for k, v in results.items() if k != "grid"}
    embedded = json.dumps(viewer, sort_keys=True, separators=(",", ":")).replace("<", "\\u003c")
    template = (ROOT / "web/template.html").read_text(encoding="utf-8")
    if template.count("__RESULTS_JSON__") != 1:
        raise RuntimeError("Expected exactly one results slot")
    return {
        ROOT / "results/full-results.json": json.dumps(results, indent=2, sort_keys=True) + "\n",
        ROOT / "results/summary.json": json.dumps(summary, indent=2, sort_keys=True) + "\n",
        ROOT / "index.html": template.replace("__RESULTS_JSON__", embedded),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Verify without rewriting files")
    args = parser.parse_args()
    outputs = artifacts()
    for path, text in outputs.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                raise SystemExit(f"Mismatch: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    manifest = ROOT / "results/SHA256SUMS.txt"
    paths = sorted(p for p in ROOT.rglob("*") if p.is_file() and p != manifest and "__pycache__" not in p.parts and p.suffix != ".pyc")
    hashes = "".join(f"{sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}\n" for p in paths)
    if args.check:
        if manifest.read_text(encoding="utf-8") != hashes:
            raise SystemExit("Checksum manifest differs")
    else:
        manifest.write_text(hashes, encoding="utf-8")
    print(f"{'Verified' if args.check else 'Generated'} 3 artifacts and {len(paths)} file checksums.")


if __name__ == "__main__":
    main()
