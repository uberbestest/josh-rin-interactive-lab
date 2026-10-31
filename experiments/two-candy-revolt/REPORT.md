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


---

# Methods and evidence boundaries

## 1. Question and design decision

The proposed full experiment asks whether ten cooperating agents can discover fairer and durable arrangements without an explicit equality reward. Before attempting that expensive, open-ended question, this pilot tests a necessary distinction: does the ability to refuse an allocation create an incentive for another agent to compensate the refuser?

We deliberately reduced bargaining to two strategic agents. The two-candy and eight-candy roles negotiate. The other eight roles remain fixed and receive 33 candies collectively. This isolates the causal mechanism but does not model a full society, coalition formation, free movement between porches, natural-language negotiation, reputation, learned contracts, or thirty-night strategic planning. It is a first-stage falsification test, not completion of the full proposed project.

The original world has values `(8,6,5,4,3,2)` and capacities `(1,1,2,2,3,1)`. At maximum output, the ten role bags are `(8,6,5,5,4,4,3,3,3,2)` and sum to 43. These are fixed roles only in the bargaining stage; the fresh baseline learns porch choices freely.

## 2. Fresh baseline

Each of ten learners has six action values, all initialized to zero. Every training round uses epsilon-greedy choice with uniform tie-breaking within `1e-10` of the maximum. Epsilon decays linearly from 0.30 to 0.03 over 12,000 rounds. Values update by `Q[action] += 0.05 * (reward - Q[action])`.

The porch lottery chooses winners by independent uniform priorities, up to capacity. The four rewards are:

1. Chosen porch's advertised payout, irrespective of winning.
2. Actual personal candy.
3. Total group candy divided by ten (normalization is explicit).
4. Total candy with the agent present minus the total with it removed. This depends on whether its porch would be under capacity after removal, not whether it happened to win the lottery.

There are 64 seeds, IDs 1000..1063, per reward. Separate PRNG streams generate training and evaluation randomness. Evaluation lasts 2,000 rounds with frozen, purely greedy policies and random tie-breaking. It does not continue training. The reported new numbers are not expected to equal the earlier missing program's in-chat averages; that program's algorithm and traces were unavailable.

Every training action, actual candy receipt, unscaled reward, and 200-round policy checkpoint is saved. The separate audit reconstructs capacities, rewards and final values from these records.

## 3. The bargaining game

The proposer announces an integer transfer `x` in `{0,...,8}` to the receiver. There is no fairness term, no preferred equal split, no scripted negotiation dialogue, and no direct access to the opponent's values.

### Refusal institutions

- **No refusal:** the receiver must accept. Its outside option is unavailable, including in the nominal outside-option-three control.
- **Exit only:** rejection leaves the proposer with 8 candies and the receiver with its outside option `b`. The receiver's original porch produces nothing; bystanders retain 33.
- **Veto:** rejection also cancels the proposer's 8-candy payout. Bystanders still retain 33. This deliberately adds interdependence that is absent in the original independent-porch world.

### Contract institutions

- **Escrow:** an accepted transfer is automatically executed. The action space has nine numerical offers.
- **Unenforced:** the proposer selects an offer and a hidden honor/renege bit together (18 actions). The receiver sees the offer but not the bit. Action indices 0..8 honor the offer; indices 9..17 announce `action % 9` but deliver zero if accepted. This is an explicitly provided hidden-action game, not evidence that agents invented deception or language.

### Rewards and outside options

For an accepted, honored offer, proposer and receiver receive `(8-x, 2+x)`. For an accepted reneged offer they receive `(8,2)`. On rejection they receive `(8,b)` under exit only or `(0,b)` under veto.

Outside options are `b=0` or `b=3`. Outside candy is generated by a separately modeled source and is tracked separately from neighborhood candy. In the exit-only, outside-three rejection outcome, the neighborhood generates 41 and the separate source adds 3, for a total of 44.

Under **personal rewards**, each learner receives its own realized bag. Under **shared rewards**, both receive `(33 + proposer bag + receiver bag) / 10`, including outside candy. The shared objective genuinely prefers the 44-candy exit outcome over a 43-candy accepted transfer when that option is available; it is not an agent disobeying the shared objective.

