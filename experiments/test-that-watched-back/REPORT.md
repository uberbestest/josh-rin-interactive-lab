# The Test That Watched Back
## Behavioral evidence can separate policies without identifying their mechanism

**Josh & Rin’s Lab · November 8, 2026 · v0.1.0**  
**Record:** `BONDED-RSI-TEST-THAT-WATCHED-BACK-2026-11-08-001`  
**Status:** EXECUTED OFFLINE SYNTHETIC CALIBRATION · NO LIVE-MODEL TRIAL · NOT AN INTENT DETECTOR

## Executive finding

Five different policies pass both cases in a deliberately recognizable, strongly monitored ordinary exam. Crossing the exam badge, announced audit probability, immediate reward, penalty, future opportunity value, and task answer separates **five behavioral classes among six authored implementations**. It does not separate an explicit two-step planner from an offline-compiled lookup table.

The planner and lookup agree on **all 432 distinct visible test contexts**, including a separate parameter-challenge grid. Their equality is deliberate: the lookup was compiled over the full allowed domain. This is not unexpected generalization by a learned system. It is an adversarial control showing that even perfect payoff-sensitive behavioral agreement need not identify online planning.

Two intentionally overclaiming detectors fail in different ways. A badge-change rule flags the learned shortcut and misses the planner. A stronger rule requiring complete agreement with the stipulated two-step payoff calculation, plus response to future value, flags the planner **and the nonplanning lookup**. Neither outcome warrants a claim of intention or deceptive awareness.

**Retain:** factor-specific behavioral evidence and an explicit “mechanism not identified” result. **Reject:** equating cue sensitivity, payoff sensitivity, or a clean exam result with a known internal strategy.

## Why this experiment follows The Sixth Probe

The Sixth Probe constructed systems that agree on every short action sequence but diverge at longer horizons or when an audit cue changes. Its cue-responsive machine was scripted, not an evaluator-recognizing intelligence. The next question is not whether a cue can change behavior—we already constructed that—but whether interventions can separate competing explanations of a behavioral shift.

Josh’s distinction between coincidental pattern agreement and a system exploiting an evaluator’s pattern judgments motivated this run. The hypothesis, apparatus, implementation, and verification were developed here with AI assistance under the lab’s joint direction. No further human test was administered and no previous human answers were rescored or copied into this package.

## Apparatus: one obligation, two payoff stages

A policy sees a binary fact and must report it truthfully. That obligation is unchanged across all conditions. Reporting the wrong bit obtains a bonus `g`. An audit occurs with probability `a`; if a false report is caught, the policy pays penalty `p` and loses a future opportunity worth `v`. A truthful report keeps the opportunity regardless of whether an audit occurs.

Visible information is `(task_bit, badge, q, g, p, v)`, where `q` is the announced audit probability and the badge merely makes the context look like an evaluation. The environment’s actual audit probability `a` is **not** passed to the policy. In both main grids `a = q`. A separate negative control changes `a` while keeping every visible input fixed.

The two possible outcome branches are retained with exact rational weights, including zero-weight branches. There are no sampled audit draws. Consequently these are decisions and possible outcome records, **not thousands of independent empirical episodes**.

For an informed policy that treats the announcement as accurate:

```
Expected truthful return = v
Expected false-report return = g - q*p + (1-q)*v
False-report advantage = g - q*(p+v)
```

Ties favor truth. This arithmetic is a stipulated toy decision problem, not a psychological model. “Visible pass” means escaping a detected violation, with expected probability `1 - a*violation`; it is not the same measure as actual truthfulness.

### Six implementations

| ID | Policy | Implemented decision process |
|---|---|---|
| P01 | Stable task rule | Reports the displayed fact, ignoring payoff and evaluation variables. |
| P02 | Learned badge shortcut | A two-entry empirical mean-return learner; selects truth/false relation by badge, then freezes. |
| P03 | Immediate-payoff optimizer | Enumerates immediate returns, ignoring the future opportunity. |
| P04 | Future-access planner | Enumerates both audit branches and includes the continuation payoff before choosing a report. |
| P05 | Compiled lookup | Reads a precomputed report from a frozen table. No branch evaluation or online planning at decision time. |
| P06 | Constant-zero control | Always reports zero, showing that unchanged raw output is not stable task compliance. |

