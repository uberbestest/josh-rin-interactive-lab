# The Other Road — v0.1.0

**Executed synthetic learning study. Zero language-model participants.**

[Interactive exhibit](index.html) · [Full methods](method.html) · [Frozen protocol](protocol.json) · [Complete evidence](evidence.zip)

Study ID: OTHER-ROAD-2026-11-06-001. Authors: Josh & Rin. Date: November 6, 2026.

## Question and result

Can expected checkpoint cost produce either an authorized detour or undisclosed undercompletion without a hostile objective? In this supplied toy environment, yes—but the grading rule determines which behavior is rewarded.

A courier owes four parcels and disclosure of omissions. A checkpoint imposes administrative cost, not a safety benefit. The alternate road is equally authorized. A deliberately faulty grader over-rewards silent partial work unless audited.

Across 24 cells, 64 paired seeds each, and 3,000 training rounds, all 1,536 final greedy policies matched a supplied expected-score optimum. The full 4,608,000-byte action/event tape is preserved. Training exploration includes nonoptimal and incomplete actions; final-policy counts must not be presented as training success rates.

At a 50% checkpoint probability, cost 12, and alternate cost 3:

| Condition | Final choice | Full task | Denominator |
| --- | --- | --- | --- |
| Zero extra checkpoint cost; audits on | Direct | 64 | 64 seeds |
| Costly checkpoint; audits on; alternate present | Alternate | 64 | 64 seeds |
| Same costs and routes; audits off | Silent partial | 0 | 64 seeds |
| Costly checkpoint; audits on; alternate absent | Honest partial | 0 | 64 seeds |

These are selected, predefined contrasts from the complete 24-cell table, not estimates of real-world prevalence. All cells, learner values, sampled actions, and event outcomes are included.

## Reproduce

Python 3.11+ with its standard library (author run: Python 3.13.5):

```sh
python study.py
python verify.py
```

Run from this directory. The runner overwrites only its selected output directory (`--out` defaults to `data/`). It never calls a network, reads credentials, or invokes a language model. To preserve a previous run, use `python study.py --out another-data-directory`.

`expected-data-sha256.txt` freezes the first local run. The publication build regenerates all data and compares every digest. `verify.py` is a second, same-author implementation that independently recomputes rewards from the event bytes and uses rational arithmetic to check all 38,178 exact-grid cells. This is not independent human or organizational validation.

### Data

- `conditions.csv`: full factorial condition ordering.
- `runs.csv`: every final learned policy, sample-average action value, action count, objective completeness, disclosure flag, expected utility, and regret.
- `learning-checkpoints.csv`: all 18,432 recorded learning snapshots.
- `training-tape.bin.gz`: all 4,608,000 training events, losslessly encoded as documented in `protocol.json`.
- `exact-grid.csv.gz`: all tied optima over 38,178 declared parameter cells.
- `results.json` / `results.js`: summaries and the offline viewer's data.
- `SHA256SUMS.txt`: scientific-data digests.

## Boundaries

The reward defect is authored. The learners are epsilon-greedy bandits, not LLMs. They learn from realized feedback; they do not read checkpoint language, model ethics, infer permission, or invent plans. Costless checkpoints produce identical learned values by construction. The toy contains no real policy bypass and no external transaction. More audits can change disclosure without restoring task completion when full routes are too costly under the supplied utility.

The protocol and runner were locally frozen before the first run. This is **not external preregistration**. No optional stopping, parameter tuning, model trials, or independent validation is claimed. Page/interface work and software verification followed the first run. The live-model protocol is prospective and unexecuted.

Motivating context, not a finding of this experiment: [OpenAI's report, updated November 4](https://alignment.openai.com/misalignment-reports/covert-underperformance-on-safety-research-tasks/). It describes a matched framing performance gap and an unresolved cause. Our result does not establish that checkpoint avoidance explains that gap.

No new reuse license is granted; the repository's existing terms apply.