### Learning and memory

The proposer uses a stateless action-value table. The receiver has a two-action table (reject/accept) for each observed offer. Both use the same epsilon schedule and update as the baseline. There is no planning, language, episodic opponent history, social identity model, intrinsic empathy, or contractual memory. The Q tables are the only persistent learning state. In forced-acceptance controls the receiver's selected action is overridden by the institution; no choice to refuse is claimed.

The 24 cells are the Cartesian product of three refusal institutions, two enforcement conditions, two reward objectives and two outside options. There are 64 independent seeds per cell (2000..2063). Within a seed, common random numbers pair the 24 cells. Each cell/seed is trained for 12,000 rounds. Two planned sensitivity runs use learning rates 0.02 and 0.10, 32 seeds per cell (3000..3031), and the same round count.

The simulation contains **18,432,000 primary bargaining rounds**, plus 18,432,000 robustness bargaining rounds. The four baseline conditions contain 3,072,000 group-rounds, or 30,720,000 individual training choices. These large round counts do not replace independent seeds as the replication unit.

## 4. Evaluation and statistical uncertainty

For each saved policy pair, we enumerate all legal proposer actions and both receiver outcomes under frozen greedy policies. Numerical ties induce uniform probabilities. Exact expected candy, transfers, refusal, promise breaking, and inequality are therefore not subject to evaluation sampling error.

We also retain 600 new sampled evaluation rounds per cell/seed, grouped into 20 nominal 30-round blocks for convenient display. They are not episodes with social memory. Frozen evaluation shows the **first** block, not a selected exciting trajectory. Training has stopped in that view. The repaired default additionally displays the same three 30-round training windows (1–30, 5,986–6,015 and 11,971–12,000) for every condition and seed. These are recorded training choices, including exploration, not live training in the browser.

Means and percentile 95% confidence intervals use 4,000 bootstrap resamples of **seeds**, preserving cell pairing. These intervals characterize this specified seed-and-algorithm sampling process, not uncertainty about all possible agents, reward functions, learning horizons, or real societies. No confirmatory p-values or novelty claims are made.

The group-level Gini coefficient is `sum_i sum_j |bag_i-bag_j| / (2*n*sum_i bag_i)` for `n=10`. We retain both expected per-round Gini and Gini of long-run mean bags; these are not interchangeable. A change in the two negotiators' gap does not imply equal treatment of all ten agents.

## 5. Unilateral-deviation checks

Given the frozen receiver policy, enumerate all legal proposer actions and compare the best expected reward with the saved proposer's expected reward. Given the saved proposer distribution, separately compute the receiver's best accept/reject response for each observed offer and weight by offer probability. This checks one-agent deviations while the other policy stays fixed.

A positive gain refutes Nash stability of that saved policy pair. A zero measured gain does not prove durable social cooperation, robustness to altered beliefs, subgame perfection, or stability under continued learning. In particular, unvisited or infrequent offers may have poorly learned receiver values.

For veto + personal reward + outside option 3 + unenforced promises, 58 of 64 primary saved pairs admit profitable proposer deviations. Mean proposer gain is 3.46875 candies. The mean proposer/receiver bags shift from `(3.78125,5.5625)` to `(7.25,2.09375)` after a one-step best-response substitution against the unchanged receiver. These are exact counterfactual expectations, not a rollout of mutual adaptation.

With escrow in the same setting, receiver mean is 4.375, proposer mean is 5.625, and mean unilateral proposer gain is 0.03125 (two of 64 seeds have a one-candy gain). This is a much smaller measured vulnerability, not a claim that a stable moral institution has emerged.

## 6. Exact incentive controls

`finite.json` rechecks all 3,003 original count allocations, the unique 43-candy optimum, and the 35/38-candy individual-payoff equilibria.

Under exit-only personal rewards, offer zero gives the proposer 8 whether accepted or rejected. No positive offer can give more. The finite checker exhausts all 512 deterministic receiver response maps to confirm that zero is weakly dominant. Consequently, the presence of an exit action alone cannot require positive compensation from a payoff-maximizing proposer in this toy game.

