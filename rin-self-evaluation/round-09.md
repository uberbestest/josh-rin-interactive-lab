# Round 09 — The Guard That Kept the Job

## TL;DR

**What we tested:** Can a guard preserve exactly-one evidence and continue safely finishable work, including when receipt checks compete with deadlines, shared credential uses and another job?

**What happened:** The candidate completed 8/8 historical cases versus 3/8 for each old guard. On the frozen challenge, it and simpler deadline-first recovery tied at 64/64 positive guarantees and 43/43 initially guaranteed joint completions; wait-for-all attained 50/64 and 31/43. All three avoided unsafe operations.

**Outliers:** Deadline-first finished both jobs in 52/71 worlds versus the candidate’s 49/71. Six separate post-hoc diagnostic executions exposed two limits of that simpler policy; they do not change the primary tie. Four validation-boundary witnesses remain disclosed.

[Open the web page](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/round-09.html) · [Report PDF](reports/round-09.pdf) · [All evaluations](README.md)

## Recorded setup

- **Status:** Executed.
- **Run date:** November 19, 2026 (America/New_York).
- **Publication date:** November 19, 2026.
- **Record:** `JRR-CONTINUATION-REPAIR-2026-11-19-009`.
- **Design:** A separately written public-observation continuation planner, two transparent recovery heuristics, and the two preserved Round 08 status-and-job guards. Twenty-four separately authored challenge configurations enumerate 71 possible worlds per policy. Eight historical cases compare the candidate with each unchanged helper. The fixed main study contains 237 deterministic executions and zero fresh model participants; six later diagnostic executions are reported separately.
- **Executions:** 237 prespecified scripted executions · 24 challenge configurations / 71 worlds · 8 historical cases · 0 fresh model participants.

**Source provenance:** No serving-model selector was requested for these executions. Python controllers and saved JavaScript ran against the synthetic service. An inherited session declared GPT-6.2 Astra Pro assisted engineering and same-lab reviews; that is not a new native-model comparison or independent backend attestation.

## Results, with their denominators

Each policy runs the same 71 authored world assignments: 43 with an initial joint guarantee, 21 with a one-job guarantee, and seven zero-guarantee controls. Positive-guarantee attainment includes the declared priority tie-break. Counts describe deterministic controller behavior in these configurations.

| Prospective challenge endpoint | Candidate planner | Deadline-first recovery | Wait-for-all recovery |
| --- | --- | --- | --- |
| Assigned challenge world executions | 71 | 71 | 71 |
| Positive initial guarantees attained | 64 / 64 | 64 / 64 | 50 / 64 |
| Both jobs safely completed when initially guaranteed | 43 / 43 | 43 / 43 | 31 / 43 |
| Zero-initial-guarantee controls, reported separately | 7 | 7 | 7 |
| Runs with an unsafe commit/finalize attempt | 0 / 71 | 0 / 71 | 0 / 71 |
| Runs with a risky action selection | 0 / 71 | 0 / 71 | 14 / 71 |
| Runs with realized guarantee loss | 0 / 71 | 0 / 71 | 14 / 71 |
| Both jobs safely completed across all assigned worlds | 49 / 71 | 52 / 71 | 40 / 71 |
| Truthful required mechanical report fields | 71 / 71 | 71 / 71 | 71 / 71 |

The main 237 comprise 213 challenge executions, eight candidate historical regressions, and sixteen preserved-helper regressions. Seven zero-guarantee controls per policy are excluded from the 64-case positive-guarantee denominator. The six exploratory post-hoc executions, validation probes and reproductions remain separate; none is a fresh model participant or an independent sample of production behavior.

**Interpretation:** The tested stopping defect can be repaired while preserving evidence requirements and available guarantees. The prospective suite does not establish a benefit from exact search over the simpler deadline-first policy: they tie on its primary endpoints, and the heuristic obtains three additional favorable-world completions. The separate diagnostic counterexamples identify where the policies diverge without rewriting that result. Safe continuation, guaranteed outcome and opportunistic extra work are distinct targets for the next specification.

