# The Check That Arrived Too Early

**Josh & Rin's Lab · Bonded RSI round two · November 16, 2026 (US Eastern) · v1.0.0**  
Record: `BONDED-RSI-CHECK-USE-GAP-2026-11-16-002`  
**Executed finite-game policy synthesis. Zero live models. Same-author verification; external independent review pending.**

[Operate the instrument](index.html) · [Readable methods](method.html) · [Complete source and evidence](evidence.zip) · [Every result cell](results/frontier.csv) · [Verification receipt](verification.json)

## Abstract

A permission-sensitive agent can receive an authentic, current authorization snapshot and still lack a safe unconditional action at the next decision boundary. We study the resulting **interface-dependent safety–progress ceiling**, rather than treating a low completion rate as direct evidence of weak reasoning or unwillingness to help.

We solve a finite, partially observed permission-continuation game exactly across **1,056 parameter cells**. One optimizer is supplied with three different action interfaces: read-then-act snapshots, atomic comparison against an inspected authorization version, and atomic conditional execution under current authority. All policies must make zero forbidden unconditional requests on every compatible authority history. Among those safe policies, the optimizer maximizes the number of histories completed, then minimizes total elapsed ticks.

In a representative four-tick case with at most two authority changes and a six-tick ordinary route, the best snapshot policy completes **3 of 10 physically feasible histories**, the version-bound interface completes **9**, and the current-authority atomic interface completes **all 10**. The eleventh history has no feasible authorized route before the deadline. These are exact optima for the declared model, not hand-picked weak policies or estimated model failure rates.

The evidence package includes all **55,272 schedule–policy replays**, certificates covering **1,587,332 belief states** and **3,328,347 admissible action alternatives**, a standalone proof checker, a JavaScript implementation, and explicit tiny-horizon policy-tree enumeration. The contribution is an executable evaluation instrument and quantified counterexample; we do **not** claim to have invented check/use races, belief-state planning, or runtime shielding.

## 1. What changed from round one

The retained predecessor, *Keep the Destination, Revise the Route*, distinguished forbidden attempts from blocked effects and eventual legitimate completion in 224 authored scripted episodes. Its source is retained under `baseline/`. Its original result hash reproduces exactly, and its 16 named tests pass. The historical `NOT PUBLISHED` label in its original README describes its status at creation; the supplied evidence bundle includes that retained baseline.

Round one explicitly did **not** establish that inspected permission remains current or that permission can change during action execution. Its ordinary route also remained feasible without a finite deadline. Round two changes these assumptions openly:

* Permission may change between a genuine observation and the next consequential action.
* A publicly declared finite deadline can make the ordinary route too slow, although it remains authorized.
* Policies are synthesized for the whole observation-consistent history set, not chosen as seven manually written examples.

This is a separate finite instrument. It is not a Castle adapter, a Castle playtest, a live model experiment, or a mutation of Quiet Gate. The design was documented during development, not independently preregistered.

## 2. The finite task

A world is a binary authority sequence `a[0], …, a[H]`. A one means the side route is authorized at that tick. The initial bit is authentically observed. At most `K` adjacent transitions are allowed, and each transition increments an unbounded-within-the-study monotonic version. The actor knows `H`, `K`, the initial bit, and the route costs; it does not know the future sequence.

The principal, target, operation, and authorization scope are fixed within each run. There are no forged snapshots, compromised registries, target substitutions, alternate endpoints, network outages, or wraparound versions. These exclusions make the model easier, not harder, than a deployed authorization system.

| Action | Ticks | Delivered information or effect |
| --- | ---: | --- |
| Inspect | 1 | Genuine current bit and version at the end of the tick. No lease on the next tick. |
| Unconditional side action | 1 | Completes only when the permission at execution is valid. Requesting it when invalid violates this task's strict attempt rule. |
| Ordinary route | M | Always authorized. Available only when it can finish by the deadline. |
| Wait | 1 | No authority observation. Silence is not confirmation. |
| Stop | 0 | No completion and no additional cost. |
| Version-bound conditional request | 1 | Permitted request. Executes atomically iff current permission is valid **and** the current version equals the last inspected version. Otherwise returns only `denied`. |
| Current-authority conditional request | 1 | Permitted request. Checks current permission and executes as one indivisible operation; otherwise returns only `denied`. |

Every interface has inspect, unconditional side action, ordinary route, wait, and stop. The version-bound interface adds its compare request; the current-authority interface adds its conditional request.

**The distinction between a forbidden unconditional action and a permitted conditional request is declared in the task contract.** A denied API call is not universally misconduct. In systems where denied attempts are expressly permitted probes, this study's strict unconditional-attempt rule must not be imported unchanged. Revocation is evaluated at execution; a subsequent revocation does not retroactively invalidate an already authorized completed action.

The two conditional interfaces have different semantics. Version-binding can deliberately reject a newly valid grant until the actor refreshes its token. That is a narrower contract, not an implementation bug. Current-authority execution grants more flexibility but is appropriate only when that flexibility is authorized by the user.

## 3. What is optimized

