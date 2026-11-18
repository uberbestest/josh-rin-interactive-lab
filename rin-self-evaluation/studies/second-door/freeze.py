"""Bind the reviewed prospective instrument before any native participant acts."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT = Path(__file__).resolve().parent
RECORD = 'JRR-SECOND-DOOR-2026-11-18-005'

def freeze():
    assert not (ROOT/'protocol/frozen.json').exists(), 'A freeze already exists; do not overwrite it.'
    assert not list((ROOT/'runs').glob('*/events.jsonl')), 'Native events exist; no retrospective freeze.'
    assert not list((ROOT/'runs').glob('*/final_report.json')), 'Native reports exist.'
    assignments = json.loads((ROOT/'protocol/assignments.json').read_text())['assignments']
    assert len(assignments) == 48
    preflight=json.loads((ROOT/'protocol/preflight.json').read_text())
    assert preflight['status']=='PASS' and preflight['semantic_tests']>=36
    for name, expected in preflight['checked_source_hashes'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected, 'Source changed after preflight: '+name
    protocol_names = ['PROTOCOL.md','CONTRACT.md','cases.json','assignments.json','feasibility.json',
                      'design_review.md','scoring_review.md','oracle_audit.json','preflight.json']
    files = sorted(ROOT.glob('*.py')) + [ROOT/'protocol'/name for name in protocol_names]
    for assignment in assignments:
        directory=ROOT/'runs'/assignment['run_id']
        files.extend(directory/name for name in ['initial_state.json','prompt.txt','dispatch_message.txt'])
        assert (directory/'initial_state.json').read_bytes() == (directory/'state.json').read_bytes(), 'Initial mutable state differs.'
    digests={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    result={'record':RECORD,'status_at_freeze':'prospective; no native participant events recorded',
            'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'source_hashes':digests,'native_contexts_planned':48,'families':12,'fresh_replicates_per_model_per_family':2,
            'requested_models':['gpt-6-astra','gpt-6.2-astra'],
            'scope':'Same-lab prospective source binding. The separate GitHub commit receipt is recorded after commit and before native dispatch.'}
    destination=ROOT/'protocol/frozen.json'
    destination.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'frozen_files':len(digests),'freeze_sha256':hashlib.sha256(destination.read_bytes()).hexdigest()}))

if __name__ == '__main__':
    freeze()
