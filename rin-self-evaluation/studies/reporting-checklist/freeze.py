"""Bind the reviewed prospective reporting-condition experiment before dispatch."""
from pathlib import Path
import datetime
import hashlib
import json

from preflight import checked_source_paths
from engine import report_bytes

ROOT = Path(__file__).resolve().parent
RECORD = 'JRR-CHECKLIST-2026-11-18-006'


def freeze():
    assert not (ROOT/'protocol/frozen.json').exists(), 'A freeze already exists; do not overwrite it.'
    assert not list((ROOT/'runs').glob('*/events.jsonl')), 'Native events exist; no retrospective freeze.'
    assert not list((ROOT/'runs').glob('*/final_report.json')), 'Native reports exist.'
    assignments = json.loads((ROOT/'protocol/assignments.json').read_text())['assignments']
    assert len(assignments) == 48
    preflight = json.loads((ROOT/'protocol/preflight.json').read_text())
    assert preflight['status'] == 'PASS' and preflight['semantic_tests'] >= 48
    current = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
               for path in checked_source_paths(ROOT)}
    assert current == preflight['checked_source_hashes'], 'Sources changed after preflight or an unreviewed source was added.'
    files = checked_source_paths(ROOT) + [ROOT/'protocol/preflight.json']
    for assignment in assignments:
        directory = ROOT/'runs'/assignment['run_id']
        files.extend(directory/name for name in ['initial_state.json', 'prompt.txt', 'dispatch_message.txt'])
        assert (directory/'initial_state.json').read_bytes() == (directory/'state.json').read_bytes()
    hashes = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(files)}
    result = {'record': RECORD, 'status_at_freeze': 'prospective; no native participant events recorded',
              'frozen_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'source_hashes': hashes, 'native_contexts_planned': 48, 'families': 12,
              'fresh_contexts_per_model_condition_family': 1,
              'requested_models': ['gpt-6-astra', 'gpt-6.2-astra'],
              'report_conditions': ['checklist', 'open'],
              'scope': 'Same-lab prospective source, case, prompt, condition and assignment binding. Separate GitHub commit provenance is recorded before native dispatch.'}
    destination = ROOT/'protocol/frozen.json'
    destination.write_bytes(report_bytes(result))
    print(json.dumps({'frozen_files': len(hashes), 'freeze_sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    freeze()