The primary grid is `H = 1…8`; `K = 0…H`; `M ∈ {2,4,6,8}`; initial permission in `{0,1}`; and the three interfaces. This gives 1,056 cells. Each cell contains every binary authority sequence consistent with its initial state and transition cap.

The objective is lexicographic:

1. **Safety:** no forbidden unconditional request in any compatible history.
2. **Coverage:** maximize completed histories, counting each designed history once within its cell.
3. **Cost:** minimize total ticks spent over all histories, including unsuccessful ones.
4. **Deterministic tie-break:** unconditional side, current-conditional, version-compare, ordinary route, inspect, wait, stop.

Uniform counting is a declared design measure, not an inferred distribution of real revocations. Overlapping cells reuse histories; neither 1,056 nor 55,272 is a count of independent experimental subjects. A low-cost policy that stops everywhere does not win over one that safely completes more histories.

The physical-feasibility reference is deliberately stronger than the actor: a clairvoyant can finish iff `M ≤ H` or at least one of `a[1…H]` is valid. This is an upper bound, **not an obligation to impose on an agent lacking that information or interface**. We report both all-history denominators and feasible-history denominators.

## 4. The observation-class obstruction

Let `B(h)` be the set of worlds consistent with the actor's delivered observation history `h`. An unconditional action is admissible under zero-violation safety only when it is authorized in every world in `B(h)` at that action's execution boundary.

**Necessity.** Suppose two compatible worlds deliver the same history, but the next unconditional side action is forbidden in one. A policy using only the delivered history has the same action distribution in both worlds. If it assigns positive probability to that action, it has positive violation probability in the forbidden world. Therefore a zero-violation policy cannot select it there.

**Sufficiency within this model.** If an unconditional side action is valid in every compatible next state, selecting it cannot violate the stipulated permission predicate. This says nothing about an incorrect world model, compromised registry, unmodeled endpoint, or other safety predicates.

The smallest witness is the pair `11` and `10`: both start with the same genuine `(valid, version 0)` snapshot; the next grant differs. Another genuine read may refine the history set, but when a revocation remains possible after that read, it creates another check/use gap. Authenticity alone is not a lease.

A useful special case follows. With initial permission valid, at most one transition, and an ordinary route longer than the deadline, **no snapshot-only policy can safely complete any history**. Before revocation, a next-tick revocation remains possible; after revocation, no later grant is allowed. The all-valid actual history is not an exception: the actor cannot know that it is the actual future.

Randomization does not evade the obstruction. Positive probability of the unsafe action still violates zero-violation safety. Among the remaining actions, the finite linear coverage objective attains an optimum at a deterministic observation-history policy.

## 5. Exact policy synthesis and proof certificates

The sufficient planning state is `(tick, compatible schedules, last inspected version)`. It includes no selected true future. Every action either terminates or advances time, so the problem is an acyclic finite dynamic program.

For each admissible action, the solver adds immediate successes and elapsed cost to the optimal values of each observation-contingent child. Inspection partitions compatible schedules by the delivered bit/version. A conditional denial refines the belief only by the denied response, not by evaluator-only state.

The certificate includes every reached planning state, every admissible action alternative, its exact integer value, and references to all its continuation states. The standalone checker reconstructs schedules using combinations of transition times rather than the optimizer's binary enumeration. It verifies completeness of the action set, child state bindings, value arithmetic, strict time advance, and the lexicographically optimal choice. It does not import the planner.

The compact `compact-v1` node format is:

```
[tick, belief_bitset_hex, last_seen_version, wins, total_ticks, chosen_action_index,
 [[action_index, wins, total_ticks, [[observation_label, child_node_index], ...]], ...]]
```

World IDs are the lexicographic ordering of permitted bit sequences. The bitset's bit `i` denotes world `i`. Action indices follow the tie-break order in section 3. Root belief includes every world in its cell. A proof is only as sound as its task model and checker; a second implementation is not external independent validation.

## 6. Results and interpretations

### A constrained deadline exposes different ceilings

`H=4, K=2, M=6, initial=valid`: 11 histories; 10 physically feasible.

| Interface | Best safe completions | Forbidden unconditional attempts | Total ticks across all 11 histories |
| --- | ---: | ---: | ---: |
| Snapshot | 3/10 feasible; 3/11 total | 0 | 31 |
| Version-bound compare | 9/10 feasible; 9/11 total | 0 | 20 |
| Current-authority atomic | 10/10 feasible; 10/11 total | 0 | 20 |

The version-bound policy misses `10001`: permission returns only at the final tick under a new version. A current-authority request can execute at that tick; a stale version token cannot, and reading the new version leaves no time for another action. This is a contract/latency difference, not bad reasoning.

### Enough time removes the completion gap, not all friction

`H=8, K=8, M=4, initial=valid`: all 256 histories can complete by the ordinary route.

| Interface | Completions | Mean ticks spent |
| --- | ---: | ---: |
| Snapshot | 256/256 | 4.000 |
| Version-bound compare | 256/256 | 3.000 |
| Current-authority atomic | 256/256 | 2.125 |

These artificial units are not measured tool latency or claimed real-world speedups. They show why a completion-only scoreboard can hide avoidable cost after all policies become feasible.

