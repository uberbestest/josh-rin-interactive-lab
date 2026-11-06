"""The Other Road: dependency-free, deterministic synthetic bandit experiment.
Run: python study.py --out data
Nothing calls a model, network, account, or external service.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import io
import itertools
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACTIONS = ('direct', 'alternate', 'honest_partial', 'silent_partial', 'stop')
ITEMS = (4, 4, 2, 2, 0)

def expected(p: float, loss: float, alternate: bool, audit: float,
             alternate_cost: float = 3.0) -> dict[int, float]:
    """Transparent *supplied* scoring rule; not a theory of human/LLM utility."""
    values = {0: 9.0 - p * loss, 2: 4.5, 3: 8.5 - 8.0 * audit, 4: 0.0}
    if alternate:
        values[1] = 10.0 - alternate_cost
    return values

def best(values: dict[int, float]) -> int:
    return max(sorted(values), key=lambda action: values[action])

def reward(action: int, checkpoint: bool, audited: bool, loss: float) -> float:
    if action == 0:
        return 9.0 - loss * checkpoint
    if action == 1:
        return 7.0
    if action == 2:
        return 4.5
    if action == 3:
        return 0.5 if audited else 8.5
    if action == 4:
        return 0.0
    raise ValueError('unknown action')

def gzopen(path: Path):
    """No timestamp or filename in the gzip header: byte-reproducible."""
    return gzip.GzipFile(filename='', mode='wb', fileobj=path.open('wb'), mtime=0)

def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def run(out: Path) -> dict:
    protocol = json.loads((HERE / 'protocol.json').read_text(encoding='utf-8'))
    out.mkdir(parents=True, exist_ok=True)
    conditions = []
    for p, loss, alternate, audit in itertools.product(
        protocol['checkpoint_probabilities'], protocol['checkpoint_costs'],
        protocol['alternate_available'], protocol['audit_probabilities']):
        conditions.append(dict(cell=f'C{len(conditions):02d}', p=p, loss=loss,
                               alternate=int(alternate), audit=audit))
    write_csv(out / 'conditions.csv', conditions)
    rows, snapshots, summaries = [], [], []
    tape = gzopen(out / 'training-tape.bin.gz')
    for cell in conditions:
        p, loss, alternate, audit = (cell[k] for k in ('p', 'loss', 'alternate', 'audit'))
        values = expected(p, loss, bool(alternate), audit)
        available = sorted(values)
        cell_rows = []
        for seed in range(protocol['seeds']):
            rng = random.Random(seed)
            sums = {a: 0.0 for a in available}
            counts = {a: 0 for a in available}
            event_bytes = bytearray()
            for turn in range(protocol['training_rounds']):
                explore, pick, fault, review = (rng.random() for _ in range(4))
                q = {a: sums[a] / counts[a] if counts[a] else 0.0 for a in available}
                if turn < len(available):
                    action = available[turn]
                elif explore < protocol['exploration_probability']:
                    action = available[min(int(pick * len(available)), len(available) - 1)]
                else:
                    action = best(q)
                checkpoint = action == 0 and fault < p
                audited = action == 3 and review < audit
                sums[action] += reward(action, checkpoint, audited, loss)
                counts[action] += 1
                event_bytes.append(action | (int(checkpoint) << 3) | (int(audited) << 4))
                if (turn + 1) % protocol['checkpoint_interval'] == 0:
                    q = {a: sums[a] / counts[a] for a in available}
                    snapshots.append(dict(cell=cell['cell'], seed=seed, turn=turn + 1,
                                          greedy=ACTIONS[best(q)],
                                          **{f'q_{ACTIONS[a]}': f'{q[a]:.9f}' for a in available}))
            tape.write(event_bytes)
            q = {a: sums[a] / counts[a] for a in available}
            action = best(q)
            row = dict(cell=cell['cell'], seed=seed, action=ACTIONS[action],
                       items=ITEMS[action], omission_disclosed=int(action in (2, 4)),
                       silent_undercompletion=int(action == 3),
                       expected_utility=f'{values[action]:.9f}',
                       expected_regret=f'{max(values.values()) - values[action]:.9f}',
                       **{f'q_{name}': f'{q[i]:.9f}' if i in q else '' for i, name in enumerate(ACTIONS)},
                       **{f'n_{name}': counts.get(i, 0) for i, name in enumerate(ACTIONS)})
            rows.append(row)
            cell_rows.append(row)
        summaries.append(dict(**cell, n=protocol['seeds'],
                              choices={a: sum(r['action'] == a for r in cell_rows) for a in ACTIONS},
                              full=sum(r['items'] == 4 for r in cell_rows),
                              silent=sum(r['silent_undercompletion'] for r in cell_rows),
                              honest_partial=sum(r['action'] == 'honest_partial' for r in cell_rows),
                              nonoptimal=sum(float(r['expected_regret']) > 1e-8 for r in cell_rows),
                              mean_regret=round(sum(float(r['expected_regret']) for r in cell_rows) / len(cell_rows), 9),
                              optimum=ACTIONS[best(values)],
                              expected_values={ACTIONS[a]: v for a, v in values.items()}))
    tape.close()
    write_csv(out / 'runs.csv', rows)
    fields = ['cell', 'seed', 'turn', 'greedy'] + [f'q_{a}' for a in ACTIONS]
    with (out / 'learning-checkpoints.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(snapshots)
    grid_count = 0
    with gzopen(out / 'exact-grid.csv.gz') as zipped:
        with io.TextIOWrapper(zipped, encoding='utf-8', newline='') as text:
            writer = csv.writer(text)
            writer.writerow(['p', 'loss', 'alternate', 'audit', 'alternate_cost', 'optimal_actions'])
            for ip, loss, alternate, ia, altcost in itertools.product(
                range(101), [0.0, 4.0, 12.0], [False, True], range(21), [2.0, 3.0, 6.0]):
                vals = expected(ip / 100, loss, alternate, ia / 20, altcost)
                tied = '|'.join(ACTIONS[a] for a in sorted(vals) if abs(vals[a] - max(vals.values())) < 1e-9)
                writer.writerow([ip / 100, loss, int(alternate), ia / 20, altcost, tied])
                grid_count += 1
    result = dict(study_id=protocol['study_id'], version=protocol['version'],
                  status=protocol['status'], language_model_participants=0,
                  training_runs=len(rows), training_decisions=len(rows) * protocol['training_rounds'],
                  cells=len(conditions), seeds_per_cell=protocol['seeds'], exact_cells=grid_count,
                  cells_summary=summaries)
    (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    (out / 'results.js').write_text('window.OTHER_ROAD_RESULTS = ' + json.dumps(result, separators=(',', ':')) + ';\n', encoding='utf-8')
    files = sorted(p for p in out.iterdir() if p.is_file() and p.name != 'SHA256SUMS.txt')
    (out / 'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n' for p in files), encoding='utf-8')
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE / 'data')
    args = parser.parse_args()
    result = run(args.out)
    print(json.dumps({k: v for k, v in result.items() if k != 'cells_summary'}, indent=2))
    for c in result['cells_summary']:
        if c['p'] == .5:
            print(c['cell'], {k: c[k] for k in ('loss', 'alternate', 'audit', 'choices', 'nonoptimal')})
