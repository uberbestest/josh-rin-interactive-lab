#!/usr/bin/env python3
"""Freeze authored inputs before the assigned deterministic helper executions."""
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT/'protocol/frozen.json'


def main():
    if TARGET.exists():
        raise SystemExit('Freeze already exists; do not rewrite a frozen instrument')
    if list(ROOT.glob('results/runs/*/events.jsonl')):
        raise SystemExit('Cannot describe a post-execution freeze as prospective')
    files = {}
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or p.is_symlink() or '__pycache__' in p.parts or p.suffix == '.pyc':
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel == 'README.md' or rel.startswith(('report/','provenance/','results/')):
            continue
        raw = p.read_bytes()
        private_prefix = ('/' + 'workspace' + '/' + 'scratch' + '/').encode()
        if private_prefix in raw:
            raise SystemExit('Private workspace prefix in freeze candidate: '+rel)
        files[rel] = hashlib.sha256(raw).hexdigest()
    data = {'record':'JRR-RECEIPT-GUARDS-2026-11-18-008',
            'kind':'prospective source freeze for deterministic authored helper matrix',
            'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'assigned_scripted_executions':64,'native_participants':0,
            'prior_known_evidence':'Historical Round 07 mocked routing fixtures motivated this design.',
            'preflight':'Transport-only tests and 28 authored witness-world executions precede this freeze; they are not assigned helper runs.',
            'source_hashes':files}
    TARGET.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'frozen_file_count':len(files),'freeze_sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
