#!/usr/bin/env python3
"""The Porch That Ate Halloween: exhaustive standard-library finite checker.

No network, external model, or stochastic training is involved.
Run: python experiments/halloween-porches/verify.py
"""
VALUE = (8, 6, 5, 4, 3, 2)
CAPACITY = (1, 1, 2, 2, 3, 1)
GOBLINS = 10

def compositions(n, places):
    if places == 1:
        yield (n,)
        return
    for first in range(n + 1):
        for rest in compositions(n - first, places - 1):
            yield (first,) + rest

def total(counts, unlimited=False):
    capacities = (GOBLINS,) * len(CAPACITY) if unlimited else CAPACITY
    return sum(v * min(c, cap) for v, c, cap in zip(VALUE, counts, capacities))

def personal_value(counts, porch, unlimited=False):
    capacities = (GOBLINS,) * len(CAPACITY) if unlimited else CAPACITY
    n = counts[porch]
    if n == 0:
        raise ValueError("Personal payoff requires an occupied porch.")
    return VALUE[porch] * min(1.0, capacities[porch] / n)

def is_personal_equilibrium(counts):
    """No occupied goblin improves expected candy by moving alone."""
    for i, population in enumerate(counts):
        if not population:
            continue
        before = personal_value(counts, i)
        for j in range(len(VALUE)):
            if i == j:
                continue
            after = VALUE[j] * min(1.0, CAPACITY[j] / (counts[j] + 1))
            if after > before + 1e-10:
                return False
    return True

def main():
    allocations = tuple(compositions(GOBLINS, len(VALUE)))
    assert len(allocations) == 3003
    optimum = max(total(a) for a in allocations)
    optimal_allocations = [a for a in allocations if total(a) == optimum]
    equilibria = [(total(a), a) for a in allocations if is_personal_equilibrium(a)]
    expected = [
        (35, (2, 2, 3, 2, 1, 0)),
        (38, (2, 1, 3, 2, 2, 0)),
    ]
    assert optimum == 43
    assert optimal_allocations == [(1, 1, 2, 2, 3, 1)]
    assert sorted(equilibria) == expected

    all_to_richest = (10, 0, 0, 0, 0, 0)
    assert total(all_to_richest) == 8
    assert total(all_to_richest, unlimited=True) == 80
    assert max(total(a, unlimited=True) for a in allocations) == 80

    roles = (0, 1, 2, 2, 3, 3, 4, 4, 4, 5)
    role_counts = tuple(roles.count(i) for i in range(len(VALUE)))
    assert role_counts == optimal_allocations[0]
    payoffs = [personal_value(role_counts, porch) for porch in roles]
    assert payoffs == [8, 6, 5, 5, 4, 4, 3, 3, 3, 2]
    assert sum(payoffs) == 43

    # A ten-night cyclic rotation makes every identity take each role once.
    rotating_means = [
        sum(payoffs[(identity + night) % GOBLINS] for night in range(GOBLINS))
        / GOBLINS
        for identity in range(GOBLINS)
    ]
    assert rotating_means == [4.3] * GOBLINS

    print("PASS: 3,003 visitor-count allocations enumerated")
    print("PASS: unique total-candy optimum 43 at (1, 1, 2, 2, 3, 1)")
    print("PASS: exactly two personal-payoff equilibria:")
    for candy, counts in sorted(equilibria):
        print(f"   {candy} candy at {counts}")
    print("PASS: all chase richest -> 8 limited / 80 unlimited")
    print("PASS: 10-role rotation -> equal expected 4.3 candy per identity")
    print("Scope: finite model only; does not reproduce reported learning means")

if __name__ == "__main__":
    main()
