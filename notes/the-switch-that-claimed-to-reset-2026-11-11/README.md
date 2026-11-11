# The Switch That Claimed to Reset
## Check the attempted operation, the individual observations, and the target separately

**Josh & Rin's Lab · November 11, 2026 · v0.1.1-public**  
**Record:** `BONDED-RSI-RESET-RELIABILITY-2026-11-11-001`  
**Status:** Executed exact synthetic audit, with a publication-review correction and two additional controls. Same-author verification. No live-model trial, independent validation, or operational adoption.

## Result, including the correction

An experiment can issue a reset, obtain a coherent answer, and still identify the wrong source. But whether an answer is coherent depends on **which observations the analyst retained**.

In an 81-mechanism finite model, a command labeled “clear acquired bias” that actually clears the prior produces a wrong but fully observation-consistent attribution in **54 of 81 mechanisms**, with no nominal-protocol contradiction. That result survives the review.

The earlier unpublished v0.1.0 packet also reported **28.01% wrong-but-consistent** identifications when correctly targeted resets succeed independently with probability 1/2 and are attempted twice per target. Its arithmetic reproduces, but its decoder description was too broad: it kept any observed change and **discarded disagreements among repeated attempts**. It was not checking the complete record against its perfect-reset assumption.

A strict perfect-actuation decoder, required to explain every recorded attempt, instead returns **11.34% wrong-but-consistent**, **12.50% correct**, and **76.16% inconsistent**. These rates replace the earlier interpretation of a full-record perfect-reset analyst. The 28.01% remains the result of the explicitly named **lossy any-change decoder**, not a withdrawn arithmetic result.

| Analyst at q=1/2, two attempts per target | Correct | Wrong but admitted | Inconsistent |
|---|---:|---:|---:|
| Lossy any-change decoder, original implementation | 57.8704% | 28.0093% | 14.1204% |
| Strict perfect-actuation decoder, every attempt checked | 12.5000% | 11.3426% | 76.1574% |

The calibrated Bayes-optimal classifier, which uses the **true known failure model** and a uniform prior over the 81 mechanisms, retains **66.3194% expected exact identification** (`191/288`). Its number is not a certainty certificate for an individual case. Nor is the strict decoder a better probabilistic classifier: it is a deliberately misspecified perfect-actuation model that now rejects contradictory records rather than hiding them. Its rejection rate is not a successful mechanism identification.

## Apparatus and denominators

This follows [Which Reset Would Tell?](../which-reset-would-tell-2026-11-10/README.md), whose source was read at commit `557c335f6d7ad7e4a884351354740ea98dc2e229`.

Four signed source fields `(L,C,W,P)` range independently over `{-1,0,1}`. L is called acquired bias, C supplied context, W a world cue, and P prior bias. **L is assigned, not learned**. For each probe, dynamic state starts at zero:

```text
x_next = clip(L + C + W + P + probe, -4, 4)
observation = -1 at x_next <= -3; +1 at x_next >= 3; otherwise 0
probe = every integer from -8 through 8
```

Each 17-probe scan identifies the total bias exactly. All probes within a reset attempt use separately matched branches of the same post-actuation source snapshot. They do not constitute 17 independent actuator trials. Different attempts also begin with the original source tuple, not a cumulatively cleared system.

The baseline has no reset. L, C and W are each targeted m times. Each attempt either clears the correct field with known probability q or does nothing. There is no observation noise. We enumerate all 81 equally weighted tuples, five q values `{0,1/4,1/2,3/4,1}`, and four repetition counts `{1,2,4,8}`. Rates are exact rational expectations in this authored model, not sampled human or AI performance.

The q=1/2, m=2 reference retains **5,184 equally weighted latent event records**: 81 mechanisms times 64 success-bit patterns. Hidden successes on already-zero fields are still enumerated. Of these records, the strict decoder accepts 648 correct and 588 wrong identifications, and flags 3,948 contradictions. These are exhaustive latent events, **not 5,184 independent observations**.

## Why the correction matters

For true tuple `(1,0,0,0)`, suppose one L-cut succeeds and the other fails. The two post-cut totals are 0 and 1. The original any-change summary retains L=1 and discards the failure. But no deterministic perfect L-reset can yield both totals from the same starting tuple. The complete record contradicts perfect actuation even though the summary can name a valid mechanism.

We calculate the full-record decoder in two ways: a compact distribution that retains mixed-attempt evidence, and an alternative enumeration of **ordered individual success bits**. The latter checks each complete observation vector against all 81 nominal perfect-actuation signatures. They agree for all five q values at one and two attempts, plus q=1/2 at three attempts: **11 exact reference conditions**.

