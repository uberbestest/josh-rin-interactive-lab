#!/usr/bin/env python3
"""Run frozen scripted policies. No model, network, or paid API is invoked.

The candidate runs as a separate JSONL process receiving only public status
and shown responses. This is an information interface, not an OS sandbox.
"""
from __future__ import annotations
import argparse
import collections
import copy
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + '\n')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def engine_module():
    return module('continuation_reference_engine', ROOT / 'input/engine.py')


def verify_freeze():
    path = ROOT / 'protocol/frozen.json'
    frozen = read(path)
    required = {'controller.py', 'comparators.py', 'run_study.py', 'input/engine.py',
                'input/client.py', 'input/COMMON_CONTRACT.md', 'protocol/lineage.json',
                'protocol/stress_cases.json', 'protocol/round08_cases.json',
                'independent_check.py', 'protocol/PROTOCOL.md',
                'reference_round08/execute.py', 'reference_round08/run_helper.mjs',
                'reference_round08/input/client.py', 'reference_round08/input/engine.py'}
    required |= {'reference_round08/helpers/'+helper+'_'+part+'.js'
                 for helper in ('w041', 'w042') for part in ('setup', 'status_job_guard')}
    required |= {str(p.relative_to(ROOT)) for p in (ROOT/'reference_round08').rglob('*')
                 if p.is_file() and p.suffix in ('.py', '.mjs', '.js', '.md', '.json')}
    if not required.issubset(frozen['files']):
        raise ValueError('Required executable inputs missing from source freeze')
    for name, expected in frozen['files'].items():
        original = ROOT / name
        target = original.resolve()
        if not target.is_relative_to(ROOT) or original.is_symlink() or sha(target) != expected['sha256']:
            raise ValueError('Frozen source mismatch: ' + name)
    return {'frozen_sha256': sha(path), 'frozen_file_count': len(frozen['files'])}


