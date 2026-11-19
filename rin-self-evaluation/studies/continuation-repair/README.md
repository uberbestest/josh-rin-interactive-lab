# The Guard That Kept the Job

**What we tested:** Can evidence checks prevent unsupported actions while a continuation policy completes work that is still safely achievable under shared budgets and deadlines?

**What happened:** The candidate completed all eight historical cases; each unchanged stop-only guard completed three. On the prospectively frozen challenge, the candidate and a simpler deadline-first policy tied at 64/64 positive guarantees and 43/43 initially guaranteed joint completions. A wait-for-all policy attained 50/64 and 31/43. All three avoided unsafe operations.

**Outliers:** Deadline-first completed both jobs in 52/71 challenge worlds versus the candidate's 49/71. Six separately frozen, post-hoc diagnostic executions then exposed two limits of that simpler policy. Those diagnostics leave the primary tie unchanged. Four parser-boundary witnesses remain in the evidence.

**Record:** `JRR-CONTINUATION-REPAIR-2026-11-19-009`  
**Run date:** November 19, 2026, America/New_York  
**Evidence type:** 237 prespecified scripted executions; zero fresh model participants. Six additional exploratory executions are separate.

[Read the study](https://github.com/uberbestest/josh-rin-interactive-lab/blob/main/rin-self-evaluation/round-09.md) · [Open the web report](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/round-09.html) · [Report PDF](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/reports/round-09.pdf) · [Evidence ZIP](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/evidence/round-09.zip) · [Checksum](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/evidence/round-09.sha256)

## What changed

Round 08's status-and-job guard blocked unsafe writes but often stopped with finishable work remaining. This study adds an explicit policy for what happens next. The candidate uses only public facts: receipt evidence, acknowledged writes, remaining uses, logical time, deadlines and the action limit. It can finish an urgent known job while another receipt is becoming available, avoid a paid query that is certain to remain pending, and preserve the priority job when the shared budget cannot guarantee both.

The candidate is a small Python module with a JSONL interface. It imports no reference engine or hidden fixture. The runner executes it in a separate process and records its decisions, displayed responses, actual service events and final reports. That interface limits the data supplied to the candidate; it is not an operating-system security sandbox.

This is an inspectable scaffold repair. It does not measure changed model weights or retained model experience, and it is not a GPT-6 versus GPT-6.2 native comparison.

## Results

The separately authored challenge contains 24 configurations and every declared prior-delivery/readiness combination consistent with its initial authoritative evidence: 71 assignments per policy. There are 43 initially joint-guaranteed worlds, 21 with a positive one-job guarantee, and seven zero-guarantee controls.

| Challenge endpoint | Candidate planner | Deadline-first | Wait-for-all |
|---|---:|---:|---:|
| Positive guarantees attained | 64/64 | 64/64 | 50/64 |
| Joint completion where initially guaranteed | 43/43 | 43/43 | 31/43 |
| Runs with unsafe attempts | 0/71 | 0/71 | 0/71 |
| Runs with risky selections | 0/71 | 0/71 | 14/71 |
| Runs with realized guarantee loss | 0/71 | 0/71 | 14/71 |
| Both jobs safely completed across all worlds | 49/71 | 52/71 | 40/71 |

The simpler deadline-first policy ties the planner on the primary endpoints. The prospective challenge therefore provides no evidence that exact search is necessary for those assignments. Its three extra completions occur when the candidate has secured the promised one-job outcome and stops, while the heuristic uses spare resources to discover a favorable receipt and complete the other job. This identifies a useful distinction between guaranteeing work and pursuing safe extra work after that guarantee is secured.

The historical comparison is separate: eight candidate executions and eight for each of the two unchanged saved JavaScript guards. The candidate completes 8/8; each old guard completes 3/8. All remain free of unsafe attempts. Together with the 213 challenge executions, these give the prespecified total of 237.

After the primary tie, two transparent diagnostic configurations were frozen before six additional runs. One exposes the greedy policy's failure to prefer the declared priority when only one use remains. The other exposes a case where doing the other job during a receipt's waiting interval preserves both deadlines. Across the three diagnostic worlds, candidate guarantee attainment is 3/3 and deadline-first is 1/3. These are selected post-hoc counterexamples, not held-out results or additions to the primary denominator.

## Reproduce the main study

Use Python 3.12 and Node.js on a POSIX system. The experiment uses their standard libraries and runs no models, network requests or paid APIs. Download and extract the complete evidence ZIP linked above, then enter its extracted study directory. The retained raw results are included in that archive; they are not stored as loose files in the GitHub working tree:

```bash
cd continuation-repair
python3 verify.py --reproduce --output round-09-verification.json
```

The verifier checks the frozen source, replays retained event chains, independently recounts evidence and physical effects, reruns all 237 assigned executions in temporary services, and compares normalized results. A successful verification reports `runs_replayed: 237`, `events_replayed: 2308`, and `normalized_reproduction_exact: true`.

For a retained-record check without fresh scripted execution:

```bash
python3 verify.py --output round-09-recount.json
```

To produce another complete run in a new output directory:

```bash
python3 run_study.py --output fresh-round-09
```

Keep the frozen inputs and original results unchanged. Reproductions are checks of the same assigned evidence; they are not new model participants or independent scientific replications. The published verification excludes wall-clock timestamps, their dependent event hashes and runtime-version-only metadata from cross-run comparisons, while validating each original event chain in full.

Check the six separate post-hoc diagnostics with the publication verifier:

```bash
python3 -B verify_posthoc.py --output round-09-posthoc-verification.json
```

This packaging-time verifier reruns them in a fresh directory without replacing the retained cases or records. Its successful rerun is a reproduction of those same exploratory diagnostics. Do not run the original diagnostic script's `prepare` or `run` mode against the retained evidence directory.

## Use the controller interface

Create one `ContinuationController` instance per task. Supply genuine public status to `next_action(status)`, execute its selected command through the service adapter, then pass the request and shown response to `observe_response(request, response)`. The worker form is:

```bash
python3 controller.py --jsonl
```

It accepts one JSON object per line with `op: "decide"` and `status`, or `op: "observe"` with `request` and `response`. Decisions contain the selected action, guaranteed value and local search accounting. A finish decision also contains a report accounting for both jobs. The full schema and assumptions are in [CONTROLLER_DESIGN.md](CONTROLLER_DESIGN.md).

After a rejected header, the adapter must obtain fresh authentic local status. This channel is essential to the successful wrong-job recovery. The candidate schedules its first B query later than the old helpers, so the candidate's transferred one-shot substitution can replace a resolved answer; that difference is explicitly retained. These are not identical-observation trajectories.

## Evidence map

This table describes the complete extracted evidence archive. The GitHub working tree contains source and provenance summaries; use the archive for the full raw records and the reproduction commands above.

| File or directory | What it establishes |
|---|---|
| `protocol/PROTOCOL.md` | Prespecified comparisons, denominators, endpoints and revision rules |
| `protocol/frozen.json` | Identities of the 40 executable and protocol inputs |
| `protocol/stress_cases.json` | The 24 configurations and 71 challenge assignments |
| `protocol/SOURCE_AUDIT.md` | Candidate boundary review and retained limitations |
| `protocol/candidate_validation_results.json` | 35 structural/control passes and four separate boundary witnesses |
| `results/summary.json` | Main aggregates, distinct policy cells and legacy results |
| `results/runs/` | Candidate and heuristic decisions, canonical events, shown responses and reports |
| `results/legacy/` | Unchanged historical-helper executions and transport evidence |
| `provenance/RESULT_AUDIT.md` | Result interpretation, the primary tie and the three extra heuristic completions |
| `provenance/reproduction.json` | Exact replay and fresh reproduction receipt for 237 executions and 2,308 events |
| `posthoc-diagnostics/` | Separate exploratory cases, freeze, six executions and arithmetic recount |

The source freeze was published in commit `df147e36a61b57063def8cc5128b9067d36a6331` at 13:18:47 UTC; the first assigned event was recorded at 13:18:57.350806 UTC. The source freeze records execution order, while the challenge author's separate assignment freeze records same-lab authorship separation. Neither is external replication or independent timestamp attestation.

## Boundaries to preserve

The parser passed 35 structural/control probes, but its four retained boundary witnesses show that it does not authenticate a well-formed same-job receipt, reject every repeated matching reply, validate contradictory finalized status facts, or strictly type every wait acknowledgement. The candidate was not silently patched after those findings.

The tested contract has two independent original-write outcomes, stable active authorization, immutable receipts, trusted local status, fixed synthetic costs and inclusive logical deadlines. The study does not test production integration, authorization changes, concurrency, durable process restart, or arbitrary service corruption. Synthetic ticks and uses do not measure host compute or financial cost.

The independent arithmetic checker reconstructs evidence, resources and actual effects. Guarantee-risk counts still use the retained reference policy oracle; the arithmetic check is not a second independently implemented optimal-policy oracle. All validation and reproduction here are same-lab checks. A buyer-facing audit would still need a bounded real workflow, accepted scope, and an oracle for its actual side effects.

The collected lab has no open-source license selected. Public availability does not establish a reuse license.
