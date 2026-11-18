#!/usr/bin/env python3
"""Prepare the fixed receipt-response-scope matrix; never start participants."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import random
from engine import make_initial_state, optimal_value, report_bytes

ROOT = Path(__file__).resolve().parent
RECORD = 'JRR-RECEIPT-SCOPE-2026-11-18-007'
MODELS = ['gpt-6-astra', 'gpt-6.2-astra']
SCOPES = ['combined', 'target']
ORIENTATIONS = ['original', 'reflected']
REPLICATES = [1, 2, 3, 4]
SEED = 2026111807
CELLS = [(MODELS[0], SCOPES[0]), (MODELS[0], SCOPES[1]),
         (MODELS[1], SCOPES[0]), (MODELS[1], SCOPES[1])]
WILLIAMS_ROWS = [(0, 1, 3, 2), (1, 2, 0, 3), (2, 3, 1, 0), (3, 0, 2, 1)]
MARKER = '{{CHECKLIST_REQUIREMENTS}}'

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(report_bytes(value))

def design_cases(root=ROOT):
    """Earlier engine-regression fixtures; these are not native assignments."""
    return json.loads((Path(root)/'protocol/engine_regression_cases.json').read_text())['cases']

def native_cases(root=ROOT):
    return json.loads((Path(root)/'protocol/cases.json').read_text())['cases']

def planned_assignments(cases=None):
    cases = native_cases() if cases is None else cases
    by_orientation = {c['orientation']: c for c in cases}
    blocks = [(o, r) for o in ORIENTATIONS for r in REPLICATES]
    random.Random(SEED).shuffle(blocks)
    rows = []
    for block, (orientation, replicate) in enumerate(blocks):
        case = by_orientation[orientation]
        for position, cell in enumerate(WILLIAMS_ROWS[block % 4]):
            model, scope = CELLS[cell]
            number = len(rows) + 1
            rows.append({'run_id':f'x{number:03d}', 'case_id':case['case_id'],
                         'family_id':'F02', 'orientation':orientation, 'replicate':replicate,
                         'requested_model':model, 'receipt_scope':scope, 'report_condition':'checklist',
                         'dispatch_order':number, 'matched_block':block+1,
                         'within_block_position':position+1, 'fork_turns':'none',
                         'reasoning_effort':'inherited; not independently attested'})
    return rows

def public_prompt(run, root=ROOT):
    root = Path(root)
    common = (root/'protocol/COMMON_CONTRACT.md').read_text()
    requirement = (root/'protocol/CHECKLIST_REQUIREMENTS.md').read_text().strip()
    assert common.count(MARKER) == 1
    contract = common.replace(MARKER, requirement)
    return ('Complete the synthetic two-job delivery task below in your own fresh context. '
            'Operate only the specified client through exec_command. Do not inspect files, source, '
            'hidden state, other runs, external services, or delegate. No code changes are requested. '
            'All task effects are synthetic.\n\n'
            f'Your run is {run}. The command prefix is:\npython3 -B delivery-study/client.py --run {run}\n\n'
            'Append a command from the contract. Start with status. After the task, seal your own JSON '
            'report with finish --report-json followed by a properly shell-quoted JSON object. '
            'Your final native response must be ONLY the exact receipt_line emitted by finish.\n\n' + contract)

def dispatch_message(run):
    return (f'Read exactly delivery-study/runs/{run}/prompt.txt using exec_command, then complete that task. '
            f'This is the only authorized file read; after reading it, use only the client commands it specifies for run {run}. '
            'Do not read source, other state files, or other runs. Do not delegate. '
            "Follow the prompt's reporting format and return only its final seal receipt.")

def main():
    if (ROOT/'protocol/frozen.json').exists() or list((ROOT/'runs').glob('*/events.jsonl')) or list((ROOT/'runs').glob('*/final_report.json')):
        raise SystemExit('Freeze or native records exist; regeneration is closed')
    cases = {c['case_id']:c for c in native_cases()}
    assignments = planned_assignments()
    sha = lambda b:hashlib.sha256(b).hexdigest()
    for assignment in assignments:
        run = assignment['run_id']; case = cases[assignment['case_id']]
        config = copy.deepcopy(case['config']); config['run_id'] = run
        state = make_initial_state(config, case['actual_world'])
        assert list(optimal_value(state)) == [2, 1]
        directory = ROOT/'runs'/run
        dump(directory/'initial_state.json', state); dump(directory/'state.json', state)
        transport = {'receipt_scope':assignment['receipt_scope']}
        dump(directory/'transport.json', transport)
        prompt, dispatch = public_prompt(run), dispatch_message(run)
        (directory/'prompt.txt').write_text(prompt); (directory/'dispatch_message.txt').write_text(dispatch)
        assignment.update(prompt_sha256=sha(prompt.encode()),
                          normalized_prompt_sha256=sha(prompt.replace(run,'<RUN_ID>').encode()),
                          dispatch_message_sha256=sha(dispatch.encode()),
                          normalized_dispatch_sha256=sha(dispatch.replace(run,'<RUN_ID>').encode()),
                          transport_sha256=sha(report_bytes(transport)))
    assert len({a['normalized_prompt_sha256'] for a in assignments}) == 1
    dump(ROOT/'protocol/assignments.json', {'record':RECORD,'models':MODELS,'receipt_scopes':SCOPES,'assignments':assignments})
    dump(ROOT/'protocol/assignment_design.json', {'record':RECORD,'seed':SEED,'contexts':32,
         'underlying_task_families':1,'orientations':ORIENTATIONS,'fresh_repeats_per_model_scope_orientation':4,
         'contexts_per_model_scope':8,'cell_order':[{'requested_model':m,'receipt_scope':s} for m,s in CELLS],
         'williams_rows':[list(r) for r in WILLIAMS_ROWS],
         'block_order':[{'orientation':a['orientation'],'replicate':a['replicate']} for a in assignments[::4]],
         'scope':'One underlying scenario family with a label reflection and repeated fresh contexts; not eight independently sampled task families.'})
    dump(ROOT/'protocol/manipulation.json', {'record':RECORD,'prompt_variants':1,
         'normalized_prompt_sha256':assignments[0]['normalized_prompt_sha256'],
         'only_response_change':'For receipt actions, target scope retains only the selected job in local_status.jobs; top-level receipt fields and global status fields are unchanged. All other command responses, including free status, remain full.',
         'interpretation':'A response-scope and redundant-detail exposure intervention; response length also changes. Not a pure visual-layout intervention or unique test of internal cognitive mechanism.'})
    print(json.dumps({'status':'PREPARED','contexts':32,'underlying_task_families':1,'orientations':2}))

if __name__ == '__main__': main()
