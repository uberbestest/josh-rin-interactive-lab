"""Exact finite reset audit, corrected full-record decoder and calibration control.

Standard library; no network, credentials, live models or operational changes.
The earlier any-change decoder is retained as a named lossy comparator, not as
an analyst that checks every attempted reset against a perfect-actuation model.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path

VALUES = (-1, 0, 1)
WORLDS = tuple(product(VALUES, repeat=4))
PROBES = tuple(range(-8, 9))
QS = tuple(map(F, ("0", "1/4", "1/2", "3/4", "1")))
REPEATS = (1, 2, 4, 8)
LABELS = ("L", "C", "W", "P")
CALIBRATION = ((1, 0, -1, 0), (0, 1, 0, -1))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_world(v):
    require(type(v) is tuple and len(v) == 4, "four-carrier tuple required")
    require(all(type(x) is int and x in VALUES for x in v), "invalid carrier")


def response(v, cut, probe):
    validate_world(v)
    require(cut is None or type(cut) is int and 0 <= cut < 4, "invalid target")
    require(type(probe) is int and probe in PROBES, "invalid probe")
    fields = list(v)
    if cut is not None:
        fields[cut] = 0
    state = max(-4, min(4, sum(fields) + probe))
    return (state >= 3) - (state <= -3)


def scan(v, cut=None):
    return tuple(response(v, cut, p) for p in PROBES)


def parent_partitions():
    result = []
    for cuts in ((None,), (None, 1), (None, 1, 2), (None, 1, 2, 0)):
        groups = defaultdict(list)
        for v in WORLDS:
            groups[tuple(scan(v, c) for c in cuts)].append(v)
        result.append({"classes": len(groups), "largest": max(map(len, groups.values()))})
    return result


def validate_design(q, m, dependence):
    require(isinstance(q, F) and 0 <= q <= 1, "q must be a Fraction in [0,1]")
    require(type(m) is int and m >= 1, "positive integer repeats required")
    require(dependence in ("independent", "persistent"), "invalid dependence")


def profiles(v, q, m, dependence="independent"):
    """Per-field distinct observed changes; order omitted, mixed outcomes retained.

    With a known q, each mixed sequence's ordering/count contributes a factor
    common to its surviving candidates. Its aggregation preserves the posterior
    ranking and Bayes success. Unlike any-change compression, it also retains
    whether a field's individual attempts contradict perfect actuation.
    """
    validate_world(v)
    validate_design(q, m, dependence)
    fail = (1-q)**m if dependence == "independent" else 1-q
    success = q**m if dependence == "independent" else q
    mixed = 1-fail-success
    choices = []
    for value in v[:3]:
        options = [((0,), F(1))] if value == 0 else [
            ((0,), fail), ((value,), success), (tuple(sorted((0, value))), mixed)]
        choices.append([(x, p) for x, p in options if p])
    for items in product(*choices):
        yield (sum(v), tuple(x for x, _ in items)), items[0][1]*items[1][1]*items[2][1]


def decode(obs, strict):
    total, fields = obs
    if strict and any(len(x) != 1 for x in fields):
        return None
    found = tuple(next((v for v in x if v), 0) for x in fields)
    prior = total-sum(found)
    return found+(prior,) if prior in VALUES else None


def outcome(truth, inferred):
    return "inconsistent" if inferred is None else "correct" if truth == inferred else "wrong"


def aggregate(joint, infer):
    rates = {k: F(0) for k in ("correct", "wrong", "inconsistent")}
    for obs, hypotheses in joint.items():
        prediction = infer(obs)
        for truth, weight in hypotheses.items():
            rates[outcome(truth, prediction)] += weight/81
    require(sum(rates.values()) == 1, "outcome mass does not normalize")
    return {k: str(v) for k, v in rates.items()}


def metrics(q, m, dependence="independent", reverse=False):
    validate_design(q, m, dependence)
    joint = defaultdict(lambda: defaultdict(F))
    for v in reversed(WORLDS) if reverse else WORLDS:
        dist = list(profiles(v, q, m, dependence))
        require(sum(p for _, p in dist) == 1, "conditional mass does not normalize")
        for obs, weight in dist:
            joint[obs][v] += weight
    bayes = sum(max(row.values()) for row in joint.values())/81
    return {"q": str(q), "repeats": m, "dependence": dependence,
            "bayes_accuracy": str(bayes),
            "any_change": aggregate(joint, lambda o: decode(o, False)),
            "strict_full_record": aggregate(joint, lambda o: decode(o, True))}


def raw_reference(q, m, reverse=False, keep_events=False):
    """Alternative ordered-event calculation, without calling profiles/decode.

    Every latent outcome bit is enumerated, including invisible successes when
    a field is already zero. Full ordered post-cut totals are the observations.
    Perfect-model consistency is checked against all 81 nominal signatures.
    """
    validate_design(q, m, "independent")
    require(m <= 3, "bounded raw-event reference supports at most three repeats")
    nominal = {(sum(v), tuple((sum(v)-v[i],)*m for i in range(3))): v for v in WORLDS}
    joint = defaultdict(lambda: defaultdict(F))
    events = []
    worlds = tuple(reversed(WORLDS)) if reverse else WORLDS
    bit_patterns = tuple(product((0, 1), repeat=3*m))
    if reverse:
        bit_patterns = tuple(reversed(bit_patterns))
    for v in worlds:
        for bits in bit_patterns:
            weight = q**sum(bits)*(1-q)**(len(bits)-sum(bits))
            if not weight:
                continue
            total = sum(v)
            readings = tuple(tuple(total-v[i]*bits[i*m+j] for j in range(m)) for i in range(3))
            obs = (total, readings)
            joint[obs][v] += weight
            if keep_events:
                found = tuple(next((total-s for s in xs if s != total), 0) for xs in readings)
                p = total-sum(found)
                lossy = found+(p,) if p in VALUES else None
                events.append({"truth": list(v), "success_bits": list(bits),
                               "baseline_total": total, "post_cut_totals": readings,
                               "joint_probability": str(weight/81),
                               "strict": outcome(v, nominal.get(obs)),
                               "any_change": outcome(v, lossy)})
    def lossy_decode(obs):
        t, xs = obs
        found = tuple(next((t-s for s in x if s != t), 0) for x in xs)
        p = t-sum(found)
        return found+(p,) if p in VALUES else None
    result = {"q": str(q), "repeats": m, "dependence": "independent",
              "bayes_accuracy": str(sum(max(x.values()) for x in joint.values())/81),
              "any_change": aggregate(joint, lossy_decode),
              "strict_full_record": aggregate(joint, nominal.get)}
    events.sort(key=lambda r: (r["truth"], r["success_bits"]))
    return result, events


def miswire(reverse=False):
    rows = []
    for v in reversed(WORLDS) if reverse else WORLDS:
        l, c, w, p = v
        inferred = (p, c, w, l)
        actual = tuple(scan(v, target) for target in (None, 1, 2, 3))
        nominal = tuple(scan(inferred, target) for target in (None, 1, 2, 0))
        require(actual == nominal, "miswire alias failed")
        rows.append({"truth": list(v), "inferred": list(inferred), "wrong": inferred != v,
                     "known_P0": p == 0, "known_P0_rejects": p == 0 and l != 0})
    return sorted(rows, key=lambda r: r["truth"])


def calibration():
    """Two trusted prepared states identify five stable deterministic candidates.

    This grants new source-control access, not an output-only cure. It cannot
    authenticate the preparation or prove future actuator behavior is stable.
    """
    targets = (None, 0, 1, 2, 3)
    # Complete scans identify a total uniquely. This table uses a separately
    # written threshold expression rather than response's clipped recurrence.
    lookup = {tuple(-1 if t+p < -2 else 1 if t+p > 2 else 0 for p in PROBES): t
              for t in range(-4, 5)}
    require(len(lookup) == 9, "total lookup not injective")
    rows = []
    for target in targets:
        readings = [{"prepared": list(v), "baseline": list(scan(v)),
                     "after": list(scan(v, target))} for v in CALIBRATION]
        drops = [lookup[tuple(x["baseline"])]-lookup[tuple(x["after"])] for x in readings]
        rows.append({"actual_target": "none" if target is None else LABELS[target],
                     "observed_drops": drops, "readings": readings})
    require(len({tuple(r["observed_drops"]) for r in rows}) == 5, "calibration collision")
    return {"prepared_states": [list(v) for v in CALIBRATION], "candidates": rows,
            "single_preparation_max_outcomes": max(len({0, *v}) for v in WORLDS),
            "limits": "Trusted preparation and same fixed deterministic actuator; no authentication or live reset proof."}


def build(reverse=False):
    conditions = [metrics(q, m, dep, reverse) for dep in ("independent", "persistent")
                  for q in QS for m in REPEATS]
    checks = [(q, m) for q in QS for m in (1, 2)] + [(F(1, 2), 3)]
    for q, m in checks:
        expected, _ = raw_reference(q, m, reverse)
        require(metrics(q, m, reverse=reverse) == expected, "ordered-event reference disagreement")
    _, events = raw_reference(F(1, 2), 2, reverse, True)
    wiring = miswire(reverse)
    summary = {"record": "BONDED-RSI-RESET-RELIABILITY-2026-11-11-001",
               "version": "v0.1.1-public", "status": "exact synthetic; same-author; no live models",
               "parent_partitions": parent_partitions(), "conditions": conditions,
               "raw_reference_conditions": len(checks), "headline_latent_events": len(events),
               "miswire": {"total": len(wiring), "wrong": sum(r["wrong"] for r in wiring),
                           "known_P0": sum(r["known_P0"] for r in wiring),
                           "known_P0_rejects": sum(r["known_P0_rejects"] for r in wiring)}}
    return {"results.json": summary, "miswire.jsonl": wiring,
            "raw_half_two.jsonl": events, "calibration.json": calibration()}


def encoded(outputs):
    return {name: ("".join(json.dumps(r, sort_keys=True)+"\n" for r in obj) if name.endswith(".jsonl")
                   else json.dumps(obj, sort_keys=True, indent=2)+"\n").encode("utf-8")
            for name, obj in outputs.items()}


def write(out, reverse=False):
    require(not out.exists(), "output directory must not already exist")
    data = encoded(build(reverse))
    out.mkdir(parents=True)
    for name, body in data.items():
        (out/name).write_bytes(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reverse", action="store_true")
    args = parser.parse_args()
    write(args.out, args.reverse)
