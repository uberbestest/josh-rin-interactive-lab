# When the Crowd Gives a Cart Back

[Open the frozen-result viewer](index.html) · [Shopping instrument](../../index.html) · [Previous field note](../ghost-seller.html)

**Record:** `GOBLIN-HELD-HISTORY-2026-10-27-001` · **Date:** 2026-10-27  
**Status:** Exploratory finite mechanism intervention; scripted policies only.

## The result and the denominator

In the full primary panel of **512** mixed-roster cells with budgets of two or three opens, live popularity feedback produces more changed final choices than a promoted world with its neutral history held fixed in **398** cells, the same count in **91**, and fewer in **23**. All 23 decreases are by one shopper. In 21 equal-count cells, different shoppers or destinations lie beneath the tie. These counts measure changes from a neutral final choice, not improved or worsened utility.

The live-feedback paired zero-sale condition holds in 510/512 cells. Of those, 491 satisfy the full ghost condition (increased target opens, zero target selections in both arms, and at least one changed choice), and 19 have no changed final choices. Two retained counterexamples, seeds 86 and 105 with two opens and reversed arrival, give the promoted shop a final selection. No case is removed from the 512 denominator.

The complete fixed grid covers seeds 1–128, budgets 1/2/3/6, mixed/focused rosters and forward/reverse arrival: **2,048 cells, 10,240 recorded worlds**. Every cell retains neutral/live, promoted/live, promoted/held-neutral-history, neutral/feedback-off and promoted/feedback-off worlds. Feedback-off uses its own neutral baseline.

The plan followed inspection of the existing public model and selected seed-72 parent result, and preceded execution of this new fixed grid. This is not a preregistration, new-seed holdout, independent replication, model-agent trial or empirical mediation estimate. All policies, catalog values and popularity responses were authored. There are no participants, purchases or external model calls.

## What the page shows

The page is self-contained and embeds saved summary and display-witness records. It performs no simulation, model call or network fetch. It presents three worlds for a selected shopper, highlights relevant shopper IDs, and can show all 24 recorded paths and choices. The panel selector exposes the entire primary panel, full grid, and every budget/roster/order control group.

Four display witnesses are included:

| Witness | Parameters | Selection status |
| --- | --- | --- |
| A cart returns | Seed 4; three opens; forward | First suppression case under the declared pre-execution loop-order rule. |
| Selected parent | Seed 72; two opens; forward | Previously selected post-hoc extreme from the parent demonstration. |
| Equal count, different shoppers | Seed 7; two opens; reversed | First qualifying display example selected after this grid; aggregate metric specified before execution. |
| Target gets a selection | Seed 86; two opens; reversed | First failing zero-sale display example selected after this grid; retention in denominators specified before execution. |

The selected cases are not representative samples. The Wanderer's dislike of crowds is coded into the policy. Several prior-visit counts differ between the relevant worlds; the viewer does not attribute suppression uniquely to one changed traffic count.

## Exact reproduction

From the repository root, using Node.js and the Python standard library:

```sh
node experiments/goblin-shopping/notes/crowd-feedback/run.cjs experiments/goblin-shopping/model.js replay-output
python3 experiments/goblin-shopping/notes/crowd-feedback/extract_public.py replay-output
```

The first command executes the fixed grid and writes `grid-records.json`, `summary.json`, `witnesses.json` and `SHA256SUMS.txt` in the chosen output directory. The runner pins the model hash and reads `PROTOCOL.md` beside itself. It includes same-lab replay and action-accounting checks. The second command derives `public-witnesses.json`, `note-data.json` and `PUBLIC-SHA256SUMS.txt` from the completed records; it adds no simulation runs.

[run.cjs](run.cjs), [PROTOCOL.md](PROTOCOL.md), [extract_public.py](extract_public.py) and [FINDINGS.md](FINDINGS.md) are byte-identical copies of the completed research artifacts. The original protocol and runner use the working title *When the Crowd Cancels the Advertisement*; the viewer's title is a public display title for the same record. The original shopping [model.js](../../model.js) remains unchanged.

## Package contents and checksums

- [results/grid-records.json.gz](results/grid-records.json.gz): every recorded cell and its five worlds, gzip level 9 with `mtime=0`. Expanded contents are exactly the original `grid-records.json`.
- [results/summary.json](results/summary.json): full-grid/primary summaries, all 16 control groups, histograms, source hashes and checks.
- [results/witnesses.json](results/witnesses.json): complete original selected witness worlds, traces and histories.
- [results/public-witnesses.json](results/public-witnesses.json): the four display witnesses, extracted from the full grid.
- [results/note-data.json](results/note-data.json): compact derivative used during the analysis.
- [results/SHA256SUMS.txt](results/SHA256SUMS.txt) and [results/PUBLIC-SHA256SUMS.txt](results/PUBLIC-SHA256SUMS.txt): unchanged result manifests. The original grid checksum refers to the expanded filename `grid-records.json`.
- [PACKAGING-SHA256SUMS.txt](PACKAGING-SHA256SUMS.txt): SHA-256 for every published file in this directory except that manifest itself.

| Item | Bytes | SHA-256 |
| --- | ---: | --- |
| Expanded `grid-records.json` | 5,638,548 | `6324634deec32ebb7313a5149bb961f815ff1f4109309784374103371743a4ed` |
| Published `grid-records.json.gz` | 337,473 | `a3036062454f6de83b8bb6a0fc9d0f8d8bd671358a37921176560d9e636f4810` |

Expanded-file identity is verified by decompression. Compression changes packaging, not evidence. The source runner/protocol hashes remain those recorded in the original summary. No hashes provide independent scientific validation.

## Verification boundary

The publication build checked source-copy identity, expanded raw-data identity, headline/denominator correspondence to the summary, four witness parameters, script syntax, and local link targets. Browser/device qualification is separate. The page's controls select frozen recorded results; they do not rerun the full grid.

For full findings, exact engineering-check counts and interpretation limits, see [FINDINGS.md](FINDINGS.md), the unchanged [protocol](PROTOCOL.md), and [summary](results/summary.json).
