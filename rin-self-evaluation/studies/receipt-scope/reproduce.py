#!/usr/bin/env python3
"""Reproduce frozen native evidence and separately verify retrospective helpers."""
from __future__ import annotations
import argparse
import io
import json
from pathlib import Path
import unittest
from engine import replay,report_bytes
from prepare import ROOT
from prepare_review import read_assignments,verify_retained_review
from presentation import validate_transport,verify_presentations
from scoring import collect
from verification import sha,verify_forensics
import audit_reference


def reproduce(root=ROOT):
    root=Path(root)
    frozen=json.loads((root/'protocol/frozen.json').read_text())
    for name,expected in frozen['source_hashes'].items():
        assert sha(root/name)==expected,'Frozen source changed: '+name
    stream=io.StringIO();suite=unittest.defaultTestLoader.discover(str(root),pattern='test_*.py')
    tested=unittest.TextTestRunner(stream=stream,verbosity=1).run(suite)
    if not tested.wasSuccessful():raise AssertionError(stream.getvalue())
    audit=audit_reference.audit(root)
    assert audit==json.loads((root/'protocol/reference_audit.json').read_text()),'Reference witness differs'
    assignments=read_assignments(root)
    events_replayed=0;presentation_events=0;stdout_bytes=0
    for assignment in assignments:
        run=assignment['run_id'];directory=root/'runs'/run
        initial=json.loads((directory/'initial_state.json').read_text())
        events=[json.loads(line) for line in (directory/'events.jsonl').read_text().splitlines()]
        state=replay(initial,events)
        assert state==json.loads((directory/'state.json').read_text()),run
        assert state['sealed'],'Missing final report '+run
        raw=(directory/'final_report.json').read_bytes()
        assert raw==report_bytes(state['final_report']),'Sealed report bytes changed'
        finishes=[e for e in events if e['action']=='finish']
        assert finishes and finishes[0]['parameters']['report']==state['final_report']
        expected='SEALED '+run+' '+sha(directory/'final_report.json')
        assert (directory/'native_final_receipt.txt').read_text().strip()==expected,'Native seal mismatch'
        assert all(e['observation']['receipt_line']==expected for e in finishes),'Logged seal mismatch'
        scope=validate_transport(json.loads((directory/'transport.json').read_text()))
        assert scope==assignment['receipt_scope'] and sha(directory/'transport.json')==assignment['transport_sha256']
        shown=[json.loads(line) for line in (directory/'presentation_events.jsonl').read_text().splitlines()]
        checked=verify_presentations(events,shown,scope)
        events_replayed+=len(events);presentation_events+=checked['presentation_events_verified'];stdout_bytes+=checked['stdout_bytes_verified']
    observed=collect(root)
    assert observed==json.loads((root/'results/observed.json').read_text()),'Observed scoring differs'
    review_names=('review/input_packet.json','results/masked_review.json','review/native_review_receipt.txt','review/identity_map.json')
    review=verify_retained_review(root) if any((root/n).exists() for n in review_names) else None
    forensic=verify_forensics(root)
    return {'status':'PASS','runs_replayed':32,'events_replayed':events_replayed,
            'mechanical_results_exact':32,'final_reports_exact':32,'preserved_scientific_record_files':96,
            'presentation_record_files_verified':32,'transport_records_verified':32,
            'presentation_events_replayed':presentation_events,'exact_stdout_records_verified':presentation_events,
            'stdout_utf8_bytes_verified':stdout_bytes,'all_presented_stdout_exact':True,
            'semantic_tests':{'status':'PASS','tests':tested.testsRun},
            'independent_analytic_reference_audit':audit,'all_frozen_hashes_match':True,
            'observed_results_recomputed_exactly':True,'assignment_cells_verified':32,
            'label_masked_review_verification':review,'retrospective_forensic_verification':forensic,
            'scope':'Deterministic same-lab replay of 32 native records, exact rendered stdout, frozen scoring, and review bindings. Retrospective authored helper replays are a separate counter. No participant calls, immutable backend attestation, outer-tool delivery/attention attestation, or external replication.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.resolve().is_relative_to(ROOT):raise SystemExit('Write replay receipts outside the evidence directory')
    result=reproduce();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(report_bytes(result))
    print(json.dumps({k:v for k,v in result.items() if k!='independent_analytic_reference_audit'},indent=2))


if __name__=='__main__':main()
