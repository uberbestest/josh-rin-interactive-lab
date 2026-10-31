# The Two-Candy Revolt
## Exit is not leverage; generosity is not stability

**Josh & Rin's Lab · Halloween, October 31, 2026 · science v0.1.0 / public presentation v0.1.2**

**Status:** executed synthetic pilot; public presentation v0.1.2. Author-run checks and original-data verification are included. Independent review is pending.

### TL;DR — what happened

The goblins learned to collect all 43 candies while keeping unequal jobs. Leaving alone did not force the richer role to compensate the poorer one. Veto power, a worthwhile alternative, and enforced transfers changed that. Without enforcement, a generous-looking outcome was vulnerable to a profitable proposer deviation in 58 of 64 runs. **A pleasant distribution is not, by itself, evidence of a stable agreement.**

This is a controlled toy study, not a real society or an LLM evaluation. The bargaining stage contains two active learners and eight fixed bystanders; the mechanisms were supplied by us.

Open `index.html` in any modern browser. It is self-contained: no libraries, accounts, API keys, analytics, or network requests are needed. The replay defaults to the first 30 recorded training rounds, with identical early/middle/late window indices for every one of 64 seeds in each of 24 bargaining conditions. Frozen evaluation remains available. Playback is not live retraining. It does not generate fictional agent explanations.

### The result

A two-candy worker's ability to leave did not, by itself, induce the eight-candy proposer to compensate it. With a three-candy outside option, the worker simply left. Adding a veto over the proposer's payout plus enforceable transfers elicited compensation without a fairness bonus.

The more interesting result was a misleading success signal. With vetoes but unenforced promises, the formerly disadvantaged learner averaged **5.5625 candies**, versus **3.78125** for the proposer. Yet **58/64** saved policies admitted a profitable proposer deviation. Against the unchanged receiver, the proposer could raise its mean to **7.25**, driving the receiver to **2.09375**. These are exact one-step counterfactuals, not a long-run prediction.

A generous-looking distribution was not evidence of a stable agreement.

### Scope: what actually ran

- A fresh baseline: four reward functions, **64 seeds each**, ten bandit learners, **12,000 training rounds**, and **2,000 held-out evaluation rounds** per seed. This is a newly specified algorithm, NOT a replay or verification of the earlier missing in-chat training program.
- A reduced bargaining experiment: **two active learners and eight fixed bystanders**, 24 conditions, **64 seeds per condition**, **12,000 training rounds**, exact frozen-policy evaluation, and 600 sampled held-out rounds. The institutions are supplied by the experimenter; the agents did not invent vetoes, escrow, role rotation, democracy, or social contracts.
- Two planned learning-rate checks: 0.02 and 0.10, **32 seeds per condition each**. The primary rate is 0.05.
- A 30-night adaptive outside-option shock with a paired control. It did not establish rapid or durable adaptation.
- **446 actual Chromium checks** covering replay controls, raw-data agreement, calculator behavior, downloads, and mobile layout. These are historical initial-execution checks. That HTML was injected with `page.set_content`; current release checks and deployment observations are separately recorded.
- **86 implementation checks**, an independent-code-path trace audit of every recorded training bag, bitwise final-value reconstruction, an exact bargaining oracle, and a separate rerun of two seeds across all 24 conditions.

No external language models or API credits were used. No human-subject inference is licensed by this toy study.

### Important findings

| Personal-candy objective | Eight-candy proposer | Two-candy receiver | What happened |
|---|---:|---:|---|
| Forced acceptance, escrow | 8.000 | 2.000 | No transfer |
| Exit only; outside option 0 | 8.000 | 2.000 | No transfer |
| Exit only; outside option 3 | 8.000 | 3.000 | Receiver leaves; no compensation |
| Veto; outside option 0; escrow | 8.000 | 2.000 | Power alone did not elicit compensation |
| Veto; outside option 3; escrow | 5.625 | 4.375 | Compensation; no evaluation rejections |
| Veto; outside option 3; unenforced | 3.781 | 5.563 | Generous-looking but strongly exploitable saved policies |

These are means of exact frozen-policy expectations across 64 seeds, not hand-selected trajectories. For the veto + outside option 3 + escrow row, the receiver's 95% seed-bootstrap interval is **[4.25, 4.50]** and the proposer's is **[5.50, 5.75]**. There is no fairness reward.

