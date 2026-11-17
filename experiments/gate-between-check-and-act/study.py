#!/usr/bin/env python3
"""The Gate Between Check and Act. Standard-library finite-model laboratory.
No model API, network, credentials, private state, or Castle dependency.
"""
from __future__ import annotations
import argparse, csv, gzip, hashlib, itertools, json
from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path
from fractions import Fraction
from typing import Callable

ACTIONS = ('raw', 'guard', 'main', 'inspect', 'wait', 'stop')
POLICIES = ('always_main', 'trust_initial', 'inspect_once', 'inspect_twice',
            'inspect_guard', 'atomic_once', 'atomic_refresh', 'belief_raw', 'belief_guard')

@dataclass(frozen=True)
class Config:
    horizon: int = 8
    main_duration: int = 4
    lag: int = 0
    changes: int = 8
    interface: str = 'guard'
    def __post_init__(self):
        if not (1 <= self.horizon <= 12 and 1 <= self.main_duration <= 12
                and 0 <= self.lag <= self.horizon and 0 <= self.changes <= self.horizon
                and self.interface in ('raw', 'guard')):
            raise ValueError('invalid finite-model configuration')

@dataclass(frozen=True)
class World:
    permission: tuple[int, ...]
    revision: tuple[int, ...]
    @property
    def name(self): return ''.join(map(str, self.permission[1:]))

def worlds(c: Config) -> tuple[World, ...]:
    out = []
    for bits in itertools.product((0, 1), repeat=c.horizon):
        p = (1,) + bits
        r = [0]
        for a, b in zip(p, p[1:]): r.append(r[-1] + int(a != b))
        if r[-1] <= c.changes: out.append(World(p, tuple(r)))
    return tuple(out)

def snapshot(w: World, t: int, lag: int) -> tuple[int, int, int]:
    s = max(0, t-lag)
    return (s, w.permission[s], w.revision[s])

def canonical(x) -> bytes:
    return (json.dumps(x, sort_keys=True, separators=(',', ':'))+'\n').encode()

class Solver:
    """Exact observation-based synthesis, not a clairvoyant per-world oracle.
    State: time, set of histories consistent with observations, last valid token.
    It sees the public model and information set, never the realized world ID.
    """
    def __init__(self, c: Config, reverse: bool = False):
        self.c = c
        self.ws = tuple(reversed(worlds(c))) if reverse else worlds(c)
        self.full = (1 << len(self.ws))-1
        self.valid = [0]*(c.horizon+1)
        self.epochs = [{} for _ in self.valid]
        self.reads = [{} for _ in self.valid]
        for i, w in enumerate(self.ws):
            bit = 1 << i
            for t in range(1, c.horizon+1):
                if w.permission[t]:
                    self.valid[t] |= bit
                    self.epochs[t][w.revision[t]] = self.epochs[t].get(w.revision[t], 0) | bit
                o = snapshot(w, t, c.lag)
                self.reads[t][o] = self.reads[t].get(o, 0) | bit
        self.best = lru_cache(None)(self._best)

    def _best(self, t: int, b: int, token: int) -> tuple[int, int, str]:
        n = b.bit_count(); H = self.c.horizon
        if n == 0: return (0, 0, 'stop')
        if t > H: return (0, n*(H+1), 'stop')
        candidates = []
        # Lower total terminal tick is better; failures cost H+1, not zero.
        if b & ~self.valid[t] == 0: candidates.append((n, n*t, 'raw'))
        if self.c.interface == 'guard':
            admitted = b & self.epochs[t].get(token, 0)
            rejected = b & ~admitted
            v = self.best(t+1, rejected, token)
            candidates.append((admitted.bit_count()+v[0], admitted.bit_count()*t+v[1], 'guard'))
        finish = t+self.c.main_duration-1
        if finish <= H: candidates.append((n, n*finish, 'main'))
        sv = st = 0
        for o, mask in sorted(self.reads[t].items()):
            subset = b & mask
            if subset:
                v = self.best(t+1, subset, o[2] if o[1] else token)
                sv += v[0]; st += v[1]
        candidates.append((sv, st, 'inspect'))
        v = self.best(t+1, b, token)
        candidates.extend([(v[0], v[1], 'wait'), (0, n*(H+1), 'stop')])
        return min(candidates, key=lambda v: (-v[0], v[1], ACTIONS.index(v[2])))

    def answer(self):
        n, total, action = self.best(1, self.full, 0)
        return dict(worlds=len(self.ws), completions=n, terminal_tick_sum=total,
                    mean_terminal_tick=str(Fraction(total, len(self.ws))), first_action=action,
                    solved_information_states=self.best.cache_info().currsize)

    def act(self, packet: dict) -> str:
        # Reconstruct the belief from delivered observations only.
        b = self.full; token = 0
        for e in packet['history']:
            t = e['tick']; a = e['action']
            if a == 'inspect':
                o = tuple(e['response']['snapshot'])
                b &= self.reads[t][o]
                if o[1]: token = o[2]
            elif a == 'guard' and e['response']['status'] == 'conflict':
                b &= ~self.epochs[t].get(e['token'], 0)
            elif a == 'raw' and e['response']['status'] == 'blocked':
                b &= ~self.valid[t]
        if not b: raise ValueError('delivered history inconsistent with public model')
        return self.best(packet['tick'], b, token)[2]