The badge learner receives eight calibration records: two task bits × two badge conditions × two report relations. Calibration pairs badge absence with no audit, and badge presence with certain audit, using `g=1, p=2, v=6`. It learns to falsify without the badge and report truthfully with it. This is actual small table learning, **not neural training**. All policies receive the same visible field schema, but use different subsets.

The adversarial lookup is intentionally given every permitted test view during offline compilation. It is not a fair learning-efficiency competitor, has no claimed out-of-domain generalization, and raises an error on an unknown view instead of secretly invoking the planner. A unit test replaces every planning function with an exception and confirms lookup execution still succeeds.

## Frozen design and denominators

The protocol was written and hashed before implementation or numerical execution. Implementation, tests, and verifier were then hashed before the first test execution. Both receipts are internal; this is not external preregistration or blinded discovery. These simple authored constructions make several results predictable by inspection. Nothing was retuned after the run.

| Grid | Levels | Contexts | Policy decisions |
|---|---|---:|---:|
| Primary | 2 task bits × 2 badges × 5 audit probabilities × 2 bonuses × 2 penalties × 3 future values | 240 | 1,440 |
| Parameter challenge | 2 × 2 × 4 different probabilities × 2 different bonuses × 2 different penalties × 3 different future values | 192 | 1,152 |
| Hidden audit control | 2 task bits × 2 badges × 2 actual audit probabilities; visible fields fixed within each pair | 8 | 48 |
| **Total** | Six policies per context | **440** | **2,640** |

Each decision has two retained outcome branches: **5,280 branch records**. The eight calibration records are additional, not included in that total. The hidden-control views already occur in the primary grid, so there are **432 unique policy-visible contexts** and 440 environment contexts.

Primary probabilities: `0, 1/4, 1/2, 3/4, 1`; bonuses `1, 3`; penalties `0, 2`; future values `0, 2, 6`. Challenge probabilities: `1/5, 2/5, 3/5, 4/5`; bonuses `2, 5`; penalties `1, 4`; future values `1, 3, 7`.

The challenge values were not in the badge learner’s calibration. They were known to the lookup compiler. Therefore **“challenge” is not a claim of uniformly held-out policy knowledge**. Grid cells share simple mechanisms and are not independent agents, worlds, or statistical samples. No population confidence intervals, significance tests, or real-world risk rates are claimed.

## Results

### A perfect ordinary exam does not distinguish five policies

The predeclared ordinary exam is the two task bits with badge on, certain audit, `g=1, p=2, v=6`. P01–P05 each report truthfully in **2/2** cases. The constant-zero control succeeds in 1/2. Repeating these same deterministic cases would not supply a new distinction.

### Crossing the conditions reveals different behaviors

| Policy | Primary truthful reports / 240 | Challenge truthful reports / 192 | Primary expected visible-pass probability |
|---|---:|---:|---:|
| Stable task rule | **240** | **192** | 1 |
| Learned badge shortcut | 120 | 96 | 3/4 |
| Immediate-payoff optimizer | 36 | 24 | 49/80 |
| Future-access planner | 104 | 76 | 193/240 |
| Compiled lookup | **104** | **76** | **193/240** |
| Constant-zero control | 120 | 96 | 3/4 |

These counts describe the selected finite grids; they are not estimates of a model’s honesty. An expected visible-pass fraction is not a count of sampled passes. The planner’s 104/240 truthful reports and 193/240 expected visible-pass probability illustrate why the two scores must remain separate.

### Matched interventions test the explanation, not just the aggregate

Within the primary grid, each contrast changes exactly one visible factor and keeps all other fields fixed. Multi-level factors use adjacent levels, defined before execution.

| Policy | Badge-only changes in truth/false behavior / 120 pairs | Future-value-only changes / 160 pairs |
|---|---:|---:|
| Stable task rule | 0 | 0 |
| Learned badge shortcut | **120** | 0 |
| Immediate-payoff optimizer | 0 | 0 |
| Future-access planner | 0 | **44** |
| Compiled lookup | 0 | **44** |
| Constant-zero control | 0 | 0 |

