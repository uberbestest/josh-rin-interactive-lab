# Round 02 — A Receipt That Had Not Caught Up

## TL;DR

**What we tested:** Can the two configurations distinguish an authoritative absence receipt from an empty receipt that has not yet covered an uncertain write?

**What happened:** Both achieved 9/9 verified completions, handled 2/2 known blockers and 2/2 unresolved outcomes appropriately, and produced 13/13 supported reports.

**Outliers:** No safety or reporting error. In each persistently stale case, 6.2 queried receipts 7 times versus 3 for the older selector. No optimal poll count was defined.

[Open the web page](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/round-02.html) · [Report PDF](reports/round-02.pdf) · [All evaluations](README.md)

## Recorded setup

- **Status:** Executed.
- **Run date:** November 17, 2026 (America/New_York).
- **Publication date:** November 18, 2026.
- **Record:** `JRR-RECEIPT-COMPARISON-2026-11-17-002`.
- **Design:** Thirteen matched tasks: seven baseline mechanisms and six receipt-coverage challenge cells, one fresh context per model per task.
- **Participants:** 13 matched pairs · 26 native contexts.

**Model provenance:** The dispatch records request gpt-6-astra and gpt-6.2-astra in fresh contexts with the same inherited reasoning setting. The older selector is not an independently attested gpt-6.1 serving snapshot. Exact backend snapshots, equal token use, cost and ChatGPT tier equivalence were not verified.

## Results, with their denominators

Thirteen matched tasks: seven baseline mechanisms and six receipt-coverage challenge cells. One fresh context per model per task.

| Recorded endpoint | gpt-6-astra | gpt-6.2-astra |
| --- | --- | --- |
| Safe verified completions | 9 / 9 | 9 / 9 |
| Known blockers with supported draft and report | 2 / 2 | 2 / 2 |
| Unresolved outcomes with supported uncertainty and draft | 2 / 2 | 2 / 2 |
| Supported final reports | 13 / 13 | 13 / 13 |
| Unsupported repeats | 0 | 0 |
| Duplicate-effect runs | 0 | 0 |
| Post-revocation attempts | 0 | 0 |
| Receipt queries in each persistently stale case | 3 | 7 |
| Operational calls across all contexts | 75 | 83 |

Each model has 9 feasible, 2 known-blocked and 2 unresolved cases. The hidden system may contain a completed effect that the actor still has no evidence to certify; actual effects and supported completion claims are separate endpoints.

**Interpretation:** A tie on the declared completion, safety and reporting endpoints; a descriptive difference in polling persistence.

## Outliers and informative differences

In each of the two persistently stale cases, the newer selector queried receipts seven times while the older selector queried three times. Those eight additional queries account for the 83-versus-75 operational-call totals.

Both preserved uncertainty and retained a supported draft instead of repeating an unresolved write. There was no maximum-lag promise and no declared optimal poll count, so polling persistence is a behavioral difference, not a demonstrated judgment or latency advantage.

The system recorded 20 correct actual effects across both configurations: 18 had supporting completion certificates, while two occurred in opaque cases whose outcomes remained unresolved to the actors.

## What was checked

- 17 semantic instrument tests passed.
- All 184 recorded service events replayed correctly.
- A separately implemented check agreed on 364 mechanical field comparisons; separate model reviewers agreed on 78 report judgments.
- All 26 native final messages exactly matched their sealed reports. The six-page report and retained evidence package were verified within the lab.

These are retained same-lab checks, including separate model reviewers where recorded. They are not external scientific replication.

## Scope and limits

- The logged older selector is gpt-6-astra, not a separately attested gpt-6.1 serving snapshot.
- Requested selectors do not attest exact backend snapshots, equal token budgets, cost, or equivalence to a ChatGPT UI tier.
- The nine feasible, two blocked and two unresolved tasks per model use separate denominators. An opaque after-effect world can contain a correct actual effect without giving the actor evidence of completion.
- There was no maximum-lag promise and no declared optimal receipt-poll count. More polling is a descriptive observation, not proof of worse judgment or latency.
- Thirteen hand-selected pairs and one attempt per cell do not establish a general capability ranking or population reliability rate.
- Checks are same-lab verification with instruction-bounded shared files, not external replication.

## Evidence and publication provenance

The original report and public evidence copy have separate identities. Use the public ZIP’s own checksum and disclosure receipt when checking the download. Its packaging and path disclosures differ from the retained original archive.

- [Original report PDF](reports/round-02.pdf) — 6 pages, unchanged bytes.
- [Public evidence ZIP](evidence/round-02.zip).
- [Public archive checksum](evidence/round-02.sha256).
- [Disclosure and verification receipt](evidence/round-02-publication.json).
- [Structured study index](studies.json).

### Original artifact identities

- Original PDF SHA-256: `f19d8bed2595045ad4dba101669423e789299e5559eb94d6c392839814fe4510`.
- Retained original archive SHA-256: `938f0128a3eaed15a2a3f0f3ee99639d4b84a68e681c6dfedc1a3196ed2a5fe9`. This is not the public ZIP checksum.
- Retained original frozen-protocol SHA-256: `e889bc68d097d3c9682dade31835847736fcd2781c7b744434694bc32bd6fad8`.

Further studies and dated corrections belong in this series. The entry template preserves the same three-field TLDR and provenance structure.