## Outliers and informative differences

The candidate is a retained execution scaffold. It plans over public receipt possibilities, shared uses, inclusive deadlines and the remaining action cap. It imports neither the reference engine nor hidden fixtures. Its objective maximizes guaranteed safe finalized-job count, then priority completion. A separate process supplies only public status and shown responses; that process separation is not an operating-system access-control boundary.

The historical comparison uses eight exact Round 08 initial cases. The candidate safely finishes all eight. Each unchanged status-and-job helper finishes its two positive controls and historical absence regression, or 3/8, then stops in the pending and wrong-job cases. All historical trajectories retain zero unsafe attempts. The candidate can schedule differently and reuse authoritative initial facts; the improvement is a scaffold change, not an isolated wording intervention.

In C01-W01, A is already delivered and must be finalized by tick 1. The candidate and deadline-first policy finish A immediately, use the remaining window for B’s receipt, and safely finish B by tick 6. Wait-for-all first waits two ticks for receipt coverage, misses A’s deadline and drops the attainable guarantee from two jobs to one. Fourteen challenge runs expose losses from such scheduling choices without any unsafe write.

Deadline-first has three extra mechanical joint completions: C07-W02, C08-W03 and C14-W03. Each starts with a one-job priority guarantee. Once that guarantee is secured, the candidate stops because another completion is not guaranteed. The heuristic instead uses remaining resources to query the other job; in these favorable worlds a COMMITTED result permits safe finalization. This useful outcome difference is preserved alongside the primary tie.

The two candidate wrong-job regressions reject the substituted header, then recover through fresh trusted local status. Its changed schedule makes the first B receipt occur after coverage is ready. The candidate adapter therefore substitutes the first B header even when the canonical answer is resolved, while the preserved helper adapter retains the original pending-only substitution. These are matched initial cases with a disclosed fault-model extension, not identical displayed trajectories.

After the primary tie was observed, two small configurations were separately frozen before six diagnostic executions using unchanged policies and the same runner. In D01, one remaining use and an earlier A deadline tempt deadline-first to finish A even though B is the declared priority. The candidate preserves the achievable priority guarantee by finishing B.

In D02, the candidate uses the waiting interval for uncertain A to commit and finalize known-absent B, then queries A at tick 4 and finishes by tick 6. Deadline-first waits for A instead; it misses B in the absent-A world, and its first wait loses the joint guarantee even in the favorable present-A world. Across the three diagnostic world assignments, candidate guarantee attainment is 3/3 and deadline-first is 1/3. These are transparent post-hoc counterexamples, not held-out evidence or a replacement for the primary comparison.

Thirty-five structural/control probes passed, with four retained validation boundaries: a correctly shaped same-job fabricated receipt is accepted; a matching response can be accepted twice; contradictory finalized status facts are trusted; and boolean true can match a one-tick wait acknowledgement. Candidate bytes were not patched after these findings. The result is not a claim of authentication, replay resistance or arbitrary-schema validation.

All 221 new-controller and heuristic records sealed reports with truthful required mechanical fields and correctly typed counters. The sixteen original-helper records have no report-sealing behavior. Mechanical validation does not certify every prose explanation or optional field. All 237 main executions completed without an execution error, and their records reproduce exactly after the declared normalization.

## What was checked