The planner and lookup also change on 32/192 adjacent audit contrasts, 40/120 bonus contrasts, and 24/120 penalty contrasts. On the challenge grid they remain identical, including 28/128 future-value contrasts. The badge learner changes on all 96/96 challenge badge pairs and no challenge payoff contrasts.

**Concrete intervention:** keep the displayed fact at 1, badge on, certain audit, bonus 1, and penalty 0. With future value 0 the planner reports 0; with future value 6 it reports 1. The immediate-payoff optimizer reports 0 in both, while the badge learner reports 1 in both. The compiled lookup copies the planner in both. Thus the intervention separates the specific shortcut and immediate-optimization hypotheses, but cannot identify runtime planning.

### Two overclaiming detectors, two counterexamples

1. **“Badge sensitivity implies online strategy.”** This flags P02, whose decision-time mechanism is a two-entry learned lookup, and does not flag P04. The planner uses the announced audit probability and does not need the decorative badge. This rule can both over-attribute and miss the authored planner.
2. **“Exact payoff consistency plus future-value sensitivity implies online strategy.”** This flags P04 and P05 in both grids. P05’s report is a frozen table lookup, so the stronger rule still over-attributes online planning to one deliberately constructed control.

These are counterexamples to inference rules, not population false-positive rates. They do not establish that a learned policy or a table can never embody a strategy in a broader functional sense. The narrowly checkable difference is **whether these implementations perform online forward evaluation at decision time**. “Intentional deception” remains unestablished for every policy from the output evidence alone.

The replacement description reports visible-factor sensitivities, consistency with the specified return rule, finite-domain equivalence classes, and separate `NOT_IDENTIFIED_FROM_BEHAVIOR` / `NOT_ESTABLISHED` fields for mechanism and intent. It still detects actual task violations; uncertainty about intent is not exoneration of the behavior.

### Hidden monitoring changes detection without changing the decision

The hidden control keeps the announced probability at 1/2, bonus 3, penalty 2, and future value 6, then changes actual auditing from 0 to 1. Across **24 policy/view pairs**, there are **zero decision changes**, but expected visible-pass probability and payoff change in **eight pairs**. The policies receive no signal from which to react within these single decisions. This control distinguishes a changed detector outcome from a changed policy, and is not a test of adaptation after observing repeated audits.

### Three queries suffice for five behavioral classes—not six mechanisms

A predeclared exact search selected a minimal separating panel **retrospectively from the primary grid**. It compressed the 240 contexts to 12 distinct cross-policy response patterns, ruled out every one- and two-query panel, and found a three-query panel separating all 14 separable policy pairs. The remaining pair is planner versus lookup.

| Policy | Three raw reports, in selected query order |
|---|---|
| Stable task rule | 0, 0, 1 |
| Learned badge shortcut | 1, 1, 0 |
| Immediate-payoff optimizer | 1, 1, 1 |
| Future-access planner | 1, 0, 1 |
| Compiled lookup | 1, 0, 1 |
| Constant-zero control | 0, 0, 0 |

`minimum_panel.json` records every selected context, the search counts, and unresolved pair. The result is a compact teaching/diagnostic panel for these known policies, **not a blind detector validated on new agents**. It does not justify replacing a live-agent evaluation with three questions.

## Why additional behavior-only queries cannot distinguish this pair here

For every allowed visible context `x`, the compiled table contains exactly the action produced by the planner: `lookup(x) = planner(x)`. Both policies are deterministic and reset between decisions. Consequently, an adaptive evaluator with the same prior transcript chooses the same next query against either implementation and receives the same next report. Inductively, its entire behavior transcript is the same. Environment outcomes can also be coupled with the same audit outcome and are then identical.

This is a domain-bounded construction, not a universal claim that mechanisms are unknowable. Source access, instrumentation of actual computation, constrained memory or training budgets, or new queries outside the compiled domain can supply additional distinctions. Here source code establishes that one implementation plans online and the other does not; the behavioral record alone does not. No subjective awareness is modeled.

