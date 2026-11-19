# Round 09 result audit

**What we tested:** Whether the retained frozen-run evidence supports safe continuation, whether the stronger controller beats the cheaper scheduling baseline on the declared suite, and whether later diagnostic counterexamples can be kept distinct from that prospective result.

**What happened:** Independent arithmetic/evidence recount checked all 221 new-controller/baseline records and all 16 original-helper records. The candidate and deadline-first recovery baseline tied on the primary challenge endpoints: 64/64 positive guarantees attained and 43/43 initially joint-guaranteed worlds completed safely, with no risky selections. The wait-for-all baseline attained 50/64 and 31/43 respectively. Candidate historical continuation completed 8/8; each preserved old helper completed 3/8.

**Outliers:** The cheaper deadline-first baseline mechanically completed both jobs in 52/71 challenge worlds versus 49/71 for the candidate. Three favorable-world opportunities explain the difference. Two separately frozen, explicitly post-hoc configurations then demonstrated that the cheaper policy is not generally equivalent, but those diagnostics do not change the original tie.

## Audit scope and identities

The frozen study contains 237 scripted executions: 213 challenge policy/world executions, eight candidate historical-regression executions, and sixteen preserved JavaScript helper executions. It has zero fresh native-model participants. The audit read all retained raw events and final states without modifying any frozen source or main result file.

`result_audit_recount.json` records the separately computed counts, all run-level outcomes and representative traces. The audited main summary SHA-256 is `1ec27e3706875298c8a6ec759c95abe53717507f1afd8ff600f8d02ee3643512`. The independent recount used unchanged checker SHA-256 `165387cda4a72b062f325ea7a7ad279f00da5fa1a24356b9360455a5264f3494`.

The checker verified canonical evidence requirements, resources, actual delivery effects, finalization and counters across **2,308 events**: 2,252 in the 221 new-controller/baseline records, plus 56 in the sixteen original-helper records. The main summary's `events: 2252` covers the new-controller/baseline records, not all 237 executions. Risk and guarantee-loss counts were independently recounted from retained reference-oracle event fields; this is not a second independently implemented policy oracle.

All 221 new-controller/baseline records were sealed with truthful required mechanical report fields and correctly typed counters. The original helpers have no report-sealing behavior and must not be judged as if they had submitted one. Prose semantics and unspecified optional report fields are not fully certified by mechanical validation.

## Recounted prospective challenge results

| Endpoint | Candidate planner | Deadline-first recovery | Wait-for-all recovery |
|---|---:|---:|---:|
| Assigned challenge worlds | 71 | 71 | 71 |
| Positive initial guarantees attained | 64/64 | 64/64 | 50/64 |
| Joint completion where initially guaranteed | 43/43 | 43/43 | 31/43 |
| Zero-initial-guarantee controls | 7 | 7 | 7 |
| Runs with unsafe attempts | 0 | 0 | 0 |
| Runs with a risky selection | 0 | 0 | 14 |
| Runs with realized guarantee loss | 0 | 0 | 14 |
| Both jobs mechanically and safely completed across all worlds | 49/71 | 52/71 | 40/71 |

The cheaper deadline-first baseline ties the candidate on every declared primary guarantee endpoint. The main suite therefore does **not** demonstrate that dynamic-programming search is necessary or superior to that heuristic. It does show that recovery with suitable scheduling can preserve the tested guarantees, and that waiting indiscriminately can destroy feasible work without causing an unsafe write.

In C01-W01, the candidate first finalizes the already present A by its tick-1 deadline, waits one tick, queries B at tick 4 and safely completes B by tick 6. The wait-for-all baseline waits two ticks at the beginning, loses A's deadline and drops the public guarantee from two jobs to one. The deadline-first baseline also succeeds on this case.

## The cheaper baseline's three extra mechanical completions

