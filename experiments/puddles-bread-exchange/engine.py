"""Puddle's Bread Exchange v0.1.0: exact, dependency-free synthetic model.

All uncertainty is authored into this finite generator. No model API is called.
Python 3.10+. The browser counterpart is engine.js.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from itertools import product
from typing import Iterable, Iterator, Sequence

RULES = ("headcount", "receipts", "shared_cause")
TOPOLOGIES = {
    "choir": (10,),
    "loud_minority": (8, 1, 1),
    "two_sources": (5, 5),
    "mixed": (4, 3, 2, 1),
    "five_pairs": (2, 2, 2, 2, 2),
    "ten_roots": (1,) * 10,
}
MARGINAL_ERRORS = (F(1, 10), F(1, 5), F(3, 10))
SHARED_FRACTIONS = (F(0), F(1, 4), F(1, 2), F(3, 4))


def validate_bits(bits: Sequence[int]) -> None:
    if not bits or any(type(b) is not int or b not in (0, 1) for b in bits):
        raise ValueError("A nonempty sequence of integer 0/1 observations is required")


def independent_posterior(successes: int, count: int, error: F) -> F:
    """P(truth=1) for independent symmetric sensors and a fair truth prior."""
    if not (isinstance(count, int) and isinstance(successes, int) and count > 0 and 0 <= successes <= count):
        raise ValueError("Require count > 0 and 0 <= successes <= count")
    error = F(error)
    if not 0 < error < F(1, 2):
        raise ValueError("Error rate must lie strictly between 0 and 1/2")
    l1 = (1-error) ** successes * error ** (count-successes)
    l0 = error ** successes * (1-error) ** (count-successes)
    return l1 / (l1+l0)


def local_error(marginal: F, shared: F) -> F:
    marginal, shared = F(marginal), F(shared)
    if not 0 <= shared < marginal < F(1, 2):
        raise ValueError("Require 0 <= shared fault probability < marginal error < 1/2")
    return (marginal-shared) / (1-2*shared)


def predict(bits: Sequence[int], copies: Sequence[int], marginal: F, shared: F) -> dict[str, F]:
    """Use observations and supplied parameters only; never truth or fault labels."""
    validate_bits(bits)
    if len(bits) != len(copies) or any(type(w) is not int or w <= 0 for w in copies):
        raise ValueError("Each root needs a positive integer multiplicity")
    e = local_error(marginal, shared)
    head = independent_posterior(sum(b*w for b, w in zip(bits, copies)), sum(copies), marginal)
    receipt = independent_posterior(sum(bits), len(bits), marginal)
    conditional = independent_posterior(sum(bits), len(bits), e)
    aware = shared + (1-2*shared) * conditional
    return dict(zip(RULES, (head, receipt, aware)))


def decide(p: F) -> str:
    if not 0 <= p <= 1:
        raise ValueError("Probability must be in [0, 1]")
    if p >= F(9, 10):
        return "buy"
    if p <= F(1, 10):
        return "reject"
    return "hold"


def payoff(action: str, truth: int) -> int:
    if action not in ("buy", "reject", "hold") or truth not in (0, 1):
        raise ValueError("Unknown action or truth")
    if action == "hold":
        return 0
    return 1 if (action == "buy") == bool(truth) else -9


@dataclass(frozen=True)
class Cell:
    topology: str
    marginal: F
    shared_fraction: F

    @property
    def shared(self) -> F:
        return self.marginal*self.shared_fraction

    @property
    def copies(self) -> tuple[int, ...]:
        return TOPOLOGIES[self.topology]

    @property
    def id(self) -> str:
        return f"a{int(100*(1-self.marginal)):02d}-s{int(100*self.shared_fraction):02d}-{self.topology}"


def cells() -> Iterator[Cell]:
    for marginal, alpha, topology in product(MARGINAL_ERRORS, SHARED_FRACTIONS, TOPOLOGIES):
        yield Cell(topology, marginal, alpha)


def histories(cell: Cell) -> Iterator[dict]:
    """Every positive-probability latent history, with exact rational mass."""
    e, q, k = local_error(cell.marginal, cell.shared), cell.shared, len(cell.copies)
    for truth, fault in product((0, 1), (0, 1)):
        fault_mass = q if fault else 1-q
        if not fault_mass:
            continue
        for errors in product((0, 1), repeat=k):
            weight = F(1, 2) * fault_mass * e**sum(errors) * (1-e)**(k-sum(errors))
            bits = tuple(truth ^ fault ^ err for err in errors)
            yield {"truth": truth, "shared_fault": fault, "local_errors": errors, "bits": bits, "weight": weight}


def summarize(cell: Cell, rows: Iterable[dict]) -> dict:
    metrics = {rule: {"brier": F(0), "coverage": F(0), "wrong_mass": F(0), "payoff": F(0)} for rule in RULES}
    total = F(0)
    count = 0
    root_correct = [F(0)] * len(cell.copies)
    cache: dict[tuple, dict[str, F]] = {}
    for row in rows:
        truth, weight, bits = row["truth"], row["weight"], row["bits"]
        total += weight
        count += 1
        for i, bit in enumerate(bits):
            root_correct[i] += weight * (bit == truth)
        if bits not in cache:
            cache[bits] = predict(bits, cell.copies, cell.marginal, cell.shared)
        for rule, p in cache[bits].items():
            action, m = decide(p), metrics[rule]
            m["brier"] += weight*(p-truth)**2
            m["coverage"] += weight*(action != "hold")
            m["wrong_mass"] += weight*(action != "hold" and payoff(action, truth) < 0)
            m["payoff"] += weight*payoff(action, truth)
    if total != 1:
        raise ArithmeticError(f"Cell {cell.id}: probability mass is {total}, not 1")
    if any(x != 1-cell.marginal for x in root_correct):
        raise ArithmeticError(f"Cell {cell.id}: marginal accuracy changed")
    result = {
        "id": cell.id, "topology": cell.topology, "copies": cell.copies,
        "marginal_error": str(cell.marginal), "shared_fraction": str(cell.shared_fraction),
        "shared_fault_probability": str(cell.shared), "local_error": str(local_error(cell.marginal, cell.shared)),
        "histories": count, "mass": str(total), "root_accuracy": str(root_correct[0]),
        "metrics": {},
    }
    for rule, m in metrics.items():
        acc = 1-m["wrong_mass"]/m["coverage"] if m["coverage"] else None
        result["metrics"][rule] = {
            **{key: float(val) for key, val in m.items()},
            "decisive_accuracy": float(acc) if acc is not None else None,
            "exact": {**{key: str(val) for key, val in m.items()}, "decisive_accuracy": str(acc) if acc is not None else None},
        }
    return result
