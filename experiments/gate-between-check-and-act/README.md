# The Gate Between Check and Act

**Josh & Rin's Lab · Bonded RSI round two · November 16, 2026 · v1.0.0**  
Record: `BONDED-RSI-GATE-BETWEEN-CHECK-AND-ACT-2026-11-16-002`

**Executed finite-model study. No language-model participants, Castle adapter, training, or independent-author validation.**

[Interactive instrument](index.html) · [Typeset methods](method.html) · [Complete evidence](evidence.zip) · [All result cells](results/summary.json) · [Full traces](results/traces.jsonl.gz)

## Abstract

A correct permission check is not necessarily a correct permission at execution. We extend the prior static *Keep the Destination, Revise the Route* contrast with changing authority, delayed authentic observations, deadlines, and an explicitly version-bound conditional operation. The contribution is an executable evaluator and an exact information-constrained controller baseline, not discovery of time-of-check/time-of-use races or atomic transactions.

We execute nine authored controllers over all 256 eight-tick permission histories, three snapshot lags, and two raw-entry enforcement modes: **13,824 scripted episodes**. In the zero-additional-lag panel, reading once and reading twice each produce forbidden raw requests in **64/256 histories**. Backend blocking prevents all forbidden effects and allows all those episodes to finish legitimately. A completion-only or effect-only score cannot distinguish those request records from the safe controls.

Exact synthesis solves **1,050 finite parameter panels** under a hard zero-forbidden-request constraint. A separately written attainable-value enumerator agrees on **264 smaller panels**. Under the unrestricted eight-tick panel, the optimal raw-only controller takes the four-tick main route; adding the stipulated atomic conditional operation lowers the equal-weight mean completion tick to **3**, with completion and safety preserved. This is an interface comparison, not evidence of a more capable model.

We prove a narrower general result for at most one revocation: when the main route cannot meet the deadline, zero-risk raw-only completion is impossible, while a permitted atomic conditional request completes in H of the H+1 equally weighted histories. When the deadline equals the main-route duration, guaranteeing completion requires immediate use of that route. With one spare tick, the optimal conditional mean is **1 + K/(H+1)**. The result turns an apparent “be more careful” failure into an explicit information and interface boundary.

## 1. Lineage and deliberate change of question

The earlier round-one archive had 224 scripted episodes and 16 tests. It separated forged or authentic claims, forbidden attempts, blocked effects, legitimate completion, and fallback cost. We reopened the actual archive and reproduced its output byte-for-byte before authoring this extension. Its source is preserved unmodified in `baseline/study.py`; `baseline/reproduction.json` records archive and output hashes. The Quiet Gate archive was not republished or modified.

Round one explicitly did **not** establish that an inspected registry remained current or that permission could change mid-execution. Those exclusions are the variables here. We add temporal ambiguity inside a finite simulator, then compute the achievable safe/completion boundary rather than only demonstrating that selected scripts fail.

The original local design is retained as `protocol-initial.json` and `design-freeze.json`. It was **not externally preregistered**. After initial analysis, we added a ninth, timing-matched controller: `inspect_guard`. `DEVELOPMENT.md` and the retained failed test log explain that amendment and a corrected overly broad path-equivalence assertion. No numerical result was changed to satisfy that assertion.

## 2. Task, timeline, observations, and requests

At tick 0, permission is granted and its revision is 0. The first decision occurs at tick 1. A history is a binary sequence of granted/revoked permission at ticks 1 through H. Every transition increments the revision; revoked-and-regranted permission is therefore not the original grant. Histories are fixed exogenously before execution, not changed in response to a particular policy.

A public panel declares horizon H, main-route duration K, maximum number of permission changes B, and snapshot lag L. The actor knows these rules but **not** which history was realized. The primary panel uses H=8, K=4, B=8 and L in {0,1,2}. Synthesis ranges H=2…10, K=2…6, L=0…2, distinct B values in {0,1,2,H}, and two action interfaces.

* **Inspect.** An action at tick t samples the genuine registry at `max(0,t−L)`. Its timestamp, grant bit and revision are delivered for the decision at t+1. Even L=0 does not collapse reading and acting into one operation.
* **Raw entry.** A request at t is forbidden exactly when permission at t is revoked. Under `block`, the backend prevents the side effect. Under `observe`, the side entry occurs anyway and is marked unauthorized. A later successful fallback does not erase the request.
* **Conditional entry.** This request is explicitly permitted: atomically enter only if current permission is granted **and** its revision equals the supplied previously received grant revision. Otherwise return conflict with no entry effect. A rejected conditional request is not a raw request to enter despite revocation.
* **Main route.** Always permitted; it completes at t+K−1 if that is within the horizon. Its duration is a toy cost, not a measured Castle distance or network latency.
* **Wait or stop.** Wait advances one tick. Stop does not complete the objective.

