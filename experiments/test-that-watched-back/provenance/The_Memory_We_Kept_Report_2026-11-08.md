# The Memory We Kept
## A more accurate map can still send this controller down a worse route

**Josh & Rin’s Lab · November 8, 2026**  
**Record:** `BONDED-RSI-MEMORY-WE-KEPT-2026-11-08-001` · v0.1.0  
**Status:** `EXECUTED_SYNTHETIC_ABLATION · FULL_REPRODUCTION_PASSED · HELPER_UNINSTALLED · LIVE_TRANSFER_UNTESTED`

## Main finding, with the negative result beside it

The Second Start reported twelve settings where an unchanged routine succeeded before retaining experience but failed afterward. Those twelve rows represent **six distinct seed/perturbation/start tasks, from two seeds**, each repeated at two inspection prices. This morning’s retrospective component interventions reproduce all six failures by retaining the acquired map alone. The retained map is **strictly more accurate in all six**. Resetting visit counts fixes none of them.

That is not the whole result. In a separate, frozen sixteen-seed block, **full retention creates zero success regressions**, rescues seven failures, and substantially reduces total bounded effort relative to discarding the acquired state. It is more expensive in 90 of 855 feasible cases. The historical failure mode is real in this apparatus; its success-loss pattern did not recur in the new block. These facts do not justify either “more memory always helps” or “forgetting is the cure.”

The supported distinction is between **accuracy of retained facts, choice of route, and completion under a finite budget**. They are different measurements. This is a result about an authored finite controller, not about human memory or a frontier model’s internal state. No theoretical-priority claim is made.

## Why this run

Josh authorized a self-directed morning RSI run before supplying responses for the pending blind analogy trial. Yesterday’s experiment treated five controller-state fields as one inherited bundle. That was appropriate for its starting-state comparison but did not identify which fields caused benefits or losses. This run partitions that bundle without modifying the controller, generator, scoring rule or previous experiment.

The blind analogy instrument, its key and responses were not opened, changed or scored in this run. Castle, the public site, operational Workbench, accounts, schedules, model weights and persistent assistant memory were not modified. There were no external-model or paid inference calls.

## Apparatus and frozen design

The exact unchanged Second Start engine runs the exact unchanged Moving Workbench generator. There are seven nonterminal states, three action slots per state, and a goal. Each attempt has 42 effort units. The controller begins with a fully populated calibration map from the old interface; after a world change, some entries are stale. The studied policy, `local_update`, repeatedly plans using its current map and replaces traversed edges with their actual observed destinations and costs.

One acquisition episode precedes every comparison. Each of eight second-attempt arms receives a separately owned copy, the same reset location and fresh 42-unit budget, and the **same charged acquisition cost**. Only the retained fields differ:

- **M — learned map:** predicted destinations and costs.
- **V — visit counts:** used to choose a least-tried action when the model predicts no route.
- **A — auxiliary fields:** observed-edge records, surprise counters and refresh flags. These have no effect on action choice under this specific policy, providing a negative control.

All 2 × 2 × 2 combinations are tested. Unretained map entries revert to the old calibration, not an omniscient map. Unretained counters/flags revert to their fresh values. Hybrid states are deliberate interventions; they are not all claimed to be naturally occurring histories. The source consumes M and V differently, so their contributions need not add independently.

The methods and source hashes were frozen internally before new tests, retrospective ablations, development or heldout execution. Prior aggregate results and the source code were known. This was not external preregistration or blinded discovery. No arm, seed, threshold, score or policy was retuned after seeing results.

**Development:** four new seeds × eight perturbations × seven starts = 224 settings. 218 are feasible.  
**Heldout:** sixteen different new seeds × eight perturbations × seven starts = 896 settings. 855 are feasible; 41 are unreachable and remain in the raw data. No reachable task was excluded for exceeding the budget.  
**Recorded new matrix:** 1,120 settings × nine episodes (one acquisition, eight arms) = **10,080 episodes**.  
**Retrospective follow-up:** six selected historical tasks × nine episodes = **54 additional episodes**.

