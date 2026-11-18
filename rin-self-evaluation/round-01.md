# Round 01 — The Retry That Needed a Receipt

## TL;DR

**What we tested:** Can an agent recover from unreliable reads and uncertain writes without duplicating an action or claiming unsupported success?

**What happened:** All 10 feasible runs completed. All 4 blocked cases retained supported drafts and disclosed the blocker. All 14 final reports were accurate.

**Outliers:** No measured error outlier. In all 4 ambiguous-acknowledgement cases, the agent checked a receipt before attempting recovery.

[Open the web page](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/round-01.html) · [Report PDF](reports/round-01.pdf) · [All evaluations](README.md)

## Recorded setup

- **Status:** Executed.
- **Run date:** November 17, 2026 (America/New_York).
- **Publication date:** November 18, 2026.
- **Record:** `JRR-RETRY-RECEIPT-2026-11-17-001`.
- **Design:** Single-configuration mechanism pilot: seven mechanisms, two payloads each, fourteen fresh native contexts.
- **Participants:** 14 native contexts · no generation control.

**Model provenance:** These participants inherited the current session model, declared as GPT-6.2 Astra Pro, without an explicit selector override. No pinned serving snapshot or older-generation control was recorded. This is a baseline pilot, not a 6.1-versus-6.2 comparison.

## Results, with their denominators

One configuration, seven authored mechanisms and two payloads per mechanism. There is no matched older-model condition.

| Recorded endpoint | Inherited-session configuration |
| --- | --- |
| Feasible completions | 10 / 10 |
| Blocked cases with supported draft and disclosure | 4 / 4 |
| Supported final reports | 14 / 14 |
| Receipt-first recovery after an ambiguous acknowledgement | 4 / 4 |
| Duplicate effects | 0 |
| Unsupported completion claims | 0 |
| Operational calls | 70 |

The 10 feasible runs and 4 blocked runs are separate outcome groups. The 12 semantic checks and 15 finite-policy cells are instrument or mathematical checks, not extra agent participants.

**Interpretation:** Successful coverage of the seven authored recovery mechanisms; this pilot cannot establish a generation difference.

## Outliers and informative differences

All four ambiguous acknowledgements were followed by a receipt check before recovery. No duplicate effect, unsupported completion claim, unsupported causal assertion, or post-revocation attempt was recorded.

The result supports recovery across the seven authored mechanisms under the supplied contract. With no older-model comparison, this round cannot establish a generation difference.

## What was checked

- 12 semantic instrument tests passed; a separate finite-policy analysis covered 15 cells without adding live participants.
- All 84 recorded service events replayed correctly.
- A separate parser agreed on 126 mechanical field comparisons, and all 14 native final messages matched the recorded reports.
- The six-page PDF was visually checked. The original HTML viewer browser check was blocked by the environment and is not claimed as browser-verified.

These are retained same-lab checks, including separate model reviewers where recorded. They are not external scientific replication.

## Scope and limits

- No matched older-model condition and no pinned serving snapshot.
- The tested configuration inherited the session declared as GPT-6.2 Astra Pro; an explicit gpt-6.2-astra selector was not recorded for these runs.
- Authored synthetic service tasks, one execution per declared cell; no population failure-rate estimate.
- Same-lab model review and replay, not external replication. The shared filesystem was bounded by instruction, not OS isolation.
- The separately checked 15 finite-policy cells concern a two-world mathematical model, not additional live participants.
- The PDF was visually checked; the original HTML viewer browser check was blocked by the environment and must not be called browser-verified.

## Evidence and publication provenance

The original report and public evidence copy have separate identities. Use the public ZIP’s own checksum and disclosure receipt when checking the download. Its packaging and path disclosures differ from the retained original archive.

- [Original report PDF](reports/round-01.pdf) — 6 pages, unchanged bytes.
- [Public evidence ZIP](evidence/round-01.zip).
- [Public archive checksum](evidence/round-01.sha256).
- [Disclosure and verification receipt](evidence/round-01-publication.json).
- [Structured study index](studies.json).

### Original artifact identities

- Original PDF SHA-256: `18dc7068214e40630cf93cef8ea5a11715763a687882f4552f6ac6cfd113e468`.
- Retained original archive SHA-256: `00872ec1c751056c9967c748a970d73ff8e463b414930fab7e725c5f77bc7bb7`. This is not the public ZIP checksum.
- Retained original frozen-protocol SHA-256: `a28da28c77931fdd05f3b008de16f6ef7d0c5606fb47da239bebd5babdc63a33`.

Further studies and dated corrections belong in this series. The entry template preserves the same three-field TLDR and provenance structure.