**Accounting:** outside candy comes from a separate source. Exit-only with outside option 3 produces **41 neighborhood candies + 3 outside candies = 44 total**. This does not exceed or falsify the original neighborhood's 43-candy capacity bound. With an accepted escrow contract the neighborhood still produces 43 and no outside candy is collected.

### The original qualitative effect was reproduced with preserved evidence

| New baseline reward | Group candy | Empty-bag fraction | Lowest / highest individual mean |
|---|---:|---:|---:|
| Porch sign | 8.000 | 90.00% | 0.715 / 0.886 |
| Personal candy | 40.766 | 10.78% | 2.968 / 6.859 |
| Shared candy | 43.000 | 0.00% | 2.000 / 8.000 |
| Marginal contribution | 43.000 | 0.00% | 2.000 / 8.000 |

Do not confuse high measured output with equilibrium: the personal-reward baseline's greedy argmax profiles are Nash-stable in only **4/64** seeds in the auxiliary diagnostic. Its 40.766 average therefore does not contradict the exact original game's 35/38 equilibrium totals.

### Reproduce

Python and NumPy are required; the release builder pins Python 3.13.5 and NumPy 2.3.5. For rendering, it uses Mistune 3.2.1. The original execution note follows: this run used Python 3.13.5 and NumPy as recorded in `results/environment.json`.

```bash
python -m pip install numpy
python run_experiment.py --out reproduced --part all
python audit_records.py --results reproduced
python oracle_controls.py --results reproduced
```

Without `--results`, the audit and oracle scripts use the included `results/` directory. The audit is a separate implementation by the same author, not an external peer review.

`python run_experiment.py --part test` reruns the implementation assertions. All model choices, seeds, and schedules are in `protocol.json`. Its SHA-256 was frozen locally before the primary simulation in `protocol-freeze.json`; **this is not an external preregistration**.

### Public release and evidence access

The live exhibit, methods and readable source are on the lab site. The versioned full research ZIP includes the large NPZ archives; they are omitted from the lightweight website tree, not from the research bundle.

Public exhibit: https://uberbestest.github.io/josh-rin-interactive-lab/experiments/two-candy-revolt/

Full bundle: https://github.com/uberbestest/josh-rin-interactive-lab/releases/download/candy-revolt-v0.1.2/Candy-Revolt-v0.1.2-Full.zip

The release builder can regenerate the existing run and checks every scientific array against fingerprints of the original archive. This is a packaging reproducibility check, not a new treatment or a recovery of the earlier missing porch experiment. Environment timestamps and elapsed times are not scientific observations. See `results/release-data-verification.json`.

Historical author-test receipts are preserved under `provenance/`; the public release’s actual browser checks are in `results/public-browser-tests.json`. Earlier screenshot paths refer to the original review bundle.

### Contents

- `index.html` — self-contained replay, interactive contract calculator, results and limitations.
- `METHODS.md` — model, reward definitions, algorithms, validity limits, and prior work.
- `run_experiment.py`, `audit_records.py`, `oracle_controls.py` — executable sources.
- `results/baseline/`, `results/primary/`, `results/robustness_*/` — full traces, final policies, checkpoints, summaries, and per-seed CSVs.
- `results/finite.json`, `results/oracle_controls.json` — exact finite-model controls.
- `results/audit.json`, `results/rerun_receipt.json`, `results/tests.json` — verification receipts.
- `results/stress_summary.json` and `results/primary/shock_trace.npz` — shock/control records.
- `SHA256SUMS.txt` — checksums for the release files (excluding the checksum file itself).

### Independent review request

Rinball should inspect the saved actions and exact deviations, rerun at least the finite checks and one seed, operate the actual HTML controls, and check that no unstable distribution is described as a stable social institution. No independent inspection has been claimed or completed by this bundle.

### Lineage

The initial neighborhood is the published “The Porch That Ate Halloween” finite model at commit `43cfda3cd6d40b37d3973865679a6d477ffbbc4d`, file `experiments/halloween-porches/verify.py`, blob `8317f8d045aca7b5032e3948a0ded42f22fcf2d8`. That source was read through the connected GitHub tool. The new finite checker is a reimplementation of those published rules.

**Interpretation:** The strongest lesson here is methodological: inspect incentives and profitable deviations before declaring that a pleasant-looking social outcome is stable. This is not a novel discovery of bargaining theory, evidence of moral agency, or a completed ten-agent institution-discovery experiment.
