"""Goblin Cycle Lab: deterministic synthetic permutation-language networks.

Author: Josh & Rin laboratory; 2026-10-26. Requires Python 3.10+, stdlib only.
All words, dictionaries, identities, and fault events here are synthetic.
The auditor takes only claimed pairwise mappings; semantic ground truth is
accessible to the generator/evaluator only. No frontier-LLM claim is made.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Dict, Tuple, List, Optional

Edge = Tuple[int, int]
MASK = (1 << 32) - 1

class XorShift32:
    def __init__(self, seed: int):
        self.state = (seed & MASK) or 0x6D2B79F5

    def draw(self) -> int:
        v = self.state
        v ^= (v << 13) & MASK
        v ^= v >> 17
        v ^= (v << 5) & MASK
        self.state = v & MASK
        return self.state

    def index(self, length: int) -> int:
        return self.draw() % length

    def shuffled(self, n: int) -> tuple[int, ...]:
        arr = list(range(n))
        for j in range(n-1, 0, -1):
            k = self.index(j + 1)
            arr[j], arr[k] = arr[k], arr[j]
        return tuple(arr)


def inverse(p: tuple[int, ...]) -> tuple[int, ...]:
    q = [None] * len(p)
    for i, x in enumerate(p):
        q[x] = i
    assert all(v is not None for v in q)
    return tuple(q)


def pairmap(cu: tuple[int, ...], cv: tuple[int, ...]) -> tuple[int, ...]:
    """For each symbol in language u, return equivalent symbol in v."""
    inv = inverse(cu)
    return tuple(cv[inv[g]] for g in range(len(cu)))


def edge(u: int, v: int) -> Edge:
    return (min(u, v), max(u, v))


def getmap(graph: dict[Edge, tuple[int, ...]], u: int, v: int) -> tuple[int, ...]:
    if u == v:
        return tuple(range(len(next(iter(graph.values())))))
    val = graph[edge(u, v)]
    return val if u < v else inverse(val)


def compose(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[int, ...]:
    """Apply mapping a then mapping b."""
    return tuple(b[x] for x in a)


def swap_outputs(table: tuple[int, ...], rng: XorShift32) -> tuple[int, ...]:
    size = len(table)
    x = rng.index(size)
    y = rng.index(size-1)
    if y >= x:
        y += 1
    return tuple(y if z == x else x if z == y else z for z in table)


@dataclass(frozen=True)
class Network:
    seed: int
    vocab: int
    mode: str
    count: int
    observed: dict[Edge, tuple[int, ...]]
    actual: dict[Edge, tuple[int, ...]]
    codebooks: tuple[tuple[int, ...], ...]
    edited: tuple[Edge, ...]


def make_network(seed: int, vocab: int=16, mode: str='single') -> Network:
    if vocab < 3:
        raise ValueError('Minimum vocabulary: 3')
    if mode not in ('single','triangle','star','coordinated','double','clean'):
        raise ValueError(mode)
    rng = XorShift32(seed)
    count = 3 if mode == 'triangle' else 4
    books = tuple(rng.shuffled(vocab) for _ in range(count))
    all_edges = tuple(combinations(range(count), 2))
    available = tuple((0,v) for v in range(1,count)) if mode=='star' else all_edges
    actual = {e: pairmap(books[e[0]],books[e[1]]) for e in available}
    obs = actual.copy()
    edited: list[Edge] = []
    if mode in ('single','triangle','star'):
        culprit = available[rng.index(len(available))]
        obs[culprit] = swap_outputs(obs[culprit], rng)
        edited = [culprit]
    elif mode == 'double':
        one = available[rng.index(len(available))]
        rest = tuple(e for e in available if e != one)
        two = rest[rng.index(len(rest))]
        obs[one] = swap_outputs(obs[one], rng)
        obs[two] = swap_outputs(obs[two], rng)
        edited = [one, two]
    elif mode == 'coordinated':
        # A simultaneous relabeling of node B's alphabet on all three incident
        # channels leaves every triangle cycle-consistent. The auditor cannot
        # distinguish it from a different choice of B's hidden codebook.
        symbol_relabel = swap_outputs(tuple(range(vocab)), rng)
        new_b = tuple(symbol_relabel[x] for x in books[1])
        altered = list(books)
        altered[1] = new_b
        obs = {e: pairmap(altered[e[0]], altered[e[1]]) for e in available}
        edited = [e for e in available if 1 in e]
    return Network(seed,vocab,mode,count,obs,actual,books,tuple(edited))


def triangles(net: Network) -> tuple[tuple[tuple[int,int,int], int], ...]:
    """Returns number of differing symbol translations for each present 3-cycle."""
    result = []
    for a,b,c in combinations(range(net.count),3):
        if not (edge(a,b) in net.observed and edge(b,c) in net.observed and edge(a,c) in net.observed):
            continue
        direct = getmap(net.observed,a,c)
        via = compose(getmap(net.observed,a,b),getmap(net.observed,b,c))
        wrong = sum(x!=y for x,y in zip(direct,via))
        result.append(((a,b,c),wrong))
    return tuple(result)


def audit(net: Network) -> dict:
    """Blind auditor: consumes ONLY net.observed and node count.

    A candidate edge must cover all failed triangles. With just one failed
    triangle, multiple candidates remain. In this synthetic full-permutation
    family a single faulty edge in K4 has exactly two bad triangles and a
    unique common edge. Confidence is conditional on the one-fault premise.
    """
    all_cycles = triangles(net)
    failed = [c for c,d in all_cycles if d > 0]
    if not all_cycles:
        return dict(status='unobservable',failed=failed,cycles=all_cycles,candidates=[],repaired=None)
    if not failed:
        return dict(status='consistent_not_verified',failed=failed,cycles=all_cycles,candidates=[],repaired=None)
    candidates = []
    for e in sorted(net.observed):
        if all(e[0] in cycle and e[1] in cycle for cycle in failed):
            candidates.append(e)
    if len(candidates) != 1:
        return dict(status='ambiguous',failed=failed,cycles=all_cycles,candidates=candidates,repaired=None)
    fault = candidates[0]
    # Rebuild from a triangle with a path that avoids the flagged edge.
    alt = []
    for k in range(net.count):
        if k in fault:
            continue
        if edge(fault[0],k) in net.observed and edge(k,fault[1]) in net.observed:
            alt.append(compose(getmap(net.observed,fault[0],k),getmap(net.observed,k,fault[1])))
    if not alt or any(p!=alt[0] for p in alt):
        return dict(status='ambiguous',failed=failed,cycles=all_cycles,candidates=[fault],repaired=None)
    # Test the entire network AFTER the putative repair. This catches many
    # (though not all) multi-fault cases; do not pretend otherwise.
    repaired_graph = dict(net.observed)
    repaired_graph[fault] = alt[0]
    from dataclasses import replace
    checked = triangles(replace(net,observed=repaired_graph))
    if any(delta for _, delta in checked):
        return dict(status='unresolved_multi_fault',failed=failed,cycles=all_cycles,candidates=[fault],repaired=None)
    return dict(status='localized_under_single_fault',failed=failed,cycles=all_cycles,candidates=[fault],repaired=alt[0])


def path_vote_audit(net: Network) -> tuple[Edge,...]:
    """Alternative path-based diagnostic, independent of triangle scoring.

    A link is independently suspicious when >=2 two-hop paths agree with
    each other but disagree with that link's claim. The auditor never reads
    actual or codebooks; it works entirely from observed mappings.
    """
    flagged=[]
    for u,v in sorted(net.observed):
        alternative_paths=[]
        for k in range(net.count):
            if k==u or k==v:
                continue
            if edge(u,k) in net.observed and edge(k,v) in net.observed:
                alternative_paths.append(compose(getmap(net.observed,u,k),getmap(net.observed,k,v)))
        if len(alternative_paths)>=2 and all(p==alternative_paths[0] for p in alternative_paths) and alternative_paths[0]!=net.observed[u,v]:
            flagged.append((u,v))
    return tuple(flagged)


def wrong_links(net: Network) -> tuple[Edge,...]:
    """Oracle ONLY, used by evaluator; MUST NOT be read in audit()."""
    return tuple(e for e in sorted(net.observed) if net.observed[e]!=net.actual[e])


def record(net: Network) -> dict:
    aud=audit(net)
    wrong=wrong_links(net)
    fault=aud['candidates'][0] if aud['status']=='localized_under_single_fault' else None
    correct=fault is not None and fault in wrong and len(wrong)==1 and aud['repaired']==net.actual[fault]
    return dict(seed=net.seed,vocab=net.vocab,mode=net.mode,n=net.count,edge_count=len(net.observed),
                oracle_wrong_links=len(wrong),bad_triangles=len(aud['failed']),checked_triangles=len(aud['cycles']),
                status=aud['status'],reported_edge='-'.join(map(str,fault)) if fault else None,
                exactly_repaired=correct,path_vote_matches=(list(path_vote_audit(net))==([fault] if fault else [])))
