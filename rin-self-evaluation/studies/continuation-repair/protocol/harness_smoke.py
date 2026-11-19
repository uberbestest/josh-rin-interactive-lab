"""Mocked infrastructure checks only; does not import the study engine/cases."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time

sys.dont_write_bytecode = True
path = Path(__file__).resolve().parents[1] / 'run_study.py'
spec = importlib.util.spec_from_file_location('audit_harness', path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class FakeEngine:
    def make_initial_state(self, config, actual):
        return {'uses_remaining': 2, 'tick': 0, 'actions_taken': 0,
                'finalized': {'A': False, 'B': False}, 'unsafe_attempts': 0,
                'duplicate_effects': {'A': 0, 'B': 0}, 'query_count': {'A': 0, 'B': 0},
                'sealed': False, 'final_report': None}

    def optimal_value(self, state):
        return (2, 1)

    def replay(self, initial, events):
        assert not events
        return copy.deepcopy(initial)

    def public_status(self, state):
        return {'jobs': {job: {'finalized': done, 'delivery': 'present'}
                         for job, done in state['finalized'].items()}}


case = {'case_id': 'mock_only', 'config': {'priority': 'A', 'max_actions': 2}}
engine = FakeEngine()
initial = engine.make_initial_state(case['config'], {})
state = copy.deepcopy(initial)
state.update(sealed=True, finalized={'A': True, 'B': True}, final_report={})
assert not m.report_check(engine, state)['valid']
state['final_report'] = {'joint_complete': True, 'uses_remaining': 2, 'tick': 0,
                         'summary': 'Both synthetic jobs are complete.'}
assert m.report_check(engine, state)['valid']
state['final_report']['uses_remaining'] = True
assert not m.report_check(engine, state)['valid']
state['final_report']['uses_remaining'] = 2
state['final_report']['jobs'] = {'A': {'finalized': False}, 'B': {'finalized': True}}
assert not m.report_check(engine, state)['valid']


class BrokenCandidate:
    def __init__(self):
        raise OSError('mock_spawn_failure')


original_candidate = m.CandidateProcess
m.CandidateProcess = BrokenCandidate
with tempfile.TemporaryDirectory(prefix='mock-harness-records-') as out:
    row = m.run_episode(engine, case, {}, 'candidate', 'mock_spawn', Path(out))
    assert row['diagnostics']['infrastructure_error']['code'] == 'mock_spawn_failure'
    assert row['diagnostics']['initial_guaranteed_value'] == [2, 1]
    assert not row['diagnostics']['protocol_complete']
    summary = m.summarize([row])
    assert summary['cells'][0]['executions'] == 1
    assert summary['cells'][0]['positive_guarantee_cases'] == 1
    assert summary['cells'][0]['infrastructure_errors'] == 1
    assert Path(out, 'runs/mock_spawn.json').exists()

    class BrokenEngine(FakeEngine):
        def make_initial_state(self, config, actual):
            raise ValueError('mock_initialization_failure')

    row = m.run_episode(BrokenEngine(), case, {}, 'candidate', 'mock_init', Path(out))
    assert row['initial_state'] is None
    assert row['diagnostics']['initial_guaranteed_value'] is None
    summary = m.summarize([row])
    assert summary['cells'][0]['unknown_initial_guarantee_cases'] == 1
    assert summary['cells'][0]['zero_guarantee_cases'] == 0
    assert Path(out, 'runs/mock_init.json').exists()
m.CandidateProcess = original_candidate

original_root = m.ROOT
with tempfile.TemporaryDirectory(prefix='mock-policy-') as folder:
    m.ROOT = Path(folder)
    (m.ROOT/'controller.py').write_text("import sys,time\nsys.stdin.readline()\nsys.stdout.write('{\"partial\":')\nsys.stdout.flush()\ntime.sleep(10)\n")
    process = m.CandidateProcess()
    process.response_timeout = 0.15
    started = time.monotonic()
    try:
        process.send({'mock': True})
        raise AssertionError('Partial stdout did not time out')
    except TimeoutError:
        assert time.monotonic() - started < 3
    finally:
        process.close()

    (m.ROOT/'controller.py').write_text("import sys\nsys.stdin.readline()\nsys.stderr.write('x'*100000)\nsys.stderr.flush()\nprint('{\"ok\":true}',flush=True)\nsys.stdin.readline()\n")
    process = m.CandidateProcess()
    try:
        assert process.send({'mock': True}) == {'ok': True}
        assert process.stderr_bytes == 100000
    finally:
        process.close()
m.ROOT = original_root
print(json.dumps({'status': 'PASS', 'checks': ['report_shape_and_truth', 'strict_counter_types',
    'per_job_truth', 'spawn_failure_retained', 'initialization_failure_retained',
    'unknown_denominator_preserved', 'partial_line_deadline', 'stderr_drained'],
    'empirical_matrix_executions': 0}))