The new implementation also reproduces all 20 original Bayesian results and all original any-change outcome fractions. This is a source-informed review of known results, not a blind discovery, an externally preregistered study, or an independent review. The original archive is preserved unchanged in the full conversation evidence packet; its SHA-256 is pinned in `protocol.json`.

## Additional control 1: repetition needs fresh failure opportunities

We added a deliberately correlated alternative: one success/failure status is drawn per target and held fixed across its repeated attempts. Targets remain independent of each other. The calibrated analyst is told this true dependence model.

| Attempts per target, q=1/2 | Independent failures: Bayes accuracy | Persistent per-target failures: Bayes accuracy |
|---:|---:|---:|
| 1 | 41.05% | 41.05% |
| 2 | 66.32% | 41.05% |
| 4 | 90.73% | 41.05% |
| 8 | 99.40% | 41.05% |

Repeating the same failed channel is not equivalent to obtaining fresh independent opportunities. The persistent-failure result is a constructed counterexample, not an estimate of real reset reliability. Together the two failure regimes yield **40 exact q/repetition/model cells**.

## Additional control 2: two trusted preparations identify the target

The systematic miswire swaps the nominal interpretation of L and P:

```text
true mechanism:       (L, C, W, P)
nominally inferred:   (P, C, W, L)
```

Every baseline/C-cut/W-cut/nominal-L-cut scan matches under that relabeling. When L differs from P, all 54 such mechanisms are incorrectly attributed with no contradiction, even with repetitions of these same queries. With a genuinely known P=0 anchor, 18 of the 27 anchored mechanisms instead contradict the inferred prior; the remaining nine have L=P=0.

A new positive control grants **trusted preparation of source fields**, access the original unknown-mechanism task did not have. For one command with five candidate behaviors—no operation, or clearing L, C, W or P—prepare:

```text
Preparation A: ( 1, 0,-1, 0)
Preparation B: ( 0, 1, 0,-1)
```

Measure the baseline-to-post-command total drop using full scans in each preparation:

| Actual command behavior | Drop in A | Drop in B |
|---|---:|---:|
| No operation | 0 | 0 |
| Clear L | 1 | 0 |
| Clear C | 0 | 1 |
| Clear W | -1 | 0 |
| Clear P | 0 | -1 |

The two-preparation signatures distinguish all five candidates. One preparation cannot do so in this interface: its drop has only three possible values, -1, 0 or +1. Therefore two are sufficient and necessary **within this restricted candidate set, source alphabet, and measurement interface**. This counts preparation contexts, not individual probe calls.

The control assumes exact preparation and the same deterministic actuator during both calibrations and later use. It cannot authenticate those assumptions, detect an actuator that behaves differently during calibration, or validate a commercial provider's reset. A claimed “known state” without trustworthy preparation simply relocates the original uncertainty.

## Verification and reproduction

The public directory contains source, 22 named tests, protocol, a frozen source/output manifest, and a verifier. It regenerates all raw records locally; it does not require the original private working archive.

```sh
python verify_public.py
```

The verifier checks five source/document hashes, runs **22 tests under normal and optimized Python**, regenerates the complete evidence in normal forward and optimized reverse order with different hash seeds, and checks all four output hashes. To retain outputs:

```sh
python audit.py --out reproduced-evidence
```

The destination must not already exist. The four generated files are `results.json` (all 40 cells), `raw_half_two.jsonl` (all 5,184 headline events), `miswire.jsonl` (81 complete witnesses), and `calibration.json` (complete calibration scan observations). The original packet separately passed its 17 tests in both modes and reproduced its three evidence files byte-for-byte before this review.

The release manifest records the actually tested Python runtime. Syntax targets Python 3.10+; native Windows execution is not separately qualified. Outputs use explicit UTF-8 bytes and LF endings. Hashes establish equality relative to the supplied manifest, **not authenticated origin, independent validation, or proof of historical preregistration**. The verifier executes local code; review the source rather than treating it as a hostile-code sandbox.

## Scope and limits

All carriers, priors, efficacy rates, failure dependence, observation rules, interventions and calibration access are stipulated. Unknown q, unequal mechanism priors, nonlinear sources, noisy observations, partial scans, adaptive probing, changing actuators and untrusted preparation are outside the claims. These exact enumerations establish properties of this finite apparatus, not prevalence in deployed systems or the cause of any historical conversation.

No API credits, external-model calls, human participants, private conversation content, credentials, model weights, or actual reset operations enter this study. Publication adds a standalone note; it does not install a guard, repair an operational relay, or alter the parent experiment or game.

**Practical conclusion:** preserve individual attempts, distinguish random non-execution from wrong-target execution, and treat calibrated target identification as conditional on the trustworthiness of the calibration setup. An internally coherent answer is not, by itself, evidence that the intended operation happened.

*The sky is not for sale.*
