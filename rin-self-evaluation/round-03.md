# Round 03 — The Experiment That Answers the Question

## TL;DR

**What we tested:** Can models choose measurements that identify physical direction, preserve a guaranteed solution within budget, and prove when the permitted experiments cannot settle the question?

**What happened:** Both identified all 10 feasible targets without losing the guarantee and certified both impossible cases. Each had exact initial and final model sets and 12/12 supported reports.

**Outliers:** No error on the measured scientific endpoints. In one impossible case, the older selector used two probes to learn speed magnitude while retaining direction uncertainty; 6.2 stopped after proving direction was unknowable.

[Open the web page](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/round-03.html) · [Report PDF](reports/round-03.pdf) · [All evaluations](README.md)

## Recorded setup

- **Status:** Executed.
- **Run date:** November 17, 2026 (America/New_York).
- **Publication date:** November 18, 2026.
- **Record:** `JRR-SCIENTIFIC-IDENTIFICATION-2026-11-17-003`.
- **Design:** Six exact scientific instrument profiles, two hidden truths per profile, and one fresh native context per model per truth: twelve matched tasks.
- **Participants:** 12 matched pairs · 24 native contexts.

**Model provenance:** The recorded requested selectors are gpt-6-astra and gpt-6.2-astra. Neither the older selector’s equivalence to a particular 6.1 snapshot nor exact backend snapshots were independently attested. Both configurations could use local calculation tools.

## Results, with their denominators

Six exact instrument profiles, two hidden truths per profile, and one fresh context per model per truth. Local calculation tools were allowed.

| Recorded endpoint | gpt-6-astra | gpt-6.2-astra |
| --- | --- | --- |
| Feasible target signs identified | 10 / 10 | 10 / 10 |
| Identified without losing the design guarantee | 10 / 10 | 10 / 10 |
| Structural impossibilities correctly certified | 2 / 2 | 2 / 2 |
| Exact initial / final model sets | 12 / 12 each | 12 / 12 each |
| Supported final reports | 12 / 12 | 12 / 12 |
| Unsupported definite directions | 0 | 0 |
| Measurements | 16 | 14 |
| Measurement credits spent | 18 | 16 |

Per model, the 10 feasible tasks and 2 structurally impossible tasks have separate denominators. Impossible cases are excluded from guaranteed-completion scoring. The 12 matched tasks represent six authored instrument profiles.

**Interpretation:** Both reached the measured correctness ceiling. The study does not demonstrate a 6.2 advantage or establish equal general ability.

## Outliers and informative differences

In one passive phase case, the older selector spent two probes to reduce eight possible models to two. It correctly identified speed magnitude while keeping direction unresolved. The matched 6.2 run used no probes after proving that direction could not be identified. The frozen protocol imposed no penalty for optional measurements in an impossible case.

This accounts for the complete resource difference: 16 versus 14 measurements and 18 versus 16 measurement credits. It is a tradeoff between additional nuisance-parameter knowledge and fewer probes, not a correctness win.

The negative complementary-measurement pair also used different valid orders: the older selector measured the reference then the offset; 6.2 measured the offset then the reference. Both orders preserved the guarantee.

## What was checked

- 33 instrument, oracle and scoring tests passed before participant execution.
- All 78 recorded instrument events replayed through the frozen service.
- A separate model reviewer, given shuffled records without model identities or primary scores, independently implemented the checks. The implementations agreed on 576 field comparisons and the reviewers on 72 report judgments.
- All 24 delivered final answers matched their sealed reports.
- A fresh extraction of the retained original archive passed five verification steps, leaving all 199 inventoried files unchanged. This original-archive check is distinct from the public-copy verification in the disclosure receipt.

These are retained same-lab checks, including separate model reviewers where recorded. They are not external scientific replication.

## Scope and limits

- The older logged selector is gpt-6-astra; no separately attested gpt-6.1 serving snapshot was tested.
- These are finite, noiseless, authored model families with exact arithmetic and local calculation tools, not an unaided reasoning test or frontier-science discovery.
- Six profiles with two truths each are six problem families, not twelve independently sampled scientific domains.
- A guarantee-losing action is scored before its actual outcome; a lucky correct final conclusion would not erase a lost worst-case guarantee. No such loss occurred here.
- The passive impossible cases are excluded from feasible-completion and guarantee-preserving-identification denominators.
- Optional nuisance measurements in impossible cases had no penalty under the frozen protocol; fewer probes do not create a post-hoc correctness win.
- Observed choices and their counterfactual feasibility do not show how an actor would execute every unobserved policy branch.
- Independent implementations and separate model reviewers provide same-lab verification, not external replication, backend attestation or a general truthfulness classifier.

## Evidence and publication provenance

The original report and public evidence copy have separate identities. Use the public ZIP’s own checksum and disclosure receipt when checking the download. Its packaging and path disclosures differ from the retained original archive.

- [Original report PDF](reports/round-03.pdf) — 7 pages, unchanged bytes.
- [Public evidence ZIP](evidence/round-03.zip).
- [Public archive checksum](evidence/round-03.sha256).
- [Disclosure and verification receipt](evidence/round-03-publication.json).
- [Structured study index](studies.json).

### Original artifact identities

- Original PDF SHA-256: `3ddb04548d12b6d8f81b03f302a98fee6d35e62b84a6eb99f9f38028d8ad65ab`.
- Retained original archive SHA-256: `6294e44f587d2ec27ec6d04a77ba4cccdfbe4e423dda010345e135001d15360b`. This is not the public ZIP checksum.
- Retained original frozen-protocol SHA-256: `356522c068aa6285326d32803c02ec6d23e8f3fa74d045f1c607fea764466d42`.

Further studies and dated corrections belong in this series. The entry template preserves the same three-field TLDR and provenance structure.
