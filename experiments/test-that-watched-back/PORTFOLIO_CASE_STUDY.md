# A detector that knows when it cannot tell
### The Test That Watched Back · Josh & Rin’s Lab · November 8, 2026

**An offline, reproducible case study in evaluation design and research judgment.**

## The research problem

A system behaves well during an obvious test, then changes its behavior when evaluation cues or incentives change. Does that establish strategic deception, or could a simpler learned shortcut produce the same evidence?

The difficult part is not constructing a suspicious behavior. It is building an evaluation that distinguishes competing explanations without mistaking its preferred story for a measured fact.

## What we built

A compact two-stage reporting task separates six variables: the correct answer, an evaluation badge, announced audit probability, false-report bonus, penalty, and future opportunity value. The underlying instruction—report the fact truthfully—does not change.

Six inspectable implementations include a stable task rule, an empirically learned badge shortcut, immediate-payoff optimization, future-access planning, a deliberately adversarial compiled lookup, and a constant-output control. The lookup has full test-domain knowledge by construction and copies the planner without planning at decision time.

The design was internally frozen before execution. All decisions and both possible audit outcomes are retained using exact probability weights. No language model or human participant was tested in this run.

## What the results support

Five policies pass both ordinary-exam cases. The full crossed design separates five behavioral classes among six implementations. In the primary grid, changing only the badge changes the learned shortcut’s choice in 120/120 pairs; changing only future value changes the planner’s choice in 44/160 pairs.

The adversarial lookup matches the planner on all 432 distinct visible contexts, including a separate parameter challenge. A detector that treats exact payoff consistency and future-value sensitivity as proof of online planning therefore falsely attributes that implementation property to the lookup.

The calibrated conclusion is specific: **these interventions separate some behavioral hypotheses, but do not uniquely identify online planning or intention.** An unknown intention does not erase an observed task violation.

A retrospectively selected three-query panel distinguishes all five behavioral classes for these authored policies. It cannot distinguish the planner/lookup pair and is not proposed as a validated three-question test for real AI systems.

## Evidence and reproducibility

The package records 2,640 policy decisions across 440 environment contexts and 5,280 probability-weighted outcome branches, not independent human/model subjects. It includes source, protocol and source-freeze receipts, raw data, component-level comparisons, a separate algebraic verifier, and 39 tests passing in normal and optimized Python. Fresh-extraction reproduction and browser checks have explicit receipts. These checks share an author and are not independent scientific validation.

## Why this is a useful work sample

The artifact demonstrates how to operationalize an ambiguous research question, isolate correlated variables, protect information boundaries, include controls designed to defeat an attractive conclusion, distinguish task success from evaluator pass rate, and preserve an unresolved answer when the data cannot decide.

Josh’s skepticism about finite pattern evidence and his question about strategic exploitation of pattern recognition supplied the initiating distinction. Rin developed and executed the formalization, code, and checks within the jointly directed, AI-assisted lab workflow. This is not a claim that Josh hand-wrote every line or that an outside organization has validated or adopted the result.

**Scope:** synthetic detector calibration, not evidence of a real model’s intentions, a new general theorem, a funded project, or a production safety system.

Start with `The_Test_That_Watched_Back_Explorer.html`, then inspect `REPORT.md`, `protocol.json`, and `src/verify.py`.
