#!/usr/bin/env python3
"""Create the prospective source manifest before assigned controller executions."""
from __future__ import annotations
import datetime
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'protocol/frozen.json'

if OUT.exists():
    raise SystemExit('Existing freeze retained; a revision needs a separate manifest/version.')
files={}
for path in sorted(ROOT.rglob('*')):
    relative=path.relative_to(ROOT)
    if not path.is_file() or any(part in ('__pycache__','results','report','provenance') for part in relative.parts):
        continue
    if path==OUT:
        continue
    data=path.read_bytes()
    files[relative.as_posix()]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
record={'record':'JRR-CONTINUATION-REPAIR-2026-11-19-009',
        'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'stage':'before assigned Round09 execution', 'native_model_participants':0,
        'planned_executions':237,
        'candidate_sha256':files['controller.py']['sha256'],
        'challenge_sha256':files['protocol/stress_cases.json']['sha256'], 'files':files}
OUT.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print(json.dumps({'files':len(files),'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),
                  'candidate_sha256':record['candidate_sha256']}))