def script(name: str, packet: dict) -> str:
    h = packet['history']
    if name == 'always_main': return 'main'
    if not h:
        return {'trust_initial':'raw', 'inspect_once':'inspect', 'inspect_twice':'inspect',
                'inspect_guard':'inspect', 'atomic_once':'guard', 'atomic_refresh':'guard'}[name]
    if name == 'inspect_twice' and len(h) == 1: return 'inspect'
    if name == 'inspect_guard' and h[-1]['action'] == 'inspect':
        return 'guard' if h[-1]['response']['snapshot'][1] else 'main'
    if name in ('inspect_once','inspect_twice') and h[-1]['action'] == 'inspect':
        return 'raw' if h[-1]['response']['snapshot'][1] else 'main'
    if name == 'atomic_refresh':
        if len(h) == 1: return 'inspect'
        if len(h) == 2 and h[-1]['response']['snapshot'][1]: return 'guard'
    return 'main'


def simulate(c: Config, w: World, policy: str, mode: str = 'block',
             actor: Callable[[dict],str] | None = None) -> dict:
    if mode not in ('block','observe'): raise ValueError('invalid enforcement')
    if len(w.permission) != c.horizon+1: raise ValueError('world length')
    t = 1; token = 0; h = []; events = []; entered = legitimate = False
    forbidden = effects = conflicts = 0; terminal = c.horizon+1
    while t <= c.horizon:
        packet = dict(tick=t, horizon=c.horizon, main_duration=c.main_duration,
                      lag=c.lag, changes=c.changes, interface=c.interface,
                      token=token, initial_receipt=[0,1,0], history=h)
        # Copy prevents a callback from editing the environment's retained history.
        action = actor(json.loads(json.dumps(packet))) if actor else script(policy, packet)
        if action not in ACTIONS or (action == 'guard' and c.interface != 'guard'):
            raise ValueError('action outside declared interface')
        allowed = bool(w.permission[t]); rev = w.revision[t]
        forbidden_here = action == 'raw' and not allowed
        effect = 'none'; status = 'continue'; next_token = token
        response = {}
        if action == 'inspect':
            o = snapshot(w, t, c.lag); response = dict(snapshot=list(o),status='receipt')
            if o[1]: next_token = o[2]
        elif action == 'raw':
            forbidden += int(forbidden_here)
            if allowed or mode == 'observe':
                effect='side'; entered=True; legitimate=allowed
                effects += int(not allowed); status='entered'; terminal=t
            else: status='blocked'
        elif action == 'guard':
            if allowed and rev == token:
                effect='side'; entered=legitimate=True; status='entered'; terminal=t
            else: status='conflict'; conflicts+=1
        elif action == 'main':
            finish=t+c.main_duration-1
            if finish <= c.horizon:
                effect='main'; entered=legitimate=True; status='entered'; terminal=finish
            else: status='deadline'
        elif action == 'stop': status='stopped'
        if not response: response=dict(status=status)
        events.append(dict(tick=t,action=action,token=token,public_before=packet,
                           response=response,truth=dict(permission=int(allowed),revision=rev),
                           effect=effect,forbidden_raw_request=bool(forbidden_here)))
        h = h+[dict(tick=t,action=action,token=token,response=response)]
        token=next_token
        if entered or status in ('deadline','stopped'): break
        t+=1
    return dict(schedule=w.name,lag=c.lag,policy=policy,enforcement=mode,
                entered=entered,legitimate_completion=legitimate,
                forbidden_raw_requests=forbidden,unauthorized_effects=effects,
                conditional_conflicts=conflicts,terminal_tick=terminal,events=events)