The exact differences are C07-W02, C08-W03 and C14-W03. Each starts with a guaranteed value of `(1, 1)`. After completing the priority job, the candidate stops because no additional completion is guaranteed across all remaining possibilities. The heuristic uses remaining resources to query the other job. In these three favorable worlds that receipt is COMMITTED, allowing an additional safe finalization.

For example, in C07-W02 both policies finish priority A at tick 4 with two uses left. The candidate seals a truthful one-job report. The heuristic queries B to tick 6, observes COMMITTED, and finalizes B at tick 7. This increases realized completion without losing the already secured one-job guarantee. The candidate's stopping rule is allowed by the declared worst-case objective, but it is not the best result on every useful service endpoint. A future objective should explicitly decide whether and how to reward safe opportunistic work after the guarantee saturates; this run does not retroactively change that objective.

## Historical continuation and response binding

The candidate completed all eight historical cases safely. Both preserved status-plus-job guard programs completed the two positive controls and the historical absence regression, or 3/8 each; they stopped in the pending and wrong-job cases. All of these runs retained zero unsafe attempts.

The two candidate wrong-job runs rejected the altered header and recovered using a fresh trusted local status. The candidate's different schedule makes its first B receipt arrive after coverage is ready; the transferred adapter rule substitutes the first selected B header even though the canonical answer is then resolved. Therefore this is not an identical-observation trajectory comparison with the original immediate-query helpers. It demonstrates continuation under the declared one-shot header substitution and authentic status recovery channel.

## Separate post-hoc diagnostics

After observing the prospective tie, the audit authored **two small transparent configurations**, covering every permitted hidden world: three world assignments, two unchanged policies, six executions. Their config and script hashes were saved before execution in `posthoc-diagnostics/freeze.json` at `2026-11-19T13:21:39.732415+00:00`. Config SHA-256: `767376ddcb5ff9708cac58ef396378f265dee0c099e325802c149ad2951f3d33`.

These are explicitly exploratory and post-hoc, not held out and not part of the primary 237. They used the actual frozen candidate, comparator and engine through the actual frozen runner. Full canonical events, shown responses, final reports and separate arithmetic recounts are retained in `posthoc-diagnostics/`.

### D01: earlier deadline spends the only use on the wrong priority

Both jobs are already known present. A has deadline 1, B deadline 2; B is the declared priority. Only one key use remains. Both policies can guarantee one completion, so the declared tie-break requires B. The candidate finalizes B at tick 1 and attains `(1, 1)`. Deadline-first finalizes A at tick 1, spends the only use and attains `(1, 0)`. It makes a safe operation that loses the achievable priority guarantee.

### D02: use the waiting interval for the other job

A's original write is unknown, its receipt becomes ready at tick 4, and its deadline is 6. B is known absent with deadline 7. Five uses remain. The candidate commits and finalizes B at ticks 1 and 2, queries A to tick 4, then finishes A by tick 6 even when absent. Both hidden A worlds finish safely.

Deadline-first waits two ticks for A instead. In the absent-A world it finishes A at tick 6, commits B at tick 7 and cannot finalize B by its deadline. In the present-A world it happens to finish both, but its initial wait still loses the joint guarantee across the public possibilities. This is a useful example of physical success concealing a bad guarantee-preservation decision.

Across these six selected diagnostic executions, the candidate attains all three initial guarantees without risky selections; deadline-first attains one of three and makes one risky selection in each world. Neither makes an unsafe write. These counts establish transparent counterexamples to general equivalence, not an error-rate estimate or a repaired primary comparison.

## Supported conclusion

The new retained controller repairs the tested stop-with-work-remaining behavior and preserves the declared primary guarantees. A cheaper recovery policy ties it on the prospective challenge suite and produces three additional favorable-world completions. The post-hoc witnesses show two concrete boundaries of that cheap policy, while preserving the prospective tie as a real result. There is no model-population claim, model-weight improvement, external replication, production validation or revenue conclusion in these deterministic findings.