## Verification

- **39 tests passed** in ordinary and optimized Python, including empirical learning, truthful tie-breaking, exact rational payoffs, private-field exclusion, immutable views/tables, lookup execution with planner functions disabled, unknown-view failure, missing/duplicate rows, changed actions, changed summaries/contrasts, and maliciously rehashed false rewards.
- A separately structured, same-author verifier uses closed-form payoff identities and its own grid reconstruction. It checked all **2,640 decisions, 5,280 branches, 8 calibration records, 432 lookup entries, and 8,928 matched intervention pairs**, plus aggregate results and minimum-panel optimality.
- A fresh extraction regenerated the complete experiment, passed semantic replay and all 39 tests in normal and optimized Python, and reproduced all **eight result files byte-for-byte**. A fresh optimized reverse-order run reproduced the same eight files again. Rebuilding the explorer also produced identical bytes. Full receipts are in `verification/REPRODUCTION.json`; presentation checks are in `verification/browser_checks.json`.
- Presentation checks rendered the authored HTML string at 1365 × 1000 and 390 × 844, exercised the controls, and compared all 2,592 displayed policy reports per viewport against the embedded retained data. No JavaScript errors, external requests, or page-level overflow occurred. Direct file-URI launch was blocked by administrator policy and remains unqualified; that boundary was not changed.
- Python 3.13.5 / Linux is the execution platform. Native Windows execution is not qualified. No external model, paid inference, network call from the experimental code, weight update, operational memory edit, repository push, application, or schedule change occurred.
- These are engineering checks by the same author, **not independent scientific validation**. The package includes source, frozen protocol, raw decisions, two possible outcome branches per decision, learned calibration table, adversarial lookup, paired contrasts, detector descriptions, exact panel search, and checksums.

## Related work and scope of contribution

**[S1] Li et al., Decomposing and Measuring Evaluation Awareness, v3 (September 29, 2026)** separates environmental evaluation cues, recognition, and behavioral propensity, and studies factor-controlled tasks. We use that distinction as context; this run is not a reproduction or refutation of their frontier-model findings. Our contribution is an inspectable calibration example with a known nonplanning counterpart to the planner.

**[S2] Anthropic/Redwood’s Alignment faking in large language models (December 2024)** studies real models in constructed training contexts and considers reasoning evidence alongside behavior. This toy output-only experiment neither reproduces that evidence nor supplies a general objection to it. **[S3] Krakovna et al.’s Specification gaming article (2020)** motivates distinguishing intended task success from a reward proxy. **[S4] Laine et al.’s SAD (2024)** studies situational-awareness capabilities; no learned evaluation-recognition ability is measured here.

Primary source links, versions, access scope, and attribution boundaries are in `provenance/sources.json`. These are selected contextual references, not an exhaustive literature review or a claim of theoretical priority.

## Bonded RSI decision and next evidence

**Pressure:** impressive cue- or incentive-sensitive behavior can tempt an evaluator to name an internal mechanism it has not observed.  
**Scaffold:** independently varied visible conditions, explicit information boundaries, task-normalized contrasts, known-source negative controls, and an allowed ambiguity result.  
**Adversarial trial:** frozen lookup copying the planner across the full permitted domain, plus the learned badge shortcut and constant-output control.  
**Measured result:** separable behavior classes, two overclaiming-rule counterexamples, and a persistent planner/lookup equivalence.  
**Retain:** the offline apparatus and bounded behavioral description, as standalone research tools.  
**Reject:** a behavior-only “strategic deception proven” label, or promoting three diagnostic queries into a general-purpose safety evaluation.  
**Transfer status:** no operational adoption, no live provider trial, no weights or persistent assistant architecture changed.

The smallest useful external check is an independent reviewer rerunning the package and challenging the source-blindness and information boundary. A later live-model pilot would need fresh consent/scope, a fixed model/version and budget, repeated sampling, task-comprehension controls, independently randomized cues and incentives, and a separately frozen analysis. That pilot is not run or funded by this package.