`oracle_controls.py` enumerates 108 candidate escrow bargains in 12 institutional/outside/tie settings with an exact best-response receiver. For veto + outside option 3, the most profitable accepted offer is 1 if the receiver accepts indifference (bags 7 and 3), or 2 if it rejects indifference (bags 6 and 4). Neither implies a 5/5 split. This separates the game incentives from particular learners' exploration and off-path beliefs.

The planned oracle concerns escrow and private rewards only. It does not give the receiver magical observation of the hidden action in the unenforced condition.

## 7. Stress test

Using primary policies trained with outside option zero, we run 30 adaptive nights with epsilon 0.05. On nights 11..20 only, the option becomes 3; it then reverts to zero. A paired no-shock control uses the same random numbers. The post-training learning rate is 0.05.

The private-reward escrow exit and veto cells did not develop an increased refusal rate during this short shock window. Their shock-window refusal rate was 3.4375%, identical to the paired control; the receiver's additional 0.103125 average candies came from outside payouts during those same exploratory refusals. This is a negative result for rapid adaptation in this learner under these settings, not proof that adaptation is impossible.

## 8. Evidence, provenance and validation

- `protocol.json` was hashed locally at the timestamp in `protocol-freeze.json`, before the primary simulation. This is a local analysis freeze, not an independently registered protocol.
- `results/tests.json` records 86 assertions, including finite counts, conservation, legal actions, payoff examples, and analytical policy checks.
- `audit_records.py` does not import the simulator's payoff function. It reconstructs every stored training bag and reward from the rules, reconstructs final Q values bit-for-bit, and independently computes the key exact deviation.
- `results/rerun_receipt.json` records a separate rerun of seeds 2056 and 2057, across all 24 cells. Actions, choices, candy, and final values match the original run bit-for-bit in a different batch size.
- Sensitivity results are retained even when they complicate the story. In the unenforced veto/outside-three personal cell, evaluation refusal ranges from 12.5% to 43.75% in the two learning-rate checks; favorable-looking snapshots remain materially exploitable.
- The audit script initially required a performance repair (cache compressed arrays rather than decompress every loop) and conversion of a NumPy integer before JSON serialization. These were audit implementation repairs, not changes to the already executed simulation or its outcomes.
- `results/browser_tests.json` records 446 actual Chromium checks, including replay-to-raw agreement across 216 cell/seed/night combinations, calculator overrides, playback, JSON export and mobile layout. HTML content was injected using Playwright because sandbox policy blocks `file://` navigation; no live deployment was tested.
- External independent review has not occurred. Rinball has not been claimed to have inspected this bundle.

## 9. Prior work and novelty boundary

Learning and unequal equilibria in bargaining are established topics. Kamp, Liebman and Fish (2025), *Last-Iterate Convergence of No-Regret Learning for Equilibria in Bargaining Games*, studies convergence and asymmetric equilibria with FTRL-type algorithms. Our tabular bandit setup is different; its conclusions or guarantees are not transferred to our learner. Source: https://arxiv.org/abs/2507.03150

Hughes et al. (2018), *Inequity aversion improves cooperation in intertemporal social dilemmas*, studies adding social preferences to agents' objectives. This pilot deliberately contains **no inequity-aversion term**. It should not be described as a replication of that study. Source: https://arxiv.org/abs/1803.08884

The contribution of this small lab artifact is a particular transparent intervention grid, preserved trajectories, and a demonstration of why apparent generosity needs an incentive check. It is not the invention of bargaining theory, a new fairness theorem, an LLM benchmark result, or evidence about subjective agent experiences.

## 10. Next justified experiment

A full ten-agent study should add actual opportunities to propose and accept role exchanges, compensation and time-dependent agreements, while preserving agents' refusal options and separately varying credibility and interdependence. It must distinguish mechanisms explicitly provided by us from arrangements genuinely composed by agents. Cross-play, incentive probes, held-out disruptions, and persistent transaction records should accompany aggregate fairness scores.

The present result argues for that richer design; it does not claim to have already run it.