class CandidateProcess:
    response_timeout = 45.0
    max_response_bytes = 1024 * 1024

    def __init__(self):
        self.folder = tempfile.TemporaryDirectory(prefix='continuation-policy-')
        self.buffer = b''
        self.stderr_bytes = 0
        self.stderr_digest = hashlib.sha256()
        try:
            self.process = subprocess.Popen([sys.executable, '-I', '-B', str(ROOT/'controller.py')],
                                            cwd=self.folder.name, stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        except Exception:
            self.folder.cleanup()
            raise

    def send(self, obj):
        self.process.stdin.write((json.dumps(obj) + '\n').encode('utf-8'))
        self.process.stdin.flush()
        deadline = time.monotonic() + self.response_timeout
        with selectors.DefaultSelector() as select:
            select.register(self.process.stdout, selectors.EVENT_READ, 'stdout')
            select.register(self.process.stderr, selectors.EVENT_READ, 'stderr')
            while b'\n' not in self.buffer:
                remaining = deadline - time.monotonic()
                ready = select.select(max(0, remaining)) if remaining > 0 else []
                if not ready:
                    self.process.kill()
                    raise TimeoutError('candidate_response_timeout')
                for key, _ in ready:
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        select.unregister(key.fileobj)
                        if key.data == 'stdout':
                            raise RuntimeError('candidate_process_ended_before_response')
                        continue
                    if key.data == 'stderr':
                        self.stderr_bytes += len(chunk)
                        self.stderr_digest.update(chunk)
                    else:
                        self.buffer += chunk
                        if len(self.buffer) > self.max_response_bytes:
                            raise ValueError('candidate_response_too_large')
        line, self.buffer = self.buffer.split(b'\n', 1)
        try:
            value = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError('candidate_output_invalid_json') from None
        if not isinstance(value, dict):
            raise ValueError('candidate_output_not_object')
        return value

    def next_action(self, status):
        return self.send({'op': 'decide', 'status': status})

    def observe_response(self, request, response):
        return self.send({'op': 'observe', 'request': request, 'response': response})

    def close(self):
        try:
            if self.process.poll() is None:
                try:
                    self.process.stdin.close()
                except BrokenPipeError:
                    pass
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
        finally:
            for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                stream.close()
            self.folder.cleanup()


def error_record(problem, stage):
    message = str(problem)
    return {'type': type(problem).__name__, 'stage': stage,
            'code': message if re.fullmatch(r'[A-Za-z0-9_.:-]{1,160}', message) else 'execution_error'}


def report_check(engine, state):
    """Validate declared mechanical facts; prose meaning is not machine-scored."""
    errors = []
    if state is None:
        return {'valid': False, 'errors': ['no_final_state'], 'scope': 'mechanical_fields_only'}
    report = state.get('final_report')
    if not state.get('sealed'):
        errors.append('report_not_sealed')
    if not isinstance(report, dict):
        return {'valid': False, 'errors': errors + ['missing_report_object'], 'scope': 'mechanical_fields_only'}
    expected = {'joint_complete': all(state['finalized'].values()),
                'uses_remaining': state['uses_remaining'], 'tick': state['tick']}
    for key, value in expected.items():
        if type(report.get(key)) is not type(value) or report[key] != value:
            errors.append('incorrect_' + key)
    if not isinstance(report.get('summary'), str) or len(report['summary'].split()) > 160:
        errors.append('invalid_summary')
    if 'jobs' in report:
        jobs = report['jobs']
        public = engine.public_status(state)['jobs']
        if not isinstance(jobs, dict) or set(jobs) != set(public):
            errors.append('invalid_job_accounting')
        else:
            for job, claims in jobs.items():
                if not isinstance(claims, dict):
                    errors.append('invalid_job_' + job)
                    continue
                for key, value in claims.items():
                    if key in public[job] and (type(value) is not type(public[job][key]) or value != public[job][key]):
                        errors.append('incorrect_job_' + job + '_' + key)
    if 'guaranteed_finalized_value' in report:
        value = report['guaranteed_finalized_value']
        if (not isinstance(value, list) or any(type(x) is not int for x in value)
                or value != list(engine.optimal_value(state))):
            errors.append('incorrect_guaranteed_finalized_value')
    return {'valid': not errors, 'errors': errors, 'scope': 'mechanical_fields_only',
            'summary_semantics_checked': False, 'unrecognized_additional_fields_checked': False}


def params_for(decision):
    action = decision.get('action')
    if action in ('receipt', 'commit', 'finalize'):
        if decision.get('job') not in ('A', 'B'):
            raise ValueError('invalid_action_job')
        return action, {'job': decision['job']}
    if action == 'wait' and type(decision.get('ticks')) is int and 1 <= decision['ticks'] <= 20:
        return action, {'ticks': decision['ticks']}
    if action == 'finish' and isinstance(decision.get('report'), dict):
        return action, {'report': decision['report']}
    raise ValueError('invalid_policy_decision')


def run_episode(engine, case, actual_world, policy_name, run_id, output_dir,
                suite='challenge', adapter='identity'):
    initial, state, initial_value, policy = None, None, None, None
    events, exchanges = [], []
    applied, replay_ok = False, False
    error, cleanup_error, verification_error = None, None, None
    stage = 'initialize_case'

    def perform(action, parameters):
        nonlocal state
        after, observation, oracle = engine.transition(state, action, **parameters)
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        event = engine.new_event(len(events), events[-1]['event_sha256'] if events else '0'*64,
                                 state, after, action, parameters, observation, oracle, timestamp)
        events.append(event)
        state = after
        return observation

    try:
        config = copy.deepcopy(case['config'])
        config['run_id'] = run_id
        initial = engine.make_initial_state(config, actual_world)
        state = copy.deepcopy(initial)
        stage = 'initial_guarantee'
        initial_value = list(engine.optimal_value(initial))
        stage = 'initialize_policy'
        policy = CandidateProcess() if policy_name == 'candidate' else module(
            'continuation_baselines', ROOT/'comparators.py').POLICIES[policy_name]()
        for _ in range(config.get('max_actions', 32) + 2):
            stage = 'public_status'
            status_observation = perform('status', {})
            status = status_observation['local_status']
            stage = 'policy_decision'
            decision = policy.next_action(copy.deepcopy(status))
            action, parameters = params_for(decision)
            stage = 'service_transition'
            canonical = perform(action, parameters)
            shown = copy.deepcopy(canonical)
            changed = False
            # Fixed Round09 transfer of the Round08 fault rule: change the
            # first selected B header, whether the canonical answer is pending
            # or already resolved under the candidate's different schedule.
            if adapter == 'misbound_committed_A' and action == 'receipt' and parameters.get('job') == 'B' and not applied:
                shown.update(status='COMMITTED', job='A', coverage='AUTHORITATIVE_FINAL')
                applied = changed = True
            request = dict(action=action, **parameters)
            exchange = {'public_status': status, 'decision': decision, 'event_index': len(events)-1,
                        'request': request, 'canonical_observation': canonical,
                        'shown_observation': shown, 'validation': None,
                        'adapter_applied': changed}
            # Preserve the issued action even if observing its response fails.
            exchanges.append(exchange)
            stage = 'policy_response_validation'
            validated = policy.observe_response(copy.deepcopy(request), copy.deepcopy(shown))
            if not isinstance(validated, dict):
                raise ValueError('policy_validation_not_object')
            exchange['validation'] = validated
            if action == 'finish':
                break
        else:
            raise RuntimeError('policy_failed_to_finish')
    except Exception as problem:
        # Preserve the assignment even if initialization or subprocess creation failed.
        error = error_record(problem, stage)
    finally:
        if isinstance(policy, CandidateProcess):
            try:
                policy.close()
            except Exception as problem:
                cleanup_error = error_record(problem, 'policy_cleanup')
                if error is None:
                    error = cleanup_error

    if initial is not None and state is not None:
        try:
            replay_ok = engine.replay(initial, events) == state
            if not replay_ok:
                raise AssertionError('canonical_event_replay_mismatch')
        except Exception as problem:
            verification_error = error_record(problem, 'canonical_replay')
            if error is None:
                error = verification_error
    try:
        report_validation = report_check(engine, state)
    except Exception as problem:
        report_validation = {'valid': False, 'errors': ['report_check_error'], 'scope': 'mechanical_fields_only'}
        if error is None:
            error = error_record(problem, 'report_check')

    observed = state is not None
    final = state
    achieved = ([sum(final['finalized'].values()), int(final['finalized'][case['config']['priority']])]
                if observed else None)
    safe_achieved = (achieved if final['unsafe_attempts'] == 0 else [0, 0]) if observed else None
    attained = (initial_value is not None and safe_achieved is not None
                and tuple(safe_achieved) >= tuple(initial_value))
    protocol_complete = observed and final['sealed'] and report_validation['valid'] and error is None and replay_ok
    diagnostics = {
        'initial_guaranteed_value': initial_value, 'achieved_value': achieved,
        'safe_achieved_value': safe_achieved,
        'attained_initial_guarantee': attained,
        'protocol_complete_guarantee_attained': protocol_complete and attained,
        'safe_joint_completion': observed and all(final['finalized'].values()) and final['unsafe_attempts'] == 0,
        'protocol_complete_safe_joint_completion': protocol_complete and all(final['finalized'].values()) and final['unsafe_attempts'] == 0,
        'mechanical_state_observed': observed,
        'mechanical_report_valid': report_validation['valid'],
        'report_validation': report_validation,
        'protocol_complete': protocol_complete, 'canonical_replay_ok': replay_ok,
        'unsafe_attempts': final['unsafe_attempts'] if observed else None,
        'duplicate_effects': sum(final['duplicate_effects'].values()) if observed else None,
        'risky_selections': sum(e['oracle']['risk_at_selection'] for e in events),
        'realized_guarantee_losses': sum(e['oracle']['realized_value_loss'] for e in events),
        'guarantee_declaration_disagreements': sum(
            'guaranteed_value' in x['decision'] and x['decision']['guaranteed_value'] !=
            events[x['event_index']]['oracle']['pre_value'] for x in exchanges),
        'uses_spent': initial['uses_remaining'] - final['uses_remaining'] if observed and initial is not None else None,
        'ticks_elapsed': final['tick'] if observed else None,
        'service_actions': final['actions_taken'] if observed else None,
        'receipt_queries': sum(final['query_count'].values()) if observed else None,
        'header_rejections': sum(isinstance(x['validation'], dict) and x['validation'].get('accepted') is False for x in exchanges),
        'unvalidated_exchanges': sum(x['validation'] is None for x in exchanges),
        'adapter_applications': sum(x['adapter_applied'] for x in exchanges),
        'sealed': final['sealed'] if observed else False, 'infrastructure_error': error,
        'cleanup_error': cleanup_error, 'verification_error': verification_error,
    }
    record = {'run_id': run_id, 'suite': suite, 'policy': policy_name,
              'case_id': case['case_id'], 'adapter': adapter,
              'initial_state': initial, 'events': events, 'exchanges': exchanges,
              'final_state': final, 'diagnostics': diagnostics,
              'no_replacement_run_performed': True}
    dump(output_dir/'runs'/(run_id+'.json'), record)
    return record


def summarize(records):
    cells = []
    for suite, policy in dict.fromkeys((r['suite'], r['policy']) for r in records):
        selected = [r for r in records if (r['suite'], r['policy']) == (suite, policy)]
        known = [r for r in selected if r['diagnostics']['initial_guaranteed_value'] is not None]
        eligible = [r for r in known if r['diagnostics']['initial_guaranteed_value'][0] > 0]
        joint = [r for r in known if r['diagnostics']['initial_guaranteed_value'][0] == 2]
        cells.append({'suite': suite, 'policy': policy, 'executions': len(selected),
                      'positive_guarantee_cases': len(eligible),
                      'positive_guarantees_attained': sum(r['diagnostics']['attained_initial_guarantee'] for r in eligible),
                      'protocol_complete_positive_guarantees_attained': sum(r['diagnostics']['protocol_complete_guarantee_attained'] for r in eligible),
                      'initial_joint_cases': len(joint),
                      'safe_joint_completions_in_joint_cases': sum(r['diagnostics']['safe_joint_completion'] for r in joint),
                      'safe_joint_completions_all_cases': sum(r['diagnostics']['safe_joint_completion'] for r in selected),
                      'protocol_complete_executions': sum(r['diagnostics']['protocol_complete'] for r in selected),
                      'mechanical_reports_valid': sum(r['diagnostics']['mechanical_report_valid'] for r in selected),
                      'protocol_complete_safe_joint_completions_in_joint_cases': sum(r['diagnostics']['protocol_complete_safe_joint_completion'] for r in joint),
                      'unsafe_executions': sum((r['diagnostics']['unsafe_attempts'] or 0) > 0 for r in selected),
                      'risky_selection_executions': sum(r['diagnostics']['risky_selections'] > 0 for r in selected),
                      'guarantee_loss_executions': sum(r['diagnostics']['realized_guarantee_losses'] > 0 for r in selected),
                      'declaration_disagreements': sum(r['diagnostics']['guarantee_declaration_disagreements'] for r in selected),
                      'infrastructure_errors': sum(r['diagnostics']['infrastructure_error'] is not None for r in selected),
                      'zero_guarantee_cases': len(known)-len(eligible),
                      'unknown_initial_guarantee_cases': len(selected)-len(known),
                      'header_rejections': sum(r['diagnostics']['header_rejections'] for r in selected)})
    return {'cells': cells, 'executions': len(records), 'native_model_participants': 0,
            'events': sum(len(r['events']) for r in records),
            'results': [{'run_id':r['run_id'], 'case_id':r['case_id'], 'suite':r['suite'],
                         'policy':r['policy'], **r['diagnostics']} for r in records]}


def execute(out, skip_legacy=False):
    freeze = verify_freeze()
    if out.exists() and any(out.iterdir()):
        raise ValueError('Output directory must be new or empty')
    out.mkdir(parents=True, exist_ok=True)
    challenge = read(ROOT/'protocol/stress_cases.json')
    round08 = read(ROOT/'protocol/round08_cases.json')
    round08 = round08 if isinstance(round08, list) else round08['cases']
    planned_primary = len(challenge['assignments'])*3 + len(round08)
    planned_legacy = 0 if skip_legacy else len(round08)*2
    planned = {'primary_executions': planned_primary, 'legacy_executions': planned_legacy,
               'total_executions': planned_primary+planned_legacy,
               'challenge_configurations': len(challenge['cases']),
               'challenge_world_assignments': len(challenge['assignments']),
               'unit': 'deterministic assignments; not independent model samples'}
    dump(out/'execution_plan.json', planned)
    engine = engine_module()
    records=[]
    mapping = {case['case_id']: case for case in challenge['cases']}
    for assignment in challenge['assignments']:
        case = mapping[assignment['case_id']]
        world = case['worlds'][assignment['world_index']]
        for policy in ('candidate', 'deadline_greedy', 'wait_all_greedy'):
            run_id = assignment['assignment_id']+'_'+policy
            record = run_episode(engine, case, world, policy, run_id, out)
            records.append(record)
        if len(records) % 30 == 0:
            print(json.dumps({'completed':len(records), 'phase':'challenge'}), flush=True)
    for case in round08:
        records.append(run_episode(engine, case, case['actual_world'], 'candidate',
                                   case['case_id']+'_candidate', out,
                                   suite='round08_regression', adapter=case['adapter']))
    legacy_rows=[]
    if not skip_legacy:
        try:
            legacy = module('continuation_legacy_runner', ROOT/'reference_round08/execute.py')
        except Exception:
            legacy = None
        node = shutil.which('node')
        for case in round08:
            for helper in ('w041', 'w042'):
                try:
                    if legacy is None:
                        raise RuntimeError('legacy_loader_failed')
                    if not node:
                        raise RuntimeError('node_unavailable')
                    legacy_rows.append(legacy.run_one(engine, node, case, helper, 'status_job_guard', out/'legacy'))
                except Exception as problem:
                    run_id = case['case_id']+'_'+helper+'_status_job_guard'
                    row = {'run_id': run_id, 'case_id': case['case_id'], 'helper_id': helper,
                           'arm': 'status_job_guard', 'status': 'INFRASTRUCTURE_ERROR',
                           'infrastructure_error': error_record(problem, 'legacy_execution'),
                           'no_replacement_run_performed': True}
                    dump(out/'legacy'/'failed_assignments'/(run_id+'.json'), row)
                    legacy_rows.append(row)
    summary = summarize(records)
    primary_errors = sum(r['diagnostics']['infrastructure_error'] is not None for r in records)
    legacy_errors = sum(r.get('infrastructure_error') is not None for r in legacy_rows)
    summary.update(freeze, legacy_executions=len(legacy_rows), legacy_results=legacy_rows,
                   total_executions=len(records)+len(legacy_rows), planned=planned,
                   attempted_primary_executions=len(records), attempted_legacy_executions=len(legacy_rows),
                   primary_execution_errors=primary_errors, legacy_execution_errors=legacy_errors,
                   completed_without_execution_error=len(records)+len(legacy_rows)-primary_errors-legacy_errors,
                   total_execution_errors=primary_errors+legacy_errors,
                   source_kind='finite scripted controller and original-helper executions',
                   python_version=sys.version.split()[0])
    dump(out/'summary.json', summary)
    return summary


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--skip-legacy', action='store_true')
    args=parser.parse_args()
    result=execute(args.output.resolve(), args.skip_legacy)
    print(json.dumps({'executions':result['executions'], 'legacy_executions':result['legacy_executions'],
                      'total_executions':result['total_executions'], 'total_execution_errors':result['total_execution_errors'],
                      'events':result['events'], 'cells':result['cells']}, indent=2))
