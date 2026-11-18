#!/usr/bin/env python3
"""Describe retained traces; never launch, alter or reclassify participants."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import replay
from prepare import MODELS, SCOPES, ORIENTATIONS, RECORD
from prepare_review import write_new_or_identical
from presentation import verify_presentations, validate_transport
from scoring import collect

INPUT_FILES = ('initial_state.json', 'state.json', 'events.jsonl',
               'presentation_events.jsonl', 'transport.json',
               'final_report.json', 'native_final_receipt.txt')


def describe(row, root):
    directory = root / 'runs' / row['run_id']
    raw = {name: (directory / name).read_bytes() for name in INPUT_FILES}
    initial = json.loads(raw['initial_state.json'])
    state = json.loads(raw['state.json'])
    events = [json.loads(line) for line in raw['events.jsonl'].splitlines()]
    shown = [json.loads(line) for line in raw['presentation_events.jsonl'].splitlines()]
    if replay(initial, events) != state:
        raise ValueError('Canonical native event replay differs from retained state')
    scope = validate_transport(json.loads(raw['transport.json']))
    if scope != row['receipt_scope']:
        raise ValueError('Receipt transport differs from frozen assignment')
    verify_presentations(events, shown, scope)
    actions = []
    prior_actions = initial['actions_taken']
    for event in events:
        status = event['observation']['local_status']
        admitted = status['actions_taken'] > prior_actions
        prior_actions = status['actions_taken']
        if event['action'] not in ('receipt', 'commit', 'finalize', 'wait'):
            continue
        actions.append({'event_index': event['index'], 'action': event['action'],
                        'parameters': event['parameters'],
                        'result': event['observation']['status'],
                        'reason': event['observation'].get('reason'),
                        'admitted_attempt': admitted,
                        'tick_after': status['tick'],
                        'uses_remaining_after': status['uses_remaining']})
    d = {key: row[key] for key in ('run_id', 'case_id', 'family_id', 'replicate',
                                  'requested_model', 'report_condition',
                                  'receipt_scope', 'orientation', 'stratum')}
    d.update(actions=actions,
             input_sha256={name: sha256(data).hexdigest() for name, data in raw.items()},
             all_nonreport_actions=[{'action': e['action'], 'parameters': e['parameters']}
                                    for e in events if e['action'] != 'finish'],
             starts_with_status=bool(events and events[0]['action'] == 'status'),
             report_top_level_fields=sorted(row['report']),
             receipt_stdout_utf8_bytes=sum(len(p['stdout'].encode('utf-8'))
                                           for e, p in zip(events, shown) if e['action'] == 'receipt'),
             nonreport_stdout_utf8_bytes=sum(len(p['stdout'].encode('utf-8'))
                                             for e, p in zip(events, shown) if e['action'] != 'finish'),
             acknowledged_deliveries_left_unfinalized=[j for j in ('A', 'B')
                 if state['commits_made'][j] == 1 and not state['actual_world'][j]['prior_delivered'] and not state['finalized'][j]],
             hidden_original_deliveries_left_unfinalized=[j for j in ('A', 'B')
                 if state['actual_world'][j]['prior_delivered'] and not state['commits_made'][j] and not state['finalized'][j]])
    # These fields and all mechanical outcomes are sourced from the frozen
    # scorer; the analysis does not introduce alternative endpoint definitions.
    for key in ('free_status_reads', 'report_utf8_bytes', 'summary_word_count',
                'opening_choice', 'receipt_query_total', 'uses_spent', 'elapsed_ticks',
                'service_wait_attempts', 'uses_remaining', 'safe_joint_completion',
                'has_commit_after_committed_attempt', 'duplicate_effects'):
        d[key] = row[key]
    return d


def summarize(rows):
    words = [r['summary_word_count'] for r in rows if r['summary_word_count'] is not None]
    return {
        'contexts': len(rows),
        'summary_words_total': sum(words),
        'summaries_with_word_count': len(words),
        'summary_words_by_run': {r['run_id']: r['summary_word_count'] for r in rows},
        'report_utf8_bytes_total': sum(r['report_utf8_bytes'] for r in rows),
        'free_status_reads': sum(r['free_status_reads'] for r in rows),
        'receipt_queries': sum(r['receipt_query_total'] for r in rows),
        'key_uses': sum(r['uses_spent'] for r in rows),
        'logical_ticks': sum(r['elapsed_ticks'] for r in rows),
        'service_wait_attempts': sum(r['service_wait_attempts'] for r in rows),
        'remaining_uses': sum(r['uses_remaining'] for r in rows),
        'opening_choice_by_run': {r['run_id']: r['opening_choice'] for r in rows},
        'runs_starting_with_status': sum(r['starts_with_status'] for r in rows),
        'receipt_stdout_utf8_bytes': sum(r['receipt_stdout_utf8_bytes'] for r in rows),
        'nonreport_stdout_utf8_bytes': sum(r['nonreport_stdout_utf8_bytes'] for r in rows),
        'acknowledged_unfinalized_delivery_runs': [r['run_id'] for r in rows if r['acknowledged_deliveries_left_unfinalized']],
        'hidden_original_unfinalized_delivery_runs': [r['run_id'] for r in rows if r['hidden_original_deliveries_left_unfinalized']],
        'top_level_field_frequencies': dict(Counter(k for r in rows for k in r['report_top_level_fields'])),
    }


def paired_description(pair, index, labels, difference_prefix):
    first, second = [index[pair['run_ids'][label]] for label in labels]
    normalized = lambda row: [{key: value for key, value in action.items() if key != 'event_index'}
                              for action in row['actions']]
    opening = lambda row: None if row['opening_choice'] is None else {
        key: value for key, value in row['opening_choice'].items() if key != 'event_index'}
    fields = ('free_status_reads', 'report_utf8_bytes', 'summary_word_count',
              'receipt_stdout_utf8_bytes', 'nonreport_stdout_utf8_bytes')
    deltas = {difference_prefix + '_' + key:
              None if first[key] is None or second[key] is None else second[key] - first[key]
              for key in fields}
    # Every already-frozen pair contrast is retained verbatim for the exact join.
    return {**pair,
            'service_wait_actions_and_outcomes_identical': normalized(first) == normalized(second),
            'all_nonreport_actions_identical': first['all_nonreport_actions'] == second['all_nonreport_actions'],
            'opening_choice_identical': opening(first) == opening(second),
            'frozen_numeric_contrasts_all_zero': not any(value for key, value in pair.items()
                                                        if key.startswith(difference_prefix + '_')
                                                        and isinstance(value, (int, float))),
            **deltas}


def build(root=ROOT):
    root = Path(root)
    observed_path = root / 'results/observed.json'
    observed = json.loads(observed_path.read_bytes())
    if observed != collect(root) or observed['record'] != RECORD:
        raise ValueError('Observed results differ from the frozen mechanical scorer')
    descriptions = [describe(row, root) for row in observed['runs']]
    index = {row['run_id']: row for row in descriptions}
    scope_pairs = [paired_description(pair, index, SCOPES, 'target_minus_combined')
                   for pair in observed['matched_scope_pairs']]
    model_pairs = [paired_description(pair, index, MODELS, 'new_minus_old')
                   for pair in observed['matched_model_pairs']]
    groups, strata = {}, {}
    for model in MODELS:
        groups[model], strata[model] = {}, {}
        for scope in SCOPES:
            cell = [r for r in descriptions if r['requested_model'] == model and r['receipt_scope'] == scope]
            if len(cell) != 8:
                raise ValueError('Eight assigned contexts required per selector/scope')
            groups[model][scope] = summarize(cell)
            strata[model][scope] = {}
            for orientation in ORIENTATIONS:
                selected = [r for r in cell if r['orientation'] == orientation]
                if len(selected) != 4:
                    raise ValueError('Four assigned contexts required per orientation stratum')
                strata[model][scope][orientation] = summarize(selected)
    sources = ('results/observed.json', 'protocol/assignments.json',
               'scoring.py', 'inherited_scoring.py', 'engine.py', 'presentation.py',
               'analysis/describe_runs.py')
    return {'record': RECORD, 'kind': 'descriptive analysis of retained native traces',
            'source_hashes': {name: sha256((root / name).read_bytes()).hexdigest() for name in sources},
            'matched_scope_pairs': scope_pairs, 'matched_model_pairs': model_pairs,
            'groups': groups, 'orientation_groups': strata, 'runs': descriptions,
            'scope': 'These are additional views of the same 32 frozen native assignments, not new participants or independent endpoints. One authored family is repeated in two mirrored settings. Mechanical measurements come from the frozen scorer. Matching observed action sequences does not establish identical contingent policies or general equivalence. Client stdout byte counts describe output supplied into the participant execution path; they are not model token counts or proof of outer-tool delivery, reading or attention. Source/parser use and internal cognitive causes are not measured. Hidden original delivery diagnostics are explicitly oracle-derived, not claims of participant knowledge.'}


def main():
    output = build()
    write_new_or_identical(ROOT / 'results/descriptive.json', output)
    print(json.dumps({'status': 'PASS', 'contexts': len(output['runs']),
                      'scope_pairs': len(output['matched_scope_pairs']),
                      'model_pairs': len(output['matched_model_pairs']),
                      'scope_pairs_with_identical_service_wait_sequences': sum(p['service_wait_actions_and_outcomes_identical'] for p in output['matched_scope_pairs']),
                      'scope_pairs_with_identical_all_nonreport_sequences': sum(p['all_nonreport_actions_identical'] for p in output['matched_scope_pairs'])}))


if __name__ == '__main__':
    main()
