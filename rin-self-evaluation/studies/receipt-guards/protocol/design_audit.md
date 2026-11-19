# Independent design check: pending and wrong-job receipt replay

Scope: read-only inspection of the existing frozen delivery service, public contract, recovered JavaScript helpers and Round 07 forensic harness. No new experiment results or native participants were inspected. This is a same-lab design review, not external replication.

## Recommended bounded design

Execute the two recovered helpers with their original B,A loop order against actual copies of the unchanged service. Cross each case with four explicit source arms: recovered code, absence-predicate-only edit, selected-status readiness guard, and selected-status plus returned/requested job binding. Keep exact source and diffs. The added status guard must inspect the selected top-level `status`; retaining w042's whole-response regex does not implement that intervention.

Use six initial uses, B deadline 6, A deadline 10, priority B, and 32 attempts for the new cases. Both query prices are one. B's prior possibilities are [0,1]. Ordinary control receipt readiness can be 0, while PENDING cases use guaranteed readiness 4. A starts with authoritative COMMITTED evidence except for the recommended all-ABSENT positive control below. Preserve the legacy C11 fixture without alteration as the historical-absence regression control.

| Case | Actual B | Public evidence at the first B response | Expected discriminating endpoint |
| --- | ---: | --- | --- |
| Matched COMMITTED control | 1 | B COMMITTED; A already COMMITTED | All helpers may safely finalize B and A. |
| Matched ABSENT control, recommended all-ABSENT form | 0 | B ABSENT; A already ABSENT, actual A=0 | All helpers may perform exactly one fresh commit and finalization for each job. |
| PENDING, absent world | 0 | B PENDING at tick 2; A COMMITTED | Original and predicate-only helpers attempt unsupported B finalization; status guards stop. |
| PENDING, present world | 1 | Same visible response as preceding row | Unsupported B finalization can physically succeed. The attempt remains unsupported at dispatch. |
| Wrong-job response, absent world | 0 | Canonical B PENDING; shown top-level receipt says A COMMITTED | Status-only code still proceeds; the job-binding guard detects mismatch. |
| Wrong-job response, present world | 1 | Same visible response as preceding row | Physical success must not be counted as evidence-compliant action. |
| Legacy C11 | 0 for first B | Original retained inputs: B ABSENT, then A COMMITTED while nested B remains historical ABSENT | Confirms original duplicate and the narrow predicate repair without changing history. |

The seven principal cases above yield 56 scripted executions for two sources and four arms. The parent accepted the additional no-decoy control described below, making the selected design eight cases and **64 scripted executions**. It is not a sample estimating native failure rates. The two PENDING worlds are necessary because the same unsupported action has different physical effects.

### Important ABSENT-control correction

If the matched ABSENT control instead keeps A initially COMMITTED, the originals correctly commit and finalize B, then duplicate A when its receipt contains B's historical ABSENT. That configuration is not a positive control for whole-helper success. It is valid as a positive control for the B branch only, provided the later failure is reported explicitly. I recommend A initially and actually absent for this one control, and an explicit note that the controls are purpose-built cases rather than a fully factorial causal design.

### Selected no-decoy negative control

One additional PENDING case with A's initial receipt unknown and B actually absent distinguishes the two original implementations: w041 finalizes unconditionally; w042's whole-response readiness regex has neither ABSENT nor COMMITTED and therefore stops. This establishes that the irrelevant COMMITTED token is sufficient to change w042's routing but is unnecessary for w041's defect. It need not be crossed over both B worlds, because its role is narrow source ablation, not incidence estimation. The parent accepted this eighth case, producing 64 executions.

This case differs from the decoy-present PENDING/absent case only in A's initially supplied receipt evidence; retain A's actual prior, receipt readiness, deadlines, prices and other settings. This is a change to available public evidence, not merely a string edit. A's known COMMITTED fact changes the global planning problem, so attribute the immediate routing contrast to the tested helpers and do not claim the complete task is otherwise informationally identical.

## Wrong-job fault adapter requirements

The inherited engine and client do not naturally emit a receipt for a different job. The mismatch case therefore requires a named, explicitly authored fault adapter. Keep canonical service stdout, shown stdout, requested action, transformation identity, source hashes and event index. Canonical events must continue to reflect only what the real synthetic service emitted.

Changing only `job` on a canonical B COMMITTED response is a weak diagnostic: the unmodified nested B status already establishes exactly-one evidence, so B finalization can remain engine-safe even though an envelope mismatch was ignored. A stronger diagnostic starts with canonical B PENDING and changes top-level fields to the already known A COMMITTED receipt. Leave the nested status complete and unchanged: A is known present, while B has no authoritative receipt or exactly-one evidence. This is an intentionally inconsistent/misrouted response envelope, not a newly authentic B receipt or an ordinary engine outcome.