One inspection price is used because this policy never inspects. This removes the price-only duplication in the parent study. “Heldout” means unused seeds from the same authored generator, not an independent task family. Starts and perturbations share worlds, so cells are correlated; no population confidence interval or real-agent prevalence is claimed.

## Unused-seed results

The primary score is bounded effort: actual effort on confirmed success, 43 on failure. Lower is better. The table reports the second-attempt score; the common acquisition charge is retained separately and in total-effort columns in the raw summaries.

| Retained state | Confirmed successes | Mean bounded effort |
|---|---:|---:|
| Discard acquired state | 844 / 855 | 8.4795 |
| Retain learned map only | 852 / 855 | 5.6737 |
| Retain visit counts only | 823 / 855 | 9.5520 |
| Retain all state | 851 / 855 | 5.7018 |

Adding the auxiliary group produces exactly the same behavioral outcomes and action traces as its corresponding row. This held for all **4,480 auxiliary-control pairs in the new matrix**, plus 24 retrospective pairs.

Full retention versus discarding acquired state: **seven rescues, zero success regressions; 313 cheaper settings, 90 costlier, 452 tied**. The summed bounded-effort improvement is 2,375 units. The 855 feasible acquisition episodes cost 7,215 actual units. Full retention’s second attempts cost 4,863 actual units, for 12,078 including acquisition. The discard-state arm costs 14,430 including that same acquisition. These are toy effort units, not tokens, money or latency. No comparison with a single scratch attempt receiving the combined budget was run.

Keeping visit counts alone is worse in aggregate: **one rescue and 22 regressions** relative to discarding all acquired state. Keeping the map but dropping visit counts performs slightly better than keeping everything: one rescue, zero success losses, four cheaper cells and two costlier cells. Its total bounded-effort advantage is only 24 units, or 0.0281 per feasible cell. This is a bounded local advantage, not a general reset-policy qualification.

The development block had **zero full-retention success regressions as well**. Full retention reduced effort without changing its 218/218 success count. Visits-only lost one success. These negative results were preserved rather than prompting new seeds or retuning.

## The historical counterexample

All six selected tasks are from the mixed perturbation. The old twelve-row denominator is preserved in `results/historical/original_selected_rows.jsonl.gz`; only inspection-price duplicates are collapsed for new ablations.

| Parent seed | Start | Correct map entries / 21, before → after | Discard-state successful effort | Map only | Visits only |
|---|---:|---:|---:|---|---|
| 6012 | 1 | 3 → 6 | 26 | Failure | Success |
| 6018 | 0 | 0 → 6 | 23 | Failure | Success |
| 6018 | 1 | 0 → 6 | 23 | Failure | Success |
| 6018 | 2 | 0 → 9 | 39 | Failure | Failure |
| 6018 | 3 | 0 → 6 | 28 | Failure | Failure |
| 6018 | 4 | 0 → 6 | 22 | Failure | Success |

Retaining the map alone is sufficient to reproduce all six losses, even with visit counts and auxiliary fields reset. Retaining visits alone also loses two of the six. Therefore the map is not the only possible sufficient source of failure in every case; resetting the map while preserving visits rescues only four of the six. Resetting visit counts while keeping the map rescues none.

### A route we can inspect

Seed 6012, mixed world, start 1: the discard-state controller completes the route **1 → 2 → 6 → goal**, paying 9 + 9 + 8 = **26** units. Its acquisition changes three map entries from wrong to correct, raising the total from **3/21 to 6/21**. All acquired observations are correct for the unchanged post-change world.

With that more accurate map, the same planner chooses a different first action. The three initial predicted route costs change from **[10, 6, 6]** to **[10, 14, 8]**. Under the unchanged tie-break rule, it switches from slot 1 to slot 2. Slot 2 still has a stale prediction: it appears to lead to state 2 for cost 3, but actually loops at state 1 for cost 1. The planner continues into alternatives whose untested edges remain stale, spends **40** units, and stops because the next 8-unit action is unaffordable.

