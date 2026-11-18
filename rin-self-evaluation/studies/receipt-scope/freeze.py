"""Bind the reviewed 32-context native study before any participant dispatch."""
import datetime
import json
from engine import report_bytes
from prepare import ROOT,RECORD,MODELS,SCOPES,ORIENTATIONS
from preflight import checked_source_paths,run_input_paths
from verification import sha


def freeze():
    assert not (ROOT/'protocol/frozen.json').exists(),'A freeze already exists; do not overwrite it'
    for name in ('events.jsonl','presentation_events.jsonl','final_report.json'):
        assert not list((ROOT/'runs').glob('*/'+name)),'Native evidence exists; no retrospective native freeze'
    assignments=json.loads((ROOT/'protocol/assignments.json').read_text())['assignments']
    assert len(assignments)==32
    preflight=json.loads((ROOT/'protocol/preflight.json').read_text())
    assert preflight['status']=='PASS' and preflight['semantic_tests']>=58
    current={p.relative_to(ROOT).as_posix():sha(p) for p in checked_source_paths()}
    assert current==preflight['checked_source_hashes'],'Sources changed after preflight or an unreviewed source was added'
    assert {p.relative_to(ROOT).as_posix():sha(p) for p in run_input_paths(ROOT,assignments)}==preflight['checked_run_input_hashes'], 'Run inputs changed after preflight'
    files=checked_source_paths()+[ROOT/'protocol/preflight.json']
    for assignment in assignments:
        directory=ROOT/'runs'/assignment['run_id']
        files.extend(directory/name for name in ('initial_state.json','prompt.txt','dispatch_message.txt','transport.json'))
        assert (directory/'initial_state.json').read_bytes()==(directory/'state.json').read_bytes()
        assert sha(directory/'transport.json')==assignment['transport_sha256']
    result={'record':RECORD,'status_at_freeze':'prospective native instrument; no fresh participant events recorded',
            'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'source_hashes':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)},
            'native_contexts_planned':32,'underlying_task_families':1,'orientation_settings':2,
            'fresh_contexts_per_model_scope_orientation':4,'requested_models':MODELS,
            'receipt_scopes':SCOPES,'orientations':ORIENTATIONS,'report_condition':'checklist',
            'forensic_status_at_freeze':'already completed retrospective helper replay and counterfactual investigation',
            'scope':'Same-lab prospective native source, case, prompt, transport, assignment, scoring and review binding. Retrospective forensic records are separately bound for integrity; their already-known results are not prospective model outcomes. Separate GitHub commit provenance is retained before native dispatch.'}
    destination=ROOT/'protocol/frozen.json';destination.write_bytes(report_bytes(result))
    print(json.dumps({'frozen_files':len(result['source_hashes']),'freeze_sha256':sha(destination)}))


if __name__=='__main__':freeze()