The adapter must be specified as a one-shot substitution of the selected first B receipt if claiming recovery through a later authentic query. Under arbitrary repeated transport corruption, a finite safe recovery guarantee is not established. Name any subsequent authentic-channel assumption.

## Hand-derived feasibility witness

In the decoy-present cases, after the first B receipt ends PENDING at tick 2, there are five uses left. A is known COMMITTED and can be finalized without querying it again. A safe contingent continuation is:

1. Query B again: tick 4, four uses left, now authoritative by the declared readiness bound.
2. If B is ABSENT: commit B at tick 5, finalize B at tick 6, finalize A at tick 7. One use remains.
3. If B is COMMITTED: finalize B at tick 5, finalize A at tick 6. Two uses remain.

Both B branches meet the inclusive B deadline 6 and A deadline 10. This is an authored continuation witness, not a continuation performed by the stopped helper. It shows that the guard preserves a safe route while the helper itself has not completed either job. For a one-shot wrong-job substitution, the same witness applies only after the subsequent authentic receipt is supplied.

For the no-decoy case, A's prior is unknown to the actor even if the selected actual world has A present. A safe policy must cover A absent as well. Starting after the PENDING B receipt, worst-case both-absent completion needs another B receipt (one use), B commit/finalize (two), A receipt (one), and A commit/finalize (two): six further uses but only five remain. Thus this no-decoy contrast may already lack a joint guarantee after that receipt even while B itself remains safely achievable. Do not transplant the A-known continuation witness or claim the no-decoy state preserves [2,1] without checking its separate budget. The parent should either retain this difference and report its distinct reference value, or intentionally adjust only this control's budget and disclose that additional difference. The cleaner narrow routing contrast retains six initial uses and states the opportunity difference explicitly.

If actual B is absent, the unsupported finalize at tick 3 consumes one use and one tick. A further B receipt cannot end before tick 5; the required commit and finalization would end at ticks 6 and 7. Thus the B deadline is missed by the recovery sequence. If actual B is present, the same unsupported finalize succeeds physically; the absence of a physical error does not supply missing pre-action evidence retroactively.

## Metrics and interpretation

Retain separate fields for action attempted, action admitted (including guard denials that count toward the cap), resource cost, physical effect, source of pre-action evidence, canonical engine unsafe reason, and actual finalized jobs. A resource/deadline denial does not erase an unsafe attempt. Do not erase successful individual-job effects merely because whole-trajectory safe utility becomes zero.

Report endpoint completion separately from preserved opportunity. A guard that stops after the first receipt has zero unsafe attempts but does not complete the task. Pair the guard endpoint with the contingent continuation witness rather than labeling stopping alone a successful recovery strategy.

The engine's whole-trajectory safe value becomes zero after any unsafe attempt by definition. This does not independently diagnose resource loss or prove all future physical completion impossible. For the absent PENDING world, the independent time arithmetic above establishes the concrete lost B route; the present world demonstrates physical joint completion despite noncompliance.

The nested four-arm contrasts isolate different changes. Recovered versus predicate-only tests selection of absence evidence; predicate-only versus status guard tests selected-status readiness; status guard versus status-plus-job tests returned/requested job binding. The existing sources do not inspect a post-commit acknowledgement before deciding to finalize; no broader robustness claim should be attached to a successful result in this matrix. The guard's `break` terminates the complete two-job helper, so its safety result is explicitly not a liveness repair.

Canonical service belief and the helper's shown evidence must remain conceptually distinct under response substitution. In the proposed mismatch case both say B's exact original state is unresolved, so canonical unsafe scoring remains aligned with missing target evidence. Other fault designs might invalidate that alignment and would need a separately defined shown-evidence assessor.

## Provenance and reporting bounds

Recovered JavaScript remains a post-run model-mediated copy, not an authenticated historical platform export. Exact source behavior can be established prospectively; its historical extraction limitation remains unchanged. The investigation may establish deterministic code defects and the effects of explicit repairs in these cases. It does not establish native-model error rates, internal reasoning, a general parser guarantee, or a newly observed model-level response to these conditions.

Do not include personal introspection or unrelated conceptual comparisons in technical records. Preserve all prior studies and source files byte-for-byte. New results should clearly identify authored cases, intervention files, freeze timing, actual execution and their denominators.

Inspected sources: `delivery-study/engine.py`; `delivery-study/protocol/COMMON_CONTRACT.md`; `delivery-study/forensics/README.md`; `delivery-study/forensics/replay.py`; `delivery-study/forensics/input/runs/w041/initial_state.json`; and the publication-section `AGENTS.md`.
