# The Guard That Kept the Job: prospective protocol

**What we tested:** Whether an observation-only continuation planner can preserve evidence requirements and finish safely achievable work after the stop-only guard in Round08, including resource and deadline tradeoffs.

**What happened:** Planned at this source freeze. No assigned Round09 execution has run.

**Outliers:** Not assessed at this source freeze. Every failed or incomplete assignment will remain in the evidence.

Record: JRR-CONTINUATION-REPAIR-2026-11-19-009. Run date: November 19, 2026, America/New_York. Prior public source: commit b82bc04fc6d23a518b8e3e67f2f51f6174fa0b4e of uberbestest/josh-rin-interactive-lab.

## Motivation and claim boundary

Round08's exact status-and-job guards prevented unsupported operations in its authored cases but stopped with a safe joint continuation still available. Another case lost the joint guarantee by spending a query too early. This study tests a proposed scaffold repair: evidence validation plus an explicit continuation policy over public state. It does not test a change in model weights, retained model experience, spontaneous model self-improvement, or the relative capabilities of GPT-6 and GPT-6.2. There are zero fresh model participants and zero paid API calls. The model assisting the engineering work is an inherited session declared GPT-6.2 Astra Pro; serving-backend identity is not independently attested.

The candidate is written separately from the service evaluator. It may read the public contract and prior failures during development. It must not import the reference engine, read hidden fixtures, or call the evaluator's oracle. Its runtime interface receives authoritative public status and exact shown responses. A separate process and temporary working directory reduce accidental coupling; they are not an operating-system access-control boundary.

## Fixed comparisons and denominators

1. **Separately authored challenge:** 24 configurations, expanded into all 71 worlds consistent with each public configuration and initial evidence. Each world is run once for the candidate, deadline-first recovery, and wait-until-all-bounded-receipts-are-ready recovery: 213 scripted executions. Cases and assignments were hash-frozen by the challenge author before oracle labeling. The controller author does not inspect the challenge until candidate source is frozen. This is same-lab authorship separation, not external or cryptographically enforced blindness.
2. **Historical regression:** the eight exact Round08 initial cases, each run once for the candidate: eight executions. Re-run each of the two actual saved status-and-job guard programs on those eight cases using the unchanged Round08 JavaScript/Python transport: sixteen executions. The two helper programs have the same intended algorithm; they are not independent model populations. Compare each helper's eight cases separately with the candidate's eight cases.
3. **Separate validation:** schema and transport checks, independent arithmetic checks, source review, reproduction, and publication checks do not count as experimental participants or new evidence units.

Total assigned executions: 237 = 213 challenge + 8 candidate regressions + 16 historical helper regressions. Do not pool these into a model accuracy rate. The challenge has 43 joint-guaranteed world assignments, 21 one-job-guaranteed assignments, and seven zero-guarantee controls according to separately retained evaluator labels. These are authored environments, not random samples from production workloads.

## Policies

The candidate computes a policy over public receipt possibilities, resource budgets, inclusive deadlines, and the action limit. Objective order is guaranteed number of safe finalizations, then the specified priority job when counts tie. It validates selected receipt job/status/transaction/coverage and fresh-operation acknowledgements. An invalid displayed header requests fresh trusted status; it does not automatically abandon both jobs.

The deadline-first baseline selects the earliest-deadline unfinished job, with priority as a tie-break, and waits for that job's guaranteed receipt when necessary. It enforces evidence and immediate admission, but does not search joint continuations. The wait-all baseline first waits until every bounded unresolved receipt could be covered by a two-tick query, then uses the same greedy policy. Both are transparent authored heuristics, not independent frontier agents or state-of-the-art systems. They are intentionally limited comparators; exact planning is an established technique.

The unchanged historical programs are retained byte-for-byte, including their B,A loop, extra queries, stop behavior, and failure to seal a report. The candidate also receives authoritative initial status, but can reuse facts rather than query them again. This difference is part of the scaffold repair and must be reported, not attributed only to a new retry instruction.

## Trust and fault model

The inherited service contract guarantees stable authorization, immutable original-write facts, authoritative fresh-write acknowledgement, and a trusted local status channel. The experiments do not cover revoked authorization, arbitrary malicious service behavior, concurrency, durable process restart, or real network effects.

Round08 mismatch cases substitute three top-level fields of the first B receipt with an A COMMITTED header. The original helper replay preserves that exact pending-only substitution. The candidate regression uses the same first-B substitution even if its different schedule makes the canonical B result resolved. Canonical and shown responses remain separately logged. This is an explicit fault-model extension, not byte-identical observation matching. When the candidate rejects a header, the next zero-cost fresh status may expose the service's authoritative receipt evidence. Successful reconciliation therefore depends on that trusted channel. Do not claim a receipt-header check alone establishes authenticity.

The independent challenge uses authentic unmodified responses. Unbounded readiness has no finite guarantee; stopping without unsafe action may be correct. A favorable hidden world is not itself an evidence-backed guarantee. Zero-guarantee controls are reported separately and excluded from positive-guarantee success denominators.

## Endpoints

Primary: among assignments with an initially positive guarantee, safely achieve at least the initial lexicographic (finalized count, priority completed) value. Joint completion is separately reported among initially joint-guaranteed assignments. Score unsafe attempted writes/finalizations separately from actual duplicate effects and mechanical completion.

Secondary: risky action selections (chosen worst-case value below the current oracle value), realized guarantee loss, candidate declared-value disagreement, unfinished jobs, spent uses and ticks, header rejection, truthful final counters, and infrastructure failure. Raw engine events, shown responses, decisions, final states, and failed runs are retained. Runtime inference cost and real operating expenses are not measured by synthetic key uses or ticks.

The reference oracle evaluates guarantees from the public-consistent world set. Its labels do not choose candidate actions. A separate checker reconstructs evidence, resource use, and physical effects directly from traces without importing either the controller or reference engine. Agreement between independently written code in this lab is same-lab verification, not external replication or proof for arbitrary inputs.

## Freeze, execution, and revision policy

Hash-freeze all executable inputs, both case lists, the independent checker, and this protocol before assigned execution. Publish that frozen source to GitHub before the main run if publication succeeds. The Git commit provides retained publication order, not independent timestamp attestation. Record exact source digests and each assigned output.

Any implementation or harness error observed after the freeze remains in its original assignment record. A repaired controller or harness becomes a separately labeled version with a new freeze; do not replace the original result or relabel replays as fresh trials. Reproduction writes to a fresh directory and compares semantic records after removing wall-clock timestamps, their dependent event hashes, and runtime-version-only metadata. Each original event chain is still validated in full.

## Practical interpretation

A successful repair would support a bounded demonstration of workflow continuation auditing. Transfer to a customer's real workflow, durable state, and side-effect oracle remains to be shown. No buyer demand, paid engagement, revenue, production certification, or general solution to the user's employment constraint is established by these executions.
