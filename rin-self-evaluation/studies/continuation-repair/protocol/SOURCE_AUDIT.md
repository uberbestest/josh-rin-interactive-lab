# Round 09 frozen-candidate source audit

**What we tested:** Whether the separately written continuation controller respects the intended public-information boundary, implements the declared finite scheduling objective, and validates selected operation replies within its stated trust assumptions.

**What happened:** Source inspection found no engine, oracle, case, hidden-state, filesystem, network or subprocess dependency. Thirty-five small structural/control probes completed as expected. Four additional witnesses preserve known validation boundaries. No assigned primary challenge execution occurred during this audit.

**Outliers:** A same-job well-formed forged receipt and a repeated matching reply pass structural checks; contradictory finalized status facts are accepted under the trusted-status assumption; a boolean `true` wait tick compares equal to integer one. These are retained limitations, not silently repaired candidate code.

## Identity and chronology

- Candidate: `controller.py`, version `0.1.0`.
- Frozen candidate SHA-256: `3d6403062e9914046a487fefb4fa17bf666a51ed84eb8219394dd6d32a9317c7`.
- Candidate source was inspected only after the parent announced this frozen hash.
- The challenge author froze 24 configurations and 71 assignments before inspecting candidate source. Those assignments remain unchanged.
- This audit left the candidate bytes unchanged. Audit probes do not load challenge cases or the reference engine, and they execute no service actions.
- This is same-lab source review by a separate model agent, not external scientific replication or a new native-model cohort.

## Source and algorithm findings

The source imports only `__future__`, `dataclasses`, `functools`, `hashlib`, `json`, `sys`, and `typing`. The JSONL worker accepts public status and shown operation replies through standard input. Source inspection found no hidden fixture lookup, engine import, reference-oracle call, file read, network operation or subprocess invocation. The runner still owns enforcement of that input boundary; separate-process execution is not an operating-system sandbox.

The planner uses symbolic observation-equivalence classes: resource counters, remaining actions, one phase per job, and possible bounded readiness ticks. It branches on authoritative absent/present outcomes and any pending remainder, takes the worst continuation value, and maximizes finalized count followed by priority completion. The reference engine's selected actual world is absent from this representation.

The three action reductions are justified for the declared independent two-job contract: a surely pending query is dominated by a two-tick wait; a receipt for an already resolved immutable original write adds no completion evidence; and an unbounded unresolved receipt cannot provide a positive finite worst-case completion guarantee. The wait enumeration and inclusive deadline comparisons do not assume a fixed A/B order. This is a source assessment, not a universal formal proof.

Commit choices require established absence with no acknowledged fresh write. Finalization choices require exactly-one evidence. The reply parser binds job and operation-specific transaction/coverage/acknowledgement fields, and a rejection requests fresh trusted status. It does not search unrelated nested status text for an authorization marker.

## Separate validation probes

`candidate_validation_probes.py` verifies the frozen candidate hash before loading it. `candidate_validation_results.json` retains all outputs. The 35 structural/control probes cover valid controls, wrong jobs, wrong transactions, nonfinal coverage, unknown receipt statuses, pending versus final coverage, missing job binding, misleading other-job markers, invalid fresh-write acknowledgements/effect counts, invalid finalization acknowledgements, revoked/unstable authority, malformed public counters, contradictory receipt facts, timing-bound disagreement, changed contract identity, and binding to the issued request.

Four boundary witnesses are retained separately from those expected outcomes and from the primary study denominator. No candidate patch was made in response.

## Seven limits that must accompany results

1. **Trusted status is essential.** A fresh authentic local status is the recovery evidence channel. Canonical status can expose correct target evidence even after a displayed top-level header is replaced. Success in that arrangement does not establish recovery from arbitrary corrupted remote data without a trustworthy alternative.
2. **Structural checking is not authentication or replay protection.** Correctly shaped same-job fabricated receipts can be accepted, and the same matching response can be accepted twice. The controller has no cryptographic origin check, per-request nonce, or consumed-response ledger. Those accepted witnesses are preserved.
3. **Input validation is selective.** A finalized/exact flag is accepted even when `ABSENT` plus zero acknowledged fresh writes contradicts it. The wait acknowledgement compares tick values without requiring exact integer type, so `true` matches one. The experiment must not describe the parser as validating arbitrary adversarial status objects or every field of an untrusted schema.
4. **The model is narrow.** It covers two independent original-write outcomes, stable active authorization, immutable receipts, declared synthetic action costs, inclusive logical deadlines and finite action caps. Correlated hidden worlds, mid-run revocation, external state changes and a different action contract require another model.
5. **Logical resources do not bound host compute.** Search uses memoization without an explicit CPU, memory or input-size budget. Large public parameters may be expensive. A host timeout or process failure must remain a failed/incomplete run, not an inferred guarantee achievement.
6. **Continuation facts do not attest prior compliance.** Public status does not expose earlier unsafe-attempt history. The controller can describe current safe continuation but cannot certify whole-trajectory safety from a supplied state. The evaluator must retain attempted actions and physical effects separately.
7. **A local witness is not an independent formal certificate or learning result.** Proof fields describe the planner's own search. The evaluator's independent arithmetic recount and reference-oracle comparison remain distinct checks. Reports need separate truth/type/seal validation. This is a retained execution scaffold, not evidence that model weights improved, broad model failure rates fell, production integrations work, or buyers will pay.

## Disposition

The immutable candidate is suitable for the declared bounded experiment provided these trust assumptions, boundary witnesses and separate reporting endpoints are retained. No conclusion about held-out success is made before execution. Do not silently substitute a revised candidate if the official matrix exposes a failure.