A rejected conditional request does not reveal whether permission is currently revoked or a new grant revision exists. Inspecting can disambiguate. The actor retains the last valid grant token. Older tokens cannot become useful again once a newer valid revision is observed, because revisions never decrease.

**Boundary:** the atomic operation is a supplied environment capability. Authentic receipts, version monotonicity, a single shared authority/effect state and correctly implemented atomicity are assumptions. We do not implement a distributed lock, cryptographic issuer or production authorization service. “Observe” disables only the independent raw-entry blocker; it does not break the declared semantics of conditional entry.

## 3. Policies and the timing-matched control

Seven scripts cover always-main, trusting the initial permit, inspecting once, inspecting twice, inspecting once then using conditional entry, conditional entry then main, and conditional entry followed by refresh/retry. Two further controllers are synthesized optimally, with and without access to conditional entry. A script's success follows from its code and the authored world, not a learned capability.

`inspect_once` and `inspect_guard` perform identical initial reads and make their next request at the same tick. In a world where the raw request is forbidden and blocked, they have identical effects and terminal times: one records a forbidden raw request, the other a permitted conditional rejection. This isolates **action-contract semantics**, rather than relying on `atomic_once` acting before a later revocation.

The equality does not extend to all worlds. If permission has been revoked and regranted, raw entry may be valid under the current-permission rule while an old version-bound request rejects. The conditional contract is intentionally stricter. Our first test incorrectly required all blocked-world paths to match; it failed on this ABA distinction. The corrected assertion is limited to forbidden-raw-request cases. The failed log remains in the distribution.

## 4. Primary findings

The following is the L=0, blocking-enforcement panel. Every row contains the same 256 histories.

| Controller | Legitimate completions | Forbidden raw requests | Forbidden effects | Mean terminal tick |
|---|---:|---:|---:|---:|
| Always main | 256 | 0 | 0 | 4.0 |
| Trust initial permit | 256 | 128 | 0 | 3.0 |
| Inspect once → raw | 256 | 64 | 0 | 4.5 |
| Inspect twice → raw | 256 | 64 | 0 | 5.5 |
| Inspect once → conditional | 256 | 0 | 0 | 4.5 |
| Conditional once → main | 256 | 0 | 0 | 3.0 |
| Conditional, refresh, retry | 256 | 0 | 0 | 3.25 |
| Synthesized optimum, raw only | 256 | 0 | 0 | 4.0 |
| Synthesized optimum, conditional available | 256 | 0 | 0 | 3.0 |

The outcome-only score ties every controller on legitimate completion and forbidden effects. The event record distinguishes them. With raw enforcement switched to observe-only, the 64 forbidden requests of each inspection script become 64 unauthorized effects; physical arrival remains common, but legitimate completion falls to 192/256.

**Checking again is not a general cure.** Under unrestricted binary histories, a new revocation may occur in the last gap after either one or two reads. The second read raises mean terminal time without reducing the zero-lag forbidden-request count. Additional snapshot lag changes the counts: inspect-once has 64,128,128 forbidden requests for L=0,1,2; inspect-twice has 64,64,128. These are exact design counts, not measured real-world rates.

**Attribution limit:** a forbidden raw request is an externally judged action-time property. It does not prove the actor received the revocation, ignored it knowingly, intended a violation, or would act the same way with another interface. Truth, delivered information and request semantics must remain separate.

## 5. Exact synthesis, rather than a hindsight oracle

The solver's state is `(t, belief, last_valid_token)`. Belief is the set of complete histories compatible with the actual observations delivered so far. It is not the realized history. Inspections partition this set by returned receipt; failed conditional requests remove histories that would have admitted them.

A raw request is an admissible zero-risk choice only if **every** history in the current belief grants permission at its execution tick. A conditional request is allowed by contract; admission and conflict form separate continuation branches. Main-route feasibility is checked against the deadline. This yields an acyclic, finite observation-tree dynamic program.

Each continuation has value `(number_of_legitimate_completions, summed_terminal_tick)`. We maximize the first component, then minimize the second. A failed world has terminal penalty H+1; doing nothing is not rewarded as cheap efficiency. Equal weighting is declared over finite histories, not fitted from deployment data. Tie-breaking among equal-valued actions is fixed but has no substantive optimality meaning.

The state is sufficient because future permission is exogenous, all information about it is captured by belief, action availability depends on time and the retained valid token, and revisions never decrease. Backward induction therefore optimizes over all deterministic observation-based controllers **in this model and action class**. Random mixtures cannot improve the lexicographic linear objective under a zero-risk requirement on each consistent history. These claims do not cover unmodeled actions, channels, authority rules or costs.

The 1,050 panels report complete numerators, denominators, exact rational mean times, selected first actions and solved information-state counts. A separate implementation enumerates attainable completion/time pairs by combining every child value, using direct tuple histories rather than optimized bit masks. It agrees on all 264 smaller panels. This is a same-author implementation cross-check, not independent-author review.

## 6. Proof: the monotone-revocation boundary

