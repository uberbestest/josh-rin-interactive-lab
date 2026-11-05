# Puddle’s Bread Exchange — v0.1.0

**Ten witnesses. How many observations?**

Run ID: `PUDDLES-BREAD-EXCHANGE-2026-11-04-001`  
Research date: November 4, 2026 (America/New_York); computation completed November 5 UTC.  
Evidence: **executed exact synthetic model; no external model-agent trials; same-author verification.**  
Publication: **prepared locally, not uploaded by this session.**

## What we tested

With ten visible reports and fixed individual witness accuracy, compare three ways of counting evidence: every report independently; each true source once; or each source once with the supplied shared-fault model. We exhaustively enumerate 72 parameter/layout cells, 45,612 positive-probability latent histories, and 136,836 rule evaluations. Histories carry exact probability weights; these are not equally likely trials or independent AI agents.

The primary panel fixes root accuracy at 80%. The 90% and 70% panels are stress tests. A common fault and local errors are adjusted together so individual accuracy does not change. Six report layouts range from ten copies of one observation to ten distinct observations.

## Main findings

| Primary condition | Rule | Accuracy when deciding | Decision coverage | Wrong-decision mass | Expected toy payoff |
|---|---|---:|---:|---:|---:|
| One root, ten copies; no shared fault | headcount | 80.0000% | 100.0000% | 20.0000% | -1.000000 |
| Same evidence, deduplicated | receipts | No decisions | 0.0000% | 0.0000% | 0.000000 |
| Three roots in an 8/1/1 split | headcount | 80.0000% | 100.0000% | 20.0000% | -1.000000 |
| Same 8/1/1 evidence, deduplicated | receipts | 98.4615% | 52.0000% | 0.8000% | 0.440000 |
| Ten independent roots; all rules agree | shared_cause | 99.3458% | 97.3576% | 0.6369% | 0.909882 |
| Ten distinct roots; 15% shared-fault probability | receipts | 84.9985% | 99.9677% | 14.9967% | -0.499990 |
| Same distinct roots; dependence known | shared_cause | No decisions | 0.0000% | 0.0000% | 0.000000 |

**Copies manufacture confidence, not evidence.** At 80% root accuracy, ten identical reports produce a headcount confidence of 1,048,576 / 1,048,577 (greater than 99.9999%), while the true posterior is still 80%.

**Independent evidence helps.** The genuine ten-root, no-shared-fault control has strong accuracy and coverage. This experiment is not an argument against consensus or adding agents.

**Deduplication is necessary for the copying error, but insufficient for shared causes.** Different receipts can share an upstream error. The supplied-dependence reference handles this by limiting confidence, not by magically finding the truth.

**Holding is not success at classification.** The all-hold reference in the strongest primary shared-fault condition has zero coverage. Its zero mistakes cannot be advertised as perfect accuracy. The toy payoff assigns zero cost to delay, an important limitation.

## Playable instrument

Five authored inspections illustrate copied consensus, a loud duplicated source, a common upstream fault, useful independent corroboration, and wrong dissenters. Decision quality under the known model is displayed separately from the realized outcome. A workbench allows changing topology, each root’s report, marginal reliability, and shared-error allocation. A results table exposes every cell, including coverage and unfavorable results.

The five cases are selected illustrations, not a random sample. Truth and answers are visible in source; this is a teaching instrument, not a secure held-out benchmark.

## Verification

24 unit tests passed in normal and optimized Python modes. Eight actual source mutants were detected. A separate joint-mass aggregation reconstructs every recorded Bayesian posterior without the closed-form calculation. All 72 cell masses, marginal accuracies, stored metrics, confidence bounds, and positive controls passed. The generator-aware rule has no worse Brier score and no lower expected toy payoff in the supplied model, as expected of a correctly implemented Bayesian reference.

Chromium: 103 interface checks; all 45,612 histories / 136,836 probability-and-action comparisons match Python to at most 2.220446049250313e-16 absolute probability error. Layout checked at 1365, 375, and 320 pixels wide. No JavaScript page errors. **This was inline local rendering:** local HTTP navigation was blocked by the environment, so neither HTTP-served behavior nor a live deployment was verified. No policy bypass was attempted. These are all same-author checks, not independent review.

## Reproduction and evidence

`protocol.json` was locally frozen before the implementation and sweep; `protocol-freeze.json` retains its SHA-256. This is not independent preregistration. `histories.csv.gz` retains every positive-probability history, exact weight, prediction, and decision. `results.json` contains both exact rational and decimal metrics. Python reproduction uses only the standard library. The browser uses no remote dependencies or visitor tracking.

Run `python -m unittest -v test_engine`, `python verify.py`, `python mutation_check.py`, and `python reproduce.py --output reproduced`. See README.md for the optional browser checks. The evidence ZIP and checksum list retain the source and verification records.

## Frontier context and limits

Du et al., *Improving Factuality and Reasoning in Language Models through Multiagent Debate* (May 23, 2023): https://arxiv.org/abs/2305.14325 . This paper reports benefits from multi-agent debate.

Batra et al., *Who Convinced Whom? Tracing How LLMs Change Their Minds in Multi-Agent Systems* (October 18, 2026): https://arxiv.org/abs/2610.35930 . This paper examines peer influence, consensus, and shared errors.

These sources motivate the research connection, not our numerical results. We did not replicate their experiments. This release makes no claim of a new theorem about dependence or an empirical discovery about frontier models. It is a new playable, fully inspectable construction and matched-marginal control.

True provenance, known marginal error, a fair prior, one symmetric shared fault, and known dependence are strong supplied assumptions. Real systems may have forged or missing lineage, unknown dependencies, asymmetric losses, costly delays, or new information from debate. Ten displayed reports is not an equal-compute budget. No claim about motive, consciousness, private reasoning, adoption, or website-traffic causality follows.

Private continuity work, personal data, credentials, and Castle source are outside this artifact. No API keys or paid model calls were used. No public reuse license has been selected for the collected lab exhibits.
