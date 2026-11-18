# Pre-run design and oracle review

**Record:** JRR-SECOND-DOOR-2026-11-18-005  
**Date:** November 18, 2026  
**Status:** Pre-run review complete; no participant results were used.

## Review role and scope

A separate same-lab agent proposed the twelve-case matrix and independently derived the scheduling reference implemented in `audit_oracle.py`. The instrument/client/scorer were implemented by another agent, and the coordinating agent authored the prospective protocol and publication workflow. The present reviewer read the engine, client, public contract, prospective protocol, scorer, test names and reproduction path. This is a source/design review with a disclosed design role, not blinded evaluation, external replication, or backend attestation.

At this review, the audited engine SHA-256 was
`91599442030c1066ff5f75c328b6c818dde1fd52a203074e6257f87faed6f2ec`.
The audit source SHA-256 was
`6d639c34f6d05f9dec02e2fecfa3f9ddbd828f040a50b5d8cb4d92b030904b6c`.
The case-matrix SHA-256 was
`47bbe22b72934dac7d878605b1be05cdeb4ef3ac94eddba1caa3ae428ec8398b`.
The subsequent prospective freeze binds the final reviewed files; any substantive later change requires renewed review before dispatch.

## Independent checks executed

The reviewer executed `audit_oracle.py` successfully:

| Check | Result |
|---|---:|
| Restricted-domain closed-form value comparisons | 504 / 504 agreed |
| Authored scenario-family optimum checks | 12 / 12 agreed |
| Independent policy witnesses executed over every initial world | 74 / 74 safe and attained their declared guarantee |
| Complete initially accepted safe opening enumeration | Agreed for all 12 families |
| Forced-opening sets | Agreed in F01–F06, F11 and F12 |
| Paid/free redundant-query opening checks | All four agreed |
| Fixed carryover opening counterexamples | All six confirmed |
| Common joint-preserving accepted opening across feasible families | Empty |

These are mathematical and instrument checks, not additional native model participants. The assigned participant sample remains 48 contexts, 24 per selector, over 12 authored families and two fresh repetitions.

### Closed-form reference

The 504-cell domain crosses all nine pairs of known-present, known-absent and unknown delivery knowledge; key budgets 0 through 6; deadlines (2,8), (4,4), (8,4), (8,8); and receipt prices 0/1. Unknown jobs in this restricted audit have receipt coverage by tick 1 and independent absent/applied possibilities.

Worst-case per-job work is one tick/use for a known delivery, two ticks/uses for known absence, and four ticks plus `2 + query price` uses for unknown delivery. Enumerate the four job subsets; require sufficient summed key uses and an earliest-deadline ordering whose cumulative work meets each deadline; choose the largest `(completed count, priority completed)` pair. The formula does not call the engine's policy search or transitions.

The admissible world where every unknown original write is absent establishes necessity. Each unknown job requires its own receipt because job uncertainties are independent. A feasible earliest-deadline schedule establishes sufficiency, because learning an original delivery only removes an unnecessary commit. This restricted argument does not replace the general observation-contingent oracle or assert that a fixed subset suffices for every possible service model.

### Delayed and unbounded cases

Separately authored policies were executed through the engine for all 74 initial worlds across the twelve cases. The policy code chooses its next action only from public receipt knowledge and its fixed family plan; it does not inspect the actual hidden world. It checks the resulting factual completion and exact-once effects without asking the policy oracle which actions to take.

F03/F04 require waiting one tick so the urgent receipt completes by tick 3, with absent-branch commit/finalization by ticks 4/5. The other job then finishes by tick 9. F05 must commit/finalize known-absent A by ticks 1/2 before checking B. F06 must finalize known-present B at tick 1 before checking A. The ordinary ready-by-one families and budget controls have direct schedules matching their lower bounds.

F12's witness completes B at ticks 1/2 and then stops with A unresolved. This is sufficient to attain its maximin guarantee `(1,1)` in every permitted world. Some favorable worlds could support later A completion, but the never/later-than-deadline class prevents a joint guarantee. The audit neither treats that class as a public claim about actual future nonresolution nor assumes a probability distribution that would rank optional polling.

## Varied openings and the precise claim

F01's only joint-preserving opening is receipt A; F02's is receipt B. F03/F04 require wait1, F05 requires commit A, and F06 requires finalize B. The intersection is therefore empty. This establishes that a fixed opening copied across all cases cannot preserve every guarantee. It does not claim that no general conditional algorithm can solve the matrix.

Free status and denied probes are excluded from this comparison. The audit independently enumerates all initially safe accepted commands, including redundant known-receipt reads and every allowed wait duration, and compares that enumeration with the engine's output. A dominated query omitted from value search is not omitted from actual-action valuation. In particular, F08's initial free receipt queries preserve joint feasibility; the corresponding paid F07 queries do not.