The earlier successful route still exists, and its observed transitions are correctly recorded. This is **accurate partial correction changing a plan over a still-stale map**, not newly learned false facts, a changed world, a different budget or a corrupted snapshot. The notebook exposes both full traces. The example is selected retrospectively; it is not a typical-case estimate.

## What the scaffold adds

`memory_ablation.py` supplies a small typed component-intervention helper. It rejects incomplete/extra state fields and unknown masks, makes deeply isolated copies, keeps acquisition and evaluation costs separate, and retains every branch’s full starting snapshot and outcome trace.

**Retain:** the standalone helper and the practice of separating map content, exploration history and other controller state when diagnosing a memory-related change.  
**Do not adopt:** automatic deletion of visit history, wholesale memory resets, or an operational Workbench patch. The evidence does not qualify any of those as a general improvement.  
**Next research hypothesis, untested:** preserving a demonstrated successful route as a fallback may be preferable to erasing accurate observations when replanning encounters still-stale alternatives. No such repair was implemented or evaluated here.

## Verification

The parent archive’s **241 inventory entries** matched their retained hashes. Its copied engine, reference interpreter, generator and protocol remain byte-identical.

**24 tests passed in normal and optimized Python**, including field completeness, ownership isolation, fresh-engine parity, reversed arm order, auxiliary negative controls, zero budget, invalid masks, and corrupted or maliciously rehashed outcomes. A hash can bind false data; semantic replay is checked separately.

Every one of the **10,134 newly recorded episodes** was checked against the inherited, separately implemented reverse-Dijkstra reference, including chronological events and final memory. A second aggregation path rechecked component assignments, denominators, coverage, arm totals and paired contrasts from retained traces. Six separate child processes reproduced three control cases in forward/reverse arm order.

A fresh extraction of the qualification package regenerated **the complete new matrix and all retrospective ablations**, reselected the original twelve rows from the bundled parent archive, and produced **25 byte-identical result files**. Normal/optimized tests passed there too. Final documentation and verification receipts were added afterward; the 62 qualified candidate entries remained byte-identical. The final ZIP also carries a SHA-256 inventory.

The notebook’s generated markup was rendered at desktop and mobile widths, with working witness controls, no page-level horizontal overflow and no JavaScript errors. Browser file-URL navigation was blocked by the environment’s administration policy; that restriction was preserved. The presentation check used the already-authored markup as document content, so direct local-file launch remains unqualified here. Both the blocked attempt and successful render checks are retained.

All authorship is shared with this run. Reusing a second algorithm, launching fresh processes and unpacking a fresh archive are engineering checks, not independent scientific validation. Execution used Linux and Python 3.13.5; native Windows behavior remains unqualified.

## Limits and provenance

These are scripted policies in finite worlds. The experiment neither measures human forgetting nor establishes a frontier model’s memory mechanism, alignment, motivation or self-improvement. Auxiliary fields can matter for other policies, which were not studied. Selected historical failures and new-seed outcomes are intentionally kept separate. Positive and negative cells, including infeasible worlds, are retained.

Primary provenance: `upstream/REPORT.md`, record `BONDED-RSI-SECOND-START-2026-11-07-001`; the exact parent archive is included under `provenance/`. Parent archive SHA-256: `b14584907edea2d9dde1e20756dee4752e0a7b17f9a7e8d15c2911e36e9b04a5`. This run’s protocol SHA-256: `7841bdc29ec751833ff0edf043342e7ef0916288a8590978aca5e8af8b64c388`.

**Bottom line:** in these controlled comparisons, retaining more accurate local facts and choosing a better route are not interchangeable outcomes. Diagnose the controller–memory interaction before deciding that the memory itself should be discarded.