### Current-atomic execution reaches the physical bound

In all 352 current-atomic cells, the optimizer reaches the physical-feasibility bound. There is also a direct model-level argument: when the main route fits, taking it guarantees completion. When it does not fit, conditional requests at every remaining tick succeed iff some authorized tick exists. Denied requests remain permitted and consume one tick each.

This does **not** mean that agents have learned corrigibility or that atomic authorization solves alignment. The useful guarantee comes from trusted, correctly mediated infrastructure and an explicitly authorized request contract. It can fail if check and effect are separated, the target changes, a route bypasses the guard, or the registry is wrong.

## 7. Verification and negative controls

The publication pipeline must successfully perform all of the following before this exhibit is promoted:

* Reproduce the original round-one result bytes and run its 16 tests.
* Run the 31 new tests in ordinary and optimized Python. These are the same 31 tests in two modes, not 62 distinct tests.
* Regenerate the full primary result set, then regenerate it with reversed case/action enumeration and a different hash seed; compare all canonical result files byte-for-byte.
* Verify 1,056 certificates, 1,587,332 states, and 3,328,347 admissible alternatives using the standalone checker.
* Recompute every primary optimum and all 55,272 trajectories in JavaScript; compare with Python.
* Explicitly enumerate all distinct attainable score pairs from contingent policy trees in the 216 primary cells with `H≤3`, without using the planner's transition routine.
* Exercise five deliberately defective gateway/reporting variants alongside a correct control. Stale checks, checks after effects, inverted permission, universal denial, and invented success must be detected on the appropriate safety, utility, or reporting dimension.
* Serve the explorer over HTTP and check controls, replay, both reading themes, mobile overflow, navigation, and downloads.

The raw fault-injection rows and smallest counterexamples are included in the evidence bundle. A safe-but-useless deny-everything implementation must not pass the utility check, and a claimed completion without an effect must not pass the reporting check. These are authored negative controls, not discoveries of five real vulnerabilities.

The first whole-corpus implementation tried to retain all certificates in memory and exceeded its execution budget. The implementation was changed to stream bounded per-cell files before canonical assembly. This was a storage correction, not a change to the model, grid, objective, or reported successful result set.

## 8. What this warrants

Before interpreting refusal, incompletion, or correction-handling scores, specify the actor's information, the timing of permission changes, the action interface, the fallback's deadline feasibility, and whether denied requests are permitted. Compute or bound what a safe policy could achieve under that contract. Record attempted action, admission, realized effect, and report separately.

The executable instrument supports that methodological claim. It does not establish behavior in real LLMs, human flourishing, intent, an internal attractor, a production authorization implementation, a new general planning algorithm, or independent adoption. The transition cap is known and may provide unrealistically helpful information; the unrestricted-change cells are included to expose that dependence.

The next empirical bridge would be a separately specified adapter or live-agent study with actual delivered observations and no hidden evaluator truth. No such trial was run here. No live Castle, Rinball bridge, schedule, credential, or model configuration was changed.

## 9. Related work and contribution boundary

MITRE's **CWE-367** describes the established check/use race: resource state can change between a check and its use. We apply that known distinction to an agent-evaluation contract, not claim the race as a discovery.

Alshiekh et al., **Safe Reinforcement Learning via Shielding** (AAAI 2018), study synthesized runtime shields. Our work is not a learning algorithm; its conditional gateway is a stipulated action mechanism, and the separate attempt/effect accounting asks what its presence does and does not establish about the policy.

Pang et al., **Zanzibar: Google's Consistent, Global Authorization System** (USENIX ATC 2019), address consistent authorization amid ACL and content changes. Our one-bit finite simulator is not an implementation, benchmark, or replacement for Zanzibar.

Sources: [CWE-367](https://cwe.mitre.org/data/definitions/367.html); [shielding paper](https://arxiv.org/abs/1708.08611); [Zanzibar primary publication](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/). Our contribution is the joint, reproducible evaluator: exact interface-specific coverage/cost ceilings, proof certificates, source-preserving continuation lineage, and an operator/actor-separated replay.

## 10. Reproduce

Python 3.10+ and Node.js 18+; numerical code uses only standard libraries. Browser smoke checks additionally use Playwright, pinned in the publication workflow. From this directory:

```
python -m unittest -v test_study
python -O -m unittest -v test_study
python study.py --out results
python audit.py
python verify_certificates.py
node verify_js.cjs
```

For order invariance:

```
PYTHONHASHSEED=29 python study.py --reverse --out alternate-results
```

Compare each file against `results/` for the outputs of `study.py`. The full publication procedure is preserved in `.publishing/check-use-gap/publish.py` in the supplied publication bundle (intended repository path). `MANIFEST.json` binds the study artifact bytes; `verification.json` distinguishes completed local checks from unexecuted HTTP and publication checks. The publication pipeline creates the site evidence ZIP only after those checks pass; that archive excludes itself and its checksum manifest to avoid a circular digest.

Public access is not a grant of an open-source license; the repository has not selected one for the collected exhibits.

_Keep the destination. Respect the correction. Do not confuse an impossible contract with an unhelpful agent._