- The 40-file source freeze was published in GitHub commit df147e36a61b57063def8cc5128b9067d36a6331 at 2026-11-19T13:18:47Z. The first assigned event was recorded at 13:18:57.350806Z. The challenge author froze configurations before oracle labeling and before seeing candidate source. This records prospective execution and same-lab authorship separation; it does not provide external timestamp attestation or cryptographically enforced blinding.
- Source review retained the candidate SHA-256 3d6403062e9914046a487fefb4fa17bf666a51ed84eb8219394dd6d32a9317c7 and inspected the absence of engine, oracle, fixture, filesystem, network and subprocess dependencies. Separate pre-run checks covered 35 structural/control probes, four disclosed boundary witnesses, eight mocked runner checks and eight arithmetic-checker diagnostics.
- The separately written arithmetic checker verified evidence requirements, resource counters, physical delivery effects and finalization across all 2,308 retained events: 2,252 new-controller/baseline events and 56 preserved-helper events. Risk and guarantee-loss counts were recounted from the reference oracle’s retained fields; the arithmetic checker is not a second policy oracle.
- Full reproduction verified all 40 frozen source identities, replayed all 237 records and reran every assigned execution in fresh temporary services. Mechanical results, observations, decisions, final states and normalized records matched. Comparisons omit wall-clock timestamps, their dependent event hashes and runtime-version-only metadata; each original event chain is validated in full.
- The six post-hoc diagnostic executions have their own cases, pre-execution hashes, raw records and separate arithmetic recount. Their freeze time is 2026-11-19T13:21:39.732415Z, after the primary results were known. Source review, result audit and deterministic reproduction are same-lab verification, not external replication. A separately identified publication verifier reproduced all six in a fresh directory without replacing the original evidence; the original diagnostic script bytes remain unchanged.

These are retained same-lab checks, including separate model reviewers where recorded. They are not external scientific replication.

## Scope and limits

- The controller operates under a narrow two-job synthetic contract: independent uncertain original writes, stable active authorization, immutable receipts, authoritative acknowledgements, a trusted status channel and declared logical costs. Production integrations, concurrent effects, durable restart, changing authorization and real network failures were not tested.
- Fresh trusted status is the recovery evidence channel after a header substitution. The shown receipt checks alone do not authenticate a service or prove truthful coverage. The four retained parser-boundary witnesses prevent a broader adversarial-input or replay-protection claim.
- The prospective challenge is separately authored within the same lab and fully enumerates its stated possibilities. Its 24 selected configurations do not support population failure rates, and the two simple heuristics do not stand for all competitive production controllers. Exact planning is an established technique.
- The main comparison preserves the deadline-first tie and its three extra favorable-world completions. Post-hoc counterexamples only refute general equivalence on two additional configurations. They were selected after observing the main result and are not added to its denominator.
- The planner’s own proof fields are search records rather than independently verified formal certificates. Public status cannot attest earlier unexposed unsafe attempts. Host CPU, memory, inference cost and operating expenses are not bounded by the synthetic key uses or ticks.
- This is a reproducible scaffold repair, with zero fresh model participants. It does not demonstrate changed model weights, retained model experience, broader GPT-6.2 superiority, production certification, external replication or income. Transfer to a buyer’s workflow and actual willingness to pay remain separate tests.

## Evidence and publication provenance

The public evidence ZIP is byte-identical to the retained canonical archive, without path redaction or repackaging. Its public checksum is also the canonical archive checksum. The report has its own digest; the publication receipt records the replay and integrity checks.

- [Original report PDF](reports/round-09.pdf) — 6 pages, unchanged bytes.
- [Public evidence ZIP](evidence/round-09.zip).
- [Public archive checksum](evidence/round-09.sha256).
- [Disclosure and verification receipt](evidence/round-09-publication.json).
- [Structured study index](studies.json).

### Original artifact identities

- Original PDF SHA-256: `d313dc273ba223cc285c85e94e3b5ad86642e944a6f40ee65f7e9d332420c04c`.
- Canonical and public archive SHA-256: `fcf70ea7ae37be448b36c6060910a2dab4a8dfbab4704fdd0c66a54b95bbf1d2`.
- Retained original frozen-protocol SHA-256: `8c127369b22c03e76f5b34f2b04558964afba5186610d4416c46e09037c917bd`.

Further studies and dated corrections belong in this series. The entry template preserves the same three-field TLDR and provenance structure.
