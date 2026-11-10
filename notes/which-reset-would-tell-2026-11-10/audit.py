"""Which Reset Would Tell? Standard-library, deterministic finite diagnostic audit.

No models, network, credentials, mutable cross-trial memory, or external data.
The dynamics are the unchanged mathematical mechanism of The Shape That Remains
Suite C. A carrier labelled 'learned' is assigned, not trained in this audit.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from pathlib import Path

VALUES = (-1, 0, 1)
PROBES = tuple(range(-8, 9))
INTERVENTIONS = ("none", "clear_context", "clear_world", "clear_learned")
PANELS = tuple(INTERVENTIONS[:i] for i in range(1, 5))
CARRIER_INDEX = {"clear_learned": 0, "clear_context": 1, "clear_world": 2}


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(values: tuple[int, ...]) -> None:
    check(type(values) is tuple and len(values) == 4, "four-carrier tuple required")
    check(all(type(v) is int and v in VALUES for v in values), "invalid carrier")


def step(x: int, values: tuple[int, ...], probe: int) -> int:
    validate(values)
    check(type(x) is int and -4 <= x <= 4, "invalid state")
    check(type(probe) is int and -8 <= probe <= 8, "invalid probe")
    return max(-4, min(4, 2*x + sum(values) + probe))


def observe(x: int) -> int:
    check(type(x) is int and -4 <= x <= 4, "invalid state")
    return 1 if x >= 3 else -1 if x <= -3 else 0


def intervene(values: tuple[int, ...], action: str) -> tuple[int, ...]:
    validate(values)
    check(action in INTERVENTIONS, "unknown intervention")
    clone = list(values)
    if action != "none":
        clone[CARRIER_INDEX[action]] = 0
    return tuple(clone)


def response(values: tuple[int, ...], action: str, probe: int) -> int:
    # Every query is a separate matched branch, not an evolving interview.
    return observe(step(0, intervene(values, action), probe))


def signature(values: tuple[int, ...], panel: tuple[str, ...]) -> tuple[int, ...]:
    return tuple(response(values, action, probe) for action in panel for probe in PROBES)


def analytic_key(values: tuple[int, ...], depth: int) -> tuple[int, ...]:
    # Independent algebraic partition: no transition, observation, or intervention calls.
    l, c, w, p = values
    return ((l+c+w+p,), (c, l+w+p), (c, w, l+p), (l, c, w, p))[depth-1]


def partition(hypotheses: list[tuple[int, ...]], depth: int) -> list[list[list[int]]]:
    groups: dict[tuple[int, ...], list[list[int]]] = {}
    for values in hypotheses:
        groups.setdefault(signature(values, PANELS[depth-1]), []).append(list(values))
    return sorted((sorted(group) for group in groups.values()))


def reference_partition(hypotheses: list[tuple[int, ...]], depth: int) -> list[list[list[int]]]:
    groups: dict[tuple[int, ...], list[list[int]]] = {}
    for values in hypotheses:
        groups.setdefault(analytic_key(values, depth), []).append(list(values))
    return sorted((sorted(group) for group in groups.values()))


def independent_response(values: tuple[int, ...], action: str, probe: int) -> int:
    # At x=0 clipping to +/-4 does not change thresholds +/-3.
    l, c, w, p = values
    if action == "clear_context": c = 0
    elif action == "clear_world": w = 0
    elif action == "clear_learned": l = 0
    elif action != "none": raise ValueError("unknown intervention")
    z = l+c+w+p+probe
    if z < -2: return -1
    if z > 2: return 1
    return 0


def build(reverse: bool = False) -> tuple[list[dict], dict]:
    hypotheses = list(itertools.product(VALUES, repeat=4))
    raw = []
    cases = list(itertools.product(hypotheses, INTERVENTIONS, PROBES))
    for values, action, probe in reversed(cases) if reverse else cases:
        result = response(values, action, probe)
        check(result == independent_response(values, action, probe), "response disagreement")
        raw.append({"carriers": list(values), "intervention": action,
                    "probe": probe, "observation": result})
    raw.sort(key=lambda r: (r["carriers"], r["intervention"], r["probe"]))
    panels = []
    for depth in range(1, 5):
        groups = partition(hypotheses, depth)
        check(groups == reference_partition(hypotheses, depth), "partition disagreement")
        fixed = [v for v in hypotheses if v[3] == 0]
        known = partition(fixed, depth)
        check(known == reference_partition(fixed, depth), "known-prior disagreement")
        panels.append({"interventions": list(PANELS[depth-1]), "classes": len(groups),
                       "largest_class": max(map(len, groups)), "classes_fixed_prior": len(known),
                       "groups": groups})
    zero = [v for v in hypotheses if sum(v) == 0]
    unmask = [{"carriers": list(v), "intervention": a,
               "bias_after_cut": sum(intervene(v, a))}
              for v in zero for a in INTERVENTIONS[1:] if sum(intervene(v, a)) != 0]
    matched = []
    for learned, prior in itertools.product(VALUES, repeat=2):
        exposed, reference = (learned, 0, 0, prior), (0, 0, 0, prior)
        matched.append({"learned": learned, "prior": prior,
                        "different": signature(exposed, PANELS[0]) != signature(reference, PANELS[0])})
    mismatched = []
    for a, b in itertools.permutations(VALUES, 2):
        mismatched.append({"prior_a": a, "prior_b": b,
                           "different_without_learning": signature((0,0,0,a), PANELS[0]) != signature((0,0,0,b), PANELS[0])})
    summary = {"record": "BONDED-RSI-RESET-DIAGNOSTICS-2026-11-10-001",
               "hypotheses": len(hypotheses), "raw_rows": len(raw), "panels": panels,
               "zero_aggregate": {"hypotheses": len(zero),
                                  "with_nonzero_learned": sum(v[0] != 0 for v in zero),
                                  "unmasking_cuts": len(unmask), "total_single_cuts": len(zero)*3},
               "unmasking_witnesses": unmask, "matched_prior_controls": matched,
               "mismatched_prior_controls": mismatched,
               "status": "finite mechanism audit; same-author verification; no live model"}
    return raw, summary


def dumps(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def verify(raw: list[dict], summary: dict) -> None:
    expected_raw, expected_summary = build()
    check(raw == expected_raw, "raw evidence mismatch")
    check(summary == expected_summary, "summary mismatch")


def write(out: Path, reverse: bool = False) -> None:
    check(not out.exists(), "output directory already exists")
    raw, summary = build(reverse)
    out.mkdir(parents=True)
    (out/"observations.jsonl").write_text("".join(json.dumps(r, sort_keys=True)+"\n" for r in raw))
    (out/"summary.json").write_text(dumps(summary))
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
    (out/"hashes.json").write_text(dumps(hashes))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reverse", action="store_true")
    args = parser.parse_args()
    write(args.out, args.reverse)