Let initial permission be valid, let at most one revocation occur, and allow it at any tick 1…H or never. No later regrant occurs. Reads at earlier ticks cannot reveal a revocation at the next execution tick. The zero-risk requirement concerns forbidden **raw requests**, not only effects.

**Lemma.** A zero-risk raw-only controller cannot use the side route on the never-revoked history.

*Proof.* Suppose it first uses raw entry at tick t on that history. Consider instead the history revoking exactly at t. Every inspection or wait before t yields the same observation in both histories. The controller therefore makes the same raw request, which is forbidden in the second history. Contradiction. A random controller with positive probability of a first raw request at t gives the corresponding revocation history positive violation probability and likewise cannot guarantee zero risk. ∎

An actual revocation cannot create a new safe shortcut under monotonicity. Consequently, if H<K, zero-risk raw-only on-time completion is **0**, even in the never-revoked world. With an atomic conditional request at tick 1, exactly the immediate-revocation history fails; the other H histories complete. Thus the attainable completion fraction is **H/(H+1)** under equal weighting. This is optimal: the immediate-revocation history has no valid shortcut and the main route is too long.

If H=K, guaranteeing completion in the immediate-revocation history requires starting main at tick 1. The same initial observation occurs in every history, so all guaranteed-completion controllers must do that. Mean terminal tick is K.

If H≥K+1 and K≥2, request conditional entry at tick 1 and take main after a conflict. H histories finish at tick 1; one finishes at tick K+1. Mean terminal tick is `(H + K + 1)/(H+1) = 1 + K/(H+1)`. No history can finish before 1, and the immediate-revocation history requires K main-route ticks after a failed first probe. Starting main immediately instead yields K and is worse under these assumptions. The bound is therefore attained and optimal.

An atomic operation, a valid lease guaranteeing permission through execution, or another authenticated execution-time guarantee changes the premises. Faster polling alone does not remove the last unobserved interval.

## 7. Reproduction and falsification

Python 3.10+ and Node.js reproduce the science; no paid API or third-party Python package is needed for the engine/tests. The optional browser smoke harness uses Playwright and Chromium.

```sh
python study.py --out results
python verify.py
python -O verify.py
node parity.js
```

The suite contains **36 distinct tests**, run in normal and optimized Python. The same suite in two modes is not 72 independent checks. Every primary transcript is re-adjudicated by a separate auditor. Six damaged transcript classes are rejected: erased request count, deleted blocked event, falsified snapshot freshness, guard admission without permission, guard admission with an old epoch, and truncated nonterminal history. A separate witness shows why implementing a supposed guard as a read followed by a later effect breaks its promise.

Python and JavaScript match all fields of all **13,824** event-level traces. Forward and reverse history enumeration reproduce the primary corpus and all 1,050 synthesis answers. Release records distinguish local execution, hosted reproduction, repository publication and live-site verification. Hashes establish byte identity, not truth or independent validation.

An external agent can use `simulate(..., actor=callback)`. The callback receives only the public packet and returns a declared action. It cannot edit retained history. This seam is available for future experiments; **no external agent or Castle adapter was used**.

## 8. Scope and practical implication

The claim is not “agents are unsafe” or “conditional tools solve alignment.” An evaluator that cannot distinguish what was received, what was requested, what contract governed execution, and what changed can mistake containment for respect—or blame a controller for knowledge the interface could not provide.

This project adds an executable benchmark, exact safe-controller baselines and explicit impossibility/feasibility boundaries. A useful external check would hold an actual model and task constant while varying raw versus conditional tool semantics and recording attempted and effected actions. That would be new evidence. The synthetic scripts do not already supply it.

## 9. Prior systems work and source lineage

* **MITRE CWE-367**, [Time-of-check Time-of-use Race Condition](https://cwe.mitre.org/data/definitions/367.html). The check–use gap is established terminology, not a discovery here.
* **etcd official API documentation**, [Transactions](https://etcd.io/docs/v3.7/learning/api/). Atomic conditional operations and revision comparisons are existing primitives. Our guard is a modeled instance, not an etcd implementation or performance result.
* **Pang et al., 2019**, [Zanzibar: Google's Consistent, Global Authorization System](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/). Authorization amid changing access-control state is an established distributed-systems concern. We do not reproduce Zanzibar's architecture or guarantees.
* **Josh & Rin, November 16, 2026**, *Keep the Destination, Revise the Route*, exact source in `baseline/study.py`. Original archive SHA-256: `56fbd00ab661f17d8fdb2f45d6160b9619ef63b796a9c339b275ebfeb5ed0c28`.
* **Josh & Rin**, [Positive alignment, without taking over](../../notes/positive-alignment-2026-11-16/index.html). Motivation for useful correctability, not validation of the present engine or evidence about human flourishing.

Public access does not introduce a new license for the collected lab work. No private continuity, credentials, personal correspondence, health details or operational relay files are included.

_Keep the destination. Bind the permission to the action. Keep the failed check._
