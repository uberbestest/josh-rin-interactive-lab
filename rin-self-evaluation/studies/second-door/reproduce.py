#!/usr/bin/env python3
"""Replay the frozen two-job record. Never starts participant model contexts."""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import unittest
from engine import replay, report_bytes
from scoring import collect

ROOT=Path(__file__).resolve().parent


def reproduce():
    frozen=json.loads((ROOT/'protocol/frozen.json').read_text())
    for name, expected in frozen['source_hashes'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected, 'Frozen source changed: '+name
    suite=unittest.defaultTestLoader.discover(str(ROOT),pattern='test_*.py')
    stream=io.StringIO()
    tested=unittest.TextTestRunner(stream=stream,verbosity=1).run(suite)
    if not tested.wasSuccessful():
        raise AssertionError(stream.getvalue())
    import audit_oracle
    with contextlib.redirect_stdout(io.StringIO()):
        audit=audit_oracle.audit()
    assert audit['status']=='PASS'
    assignments=json.loads((ROOT/'protocol/assignments.json').read_text())['assignments']
    assert len(assignments)==48 and len({a['run_id'] for a in assignments})==48
    events_replayed=0
    for a in assignments:
        directory=ROOT/'runs'/a['run_id']
        initial=json.loads((directory/'initial_state.json').read_text())
        rows=[json.loads(l) for l in (directory/'events.jsonl').read_text().splitlines()]
        state=replay(initial,rows)
        assert state==json.loads((directory/'state.json').read_text()),a['run_id']
        assert state['sealed'], 'Missing final report '+a['run_id']
        raw=(directory/'final_report.json').read_bytes()
        assert raw==report_bytes(state['final_report']), 'Sealed bytes changed'
        finishes=[r for r in rows if r['action']=='finish']
        assert finishes and finishes[0]['parameters']['report']==state['final_report']
        expected='SEALED '+a['run_id']+' '+hashlib.sha256(raw).hexdigest()
        assert (directory/'native_final_receipt.txt').read_text().strip()==expected, 'Native seal mismatch'
        assert finishes[0]['observation']['receipt_line']==expected, 'Logged seal mismatch'
        events_replayed+=len(rows)
    observed=collect(ROOT)
    assert observed==json.loads((ROOT/'results/observed.json').read_text()), 'Observed scoring differs'
    return {'status':'PASS','runs_replayed':48,'events_replayed':events_replayed,
            'mechanical_results_exact':48,'final_reports_exact':48,
            'preserved_scientific_record_files':144,
            'semantic_tests':{'status':'PASS','tests':tested.testsRun},
            'independent_analytic_oracle_audit':audit,
            'all_frozen_hashes_match':True,'observed_results_recomputed_exactly':True,
            'scope':'Deterministic same-lab replay and prospective scoring plus separately derived oracle audit. No participant calls, immutable backend attestation or external replication.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.resolve().is_relative_to(ROOT):
        raise SystemExit('Write replay receipts outside the evidence directory')
    result=reproduce()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='independent_analytic_oracle_audit'},indent=2))


if __name__=='__main__':
    main()
