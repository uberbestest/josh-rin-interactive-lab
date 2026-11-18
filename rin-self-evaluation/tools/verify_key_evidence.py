#!/usr/bin/env python3
"""Verify the trusted, byte-identical consumable-key study archive.

This publication wrapper checks the complete inventory and the externally
declared pre-run freeze, then invokes the archived replay entrypoint. It never
starts participant models. Only use it with this lab's trusted evidence ZIPs:
reproduction necessarily executes the scientific Python code in the archive.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
import zipfile

INVENTORY = "INVENTORY.json"
FREEZE = "protocol/frozen.json"
RAW_RECORD = re.compile(r"runs/([^/]+)/(initial_state\.json|state\.json|events\.jsonl)$")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
MAX_UNCOMPRESSED_BYTES = 128 * 1024 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative_path(name: str) -> PurePosixPath:
    if not isinstance(name, str) or not name or "\\" in name or ":" in name or "\x00" in name:
        raise ValueError("Invalid evidence path")
    if any(part in ("", ".", "..") for part in name.split("/")):
        raise ValueError("Noncanonical evidence path")
    path = PurePosixPath(name)
    if path.is_absolute():
        raise ValueError("Absolute evidence path")
    return path


def extract(archive: Path, destination: Path) -> Path:
    with zipfile.ZipFile(archive) as bundle:
        members = []
        names = set()
        roots = set()
        total = 0
        for info in bundle.infolist():
            name = info.filename.rstrip("/") if info.is_dir() else info.filename
            path = relative_path(name)
            if name in names:
                raise ValueError("Duplicate archive member")
            names.add(name)
            roots.add(path.parts[0])
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode) or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError("Nonregular archive member")
            if info.flag_bits & 1:
                raise ValueError("Encrypted archive member")
            total += info.file_size
            if total > MAX_UNCOMPRESSED_BYTES:
                raise ValueError("Evidence archive exceeds the declared extraction bound")
            members.append((info, destination.joinpath(*path.parts)))
        if len(roots) != 1:
            raise ValueError("Evidence archive must contain one root directory")
        for info, target in members:
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as stream:
                    stream.write(bundle.read(info))
    return destination / next(iter(roots))


def file_map(root: Path) -> dict[str, Path]:
    result = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("Symlink in evidence archive")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = path
        elif not path.is_dir():
            raise ValueError("Nonregular evidence file")
    return result


def check_inventory(root: Path) -> tuple[dict, dict[str, Path]]:
    inventory = json.loads((root / INVENTORY).read_text(encoding="utf-8"))
    rows = inventory.get("files")
    if not isinstance(rows, dict) or not rows:
        raise ValueError("Expected a complete inventory mapping")
    actual = file_map(root)
    if set(actual) != set(rows) | {INVENTORY} or INVENTORY in rows:
        raise ValueError("Inventory membership differs from archive files")
    for name, row in rows.items():
        relative_path(name)
        if not isinstance(row, dict) or not DIGEST.fullmatch(str(row.get("sha256", ""))):
            raise ValueError("Invalid inventory digest")
        raw = actual[name].read_bytes()
        if type(row.get("bytes")) is not int or row["bytes"] != len(raw) or row["sha256"] != sha(raw):
            raise ValueError("Inventory digest or length mismatch: " + name)
    return inventory, actual


def verify(root: Path, frozen_sha256: str, output: Path) -> dict:
    if not DIGEST.fullmatch(frozen_sha256):
        raise ValueError("A valid external pre-run freeze digest is required")
    inventory_before = (root / INVENTORY).read_bytes()
    _, actual = check_inventory(root)
    frozen_bytes = actual[FREEZE].read_bytes()
    if sha(frozen_bytes) != frozen_sha256:
        raise ValueError("Archived freeze does not match the published study identity")
    frozen = json.loads(frozen_bytes)
    sources = frozen.get("source_hashes")
    if not isinstance(sources, dict) or not {"engine.py", "client.py", "reproduce.py"} <= set(sources):
        raise ValueError("Freeze must identify the instrument, client, and reproduction source")
    for name, digest in sources.items():
        relative_path(name)
        if name not in actual or not DIGEST.fullmatch(str(digest)) or sha(actual[name].read_bytes()) != digest:
            raise ValueError("Frozen source changed: " + name)

    command = [sys.executable, "-B", "reproduce.py", "--output", str(output)]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    completed = subprocess.run(command, cwd=root, env=environment, text=True, encoding="utf-8",
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300, check=False)
    if completed.returncode != 0 or not output.is_file():
        raise ValueError("Archived scientific reproduction failed:\n" + (completed.stdout + completed.stderr)[-6000:])
    result = json.loads(output.read_text(encoding="utf-8"))
    if result.get("status") != "PASS":
        raise ValueError("Archived scientific reproduction did not pass")
    for field in ("runs_replayed", "events_replayed", "mechanical_results_exact",
                  "final_reports_exact", "preserved_scientific_record_files"):
        if type(result.get(field)) is not int or result[field] < 0:
            raise ValueError("Missing or invalid reproduction count: " + field)
    count = result["runs_replayed"]
    if count < 1 or result["mechanical_results_exact"] != count or result["final_reports_exact"] != count:
        raise ValueError("Not every archived run or sealed report reproduced exactly")
    raw_records = {name for name in actual if RAW_RECORD.fullmatch(name)}
    run_ids = {RAW_RECORD.fullmatch(name).group(1) for name in raw_records}
    if len(run_ids) != count or len(raw_records) != 3 * count:
        raise ValueError("Initial state, final state, and event logs are incomplete")
    if result["preserved_scientific_record_files"] != len(raw_records):
        raise ValueError("Preserved scientific-record count differs")
    tests = result.get("semantic_tests", {})
    if tests.get("status") != "PASS" or type(tests.get("tests")) is not int or tests["tests"] < 1:
        raise ValueError("Instrument semantic tests did not pass")
    check_inventory(root)
    if (root / INVENTORY).read_bytes() != inventory_before:
        raise ValueError("The evidence inventory changed during reproduction")
    result.update({
        "round": "round-04", "verification_kind": "consumable-key-v1",
        "canonical_frozen_sha256": frozen_sha256,
        "inventory_sha256": sha(inventory_before), "public_inventory_files": len(actual),
        "unchanged_frozen_sources_verified": len(sources),
        "all_public_files_unchanged_during_verification": True,
        "scope": "Same-lab replay and integrity checks of the frozen instrument and recorded native runs. No new participant trials, backend attestation, or external replication.",
    })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--frozen-sha256", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    archive = args.archive.resolve()
    if args.output is not None and args.output.resolve() == archive:
        raise ValueError("A reproduction receipt cannot overwrite the archive")
    with tempfile.TemporaryDirectory(prefix="rin-key-evidence-") as folder:
        temporary = Path(folder)
        root = extract(archive, temporary / "extracted")
        result = verify(root, args.frozen_sha256, temporary / "reproduction.json")
    result.update({
        "public_archive": archive.name, "public_archive_sha256": sha(archive.read_bytes()),
        "public_archive_identical_to_canonical": True,
        "fresh_extraction": True, "temporary_extraction_removed": True,
        "verified_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    fields = ("status", "round", "runs_replayed", "events_replayed", "mechanical_results_exact", "final_reports_exact")
    print(json.dumps({field: result[field] for field in fields}, indent=2))


if __name__ == "__main__":
    main()