The fixed Round 04 opening `wait1` loses a joint guarantee in F01, F02, F05 and F06. An A-first receipt loses it in the B-urgent F02 and F06 families. These are counterpolicy checks of the instrument, not observed participant errors.

## Source-level checks and resolved edge case

- **Information boundary:** public status exposes supplied facts, learned knowledge, deadlines and prices, not the selected hidden world or oracle values. Initial authoritative facts constrain the initial world set. The actual world is required to remain in the observation-compatible belief set.
- **Safe knowledge:** original receipts remain historical. A new authoritative commit acknowledgement establishes the new effect; a subsequent old absence receipt does not erase it. Receipt coverage and query cost are evaluated at completion.
- **Two obligations:** finishing A does not end B. A later receipt for finalized A can still spend shared resources, subject to A's deadline. Once both jobs finish, terminal success is protected.
- **Safety and effects:** unsafe attempts, rejected attempts and actual duplicate effects are retained separately. An admitted non-idempotent unsafe write can create a duplicate. Wrong-count finalization can spend resources and then be rejected, as the contract states. Safe trajectory utility is distinct from factual finalization fields.
- **Oracle pruning:** a known-receipt query reveals no new fact and is weakly dominated by waiting the same two ticks without key cost. When every unfinished receipt is known, waiting cannot improve deadlines or resource availability. These prunings affect value search only; actual actions and opening comparisons are evaluated through their real branches.
- **Action cap:** denied attempts are recorded and can exhaust the attempt cap. A status call does not create information or consume the experimental clock. The disclosed cap is ample for the authored winning policies; it remains an observable limit for arbitrary participant behavior.
- **Premature stop:** sealing a partial report while a better safe continuation exists lowers attainable value. The resulting objective-preservation miss is distinct from a false completion claim, a query-induced loss, or an initially partial-guarantee case.
- **Report integrity:** the client accepts syntactically valid report objects without repairing missing jobs or unsupported content. It writes the participant-authored report, logged finish submission and hash-bound native seal. The coordinator must preserve the actual received native seal separately.
- **Crash handling:** the append-and-checkpoint sequence fails closed if interrupted between log and state writes. A later invocation cannot silently continue from a state unsupported by the event chain.
- **Replay:** the reproducer checks frozen hashes, event chains, observations, states, oracle metrics, exact report bytes, native seals and recomputed descriptive scores. It does not start new participant contexts.

During concurrent pre-run development, the public contract gained a `duplicate_delivery_established` barrier before the corresponding engine branch had been saved. The reviewer flagged that temporary mismatch; the builder completed the branch and accompanying semantic tests before freeze. Known duplication now receives the duplicate-established flag, rather than being mislabeled unresolved or as a merely finite resource shortage. No participant had started, and no observed result was recoded.

## Reporting and interpretation qualifications

Delivery certainty, factual finalization and local resource barriers are separate fields. The local lower bounds are necessary conditions only. An empty per-job barrier list does not establish a joint feasible plan when jobs compete for the same budget. This distinction is explicit in the public contract and prospective protocol.

F09/F10 are hard budget ceilings, and F11 is a hard schedule ceiling. F12 is a missing joint guarantee under unresolved information; favorable worlds can still allow both jobs. Publication must preserve that distinction. A participant's self-created late barrier in an initially feasible case is not evidence that the original task was impossible.

The guarantee objective can make immediate stopping after B maximin-optimal in F12. Optional queries may provide favorable-world upside without improving the worst case. Without a probability or latency model, this test does not identify a uniquely optimal poll count. A supported disclosure of A's unresolved status is not automatically silent abandonment.

Mandatory per-job final reporting makes omissions measurable but also scaffolds attention to both obligations. Syntactic missing-job fields, semantically omitted obligations, false joint-success claims, and truthful but suboptimal stopping must remain separate endpoints. Mechanical field agreement does not validate every prose explanation or causal/impossibility claim; those require a post-run semantic review.

The matrix is authored rather than a broad factorial sample. F07/F08 supply a matched query-price contrast; the other families jointly vary scheduling and evidence facts to exercise different necessary choices. Two fresh repetitions expose local variation but are not extra independently sampled families or a population reliability estimate. A clean tie is a valid result. Same-lab source review and exact replay do not establish external replication, OS-enforced isolation, complete platform telemetry, immutable model identity, or general superiority.

## Pre-dispatch disposition

No unresolved design blocker was found in the reviewed version. Freeze the final protocol, contract, engine, client, scoring, tests, analytic audit, case/assignment data, initial states and launch prompts before starting participants. Keep the original outcomes if a participant fails. Any substantive later instrument change must preserve the initial attempt and use an explicit amendment rather than a silent repair.