def primary(reverse=False):
    summaries=[]; episodes=[]
    for lag in range(3):
        c=Config(lag=lag)
        solvers={i:Solver(Config(lag=lag,interface=i)) for i in ('raw','guard')}
        ws=worlds(c)
        for mode in ('block','observe'):
            for policy in POLICIES:
                cb=solvers[policy[7:]].act if policy.startswith('belief_') else None
                rows=[simulate(c,w,policy,mode,cb) for w in (reversed(ws) if reverse else ws)]
                episodes.extend(rows)
                summaries.append(dict(lag=lag,enforcement=mode,policy=policy,episodes=len(rows),
                    legitimate=sum(r['legitimate_completion'] for r in rows),
                    entered=sum(r['entered'] for r in rows),
                    forbidden_requests=sum(r['forbidden_raw_requests'] for r in rows),
                    unauthorized_effects=sum(r['unauthorized_effects'] for r in rows),
                    conditional_conflicts=sum(r['conditional_conflicts'] for r in rows),
                    terminal_tick_sum=sum(r['terminal_tick'] for r in rows)))
    episodes.sort(key=lambda r:(r['lag'],r['enforcement'],r['policy'],r['schedule']))
    summaries.sort(key=lambda r:(r['lag'],r['enforcement'],r['policy']))
    return summaries,episodes


def grid(reverse=False):
    rows=[]
    for H,K,L in itertools.product(range(2,11),range(2,7),range(3)):
        for B in sorted({0,1,2,H}):
            for interface in ('raw','guard'):
                c=Config(H,K,L,B,interface); s=Solver(c,reverse)
                rows.append(asdict(c)|s.answer())
    return rows


def write_results(out: Path):
    out.mkdir(parents=True,exist_ok=True)
    summary,eps=primary(); frontier=grid()
    (out/'summary.json').write_bytes(canonical(dict(primary=summary,synthesis=frontier,
        primary_episodes=len(eps),synthesis_panels=len(frontier),
        note='Exhaustive authored schedules, not sampled agent trials. Equal-weight design measure.')))
    with (out/'frontier.csv').open('w',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=list(frontier[0]));wr.writeheader();wr.writerows(frontier)
    # Store all event-level traces, deterministic gzip without a timestamp.
    raw=b''.join(canonical(r) for r in eps)
    (out/'traces.jsonl.gz').write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
    selected=[]
    for name,lag,mode,policy in [('10000000',0,'block','inspect_once'),
          ('10000000',0,'observe','inspect_once'),('00000000',0,'block','atomic_once'),
          ('01111111',0,'block','atomic_refresh'),('11111111',0,'block','belief_raw')]:
        selected.append(next(r for r in eps if (r['schedule'],r['lag'],r['enforcement'],r['policy'])==(name,lag,mode,policy)))
    (out/'witnesses.json').write_bytes(canonical(selected))
    return dict(episodes=len(eps),panels=len(frontier),
                outputs={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                         for p in sorted(out.iterdir()) if p.is_file()})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='results');args=ap.parse_args()
    print(json.dumps(write_results(Path(args.out)),indent=2,sort_keys=True))
