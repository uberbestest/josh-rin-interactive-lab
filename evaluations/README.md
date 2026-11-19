# Agent evaluations

**What this hub presents:** Seven completed native model-agent studies (Rounds 01–07), two completed scripted studies (Rounds 08–09), and the reporting contract for future direct provider API runs.

**Execution status:** No direct provider API experiment has been run in this workspace and no provider API result or usage ledger is published in this release. Native sessions and scripted executions retain their original provenance. The separately reported cold-start reproduction pilot is complete: both assigned fresh native sessions reproduced the released study and explained its limits.

**Inventory:** 232 assigned native contexts across Rounds 01–07; 301 primary scripted executions across Rounds 08–09. Round 09’s six post-hoc diagnostic executions are separate. These counts are an inventory, not a pooled accuracy score or independent task-family count.

## Read the evidence

- [Evaluation hub](index.html)
- [Full original study series](../rin-self-evaluation/index.html)
- [Original presentation data](../rin-self-evaluation/studies.json)
- [Machine-readable evidence index](evidence-index.json)

Each expanded study card links to its original methods, PDF, evidence archive, checksum and publication receipt. Recorded outcomes and outliers are copied from the reviewed presentation data; the short headlines retain the same denominators.

## Source provenance

- As-of date: November 19, 2026, America/New_York.
- Source revision: [8f5aaa28346f4c9d1a605fda85b36d1bacbbeb84](https://github.com/uberbestest/josh-rin-interactive-lab/tree/8f5aaa28346f4c9d1a605fda85b36d1bacbbeb84/rin-self-evaluation).
- Source `studies.json` SHA-256: `f5c997bbbb96089a67fc73d2198898a0978348fffa928b941e8834eb888462fe`.
- Matched requested selectors: `gpt-6-astra` and `gpt-6.2-astra`. These are requested identities, not independently attested serving snapshots. The informal “6.1 vs 6.2” label does not establish an older 6.1 backend.
- Round 01 inherited a session declared “GPT-6.2 Astra Pro” without an explicit selector override or older-model control.
- Provider token usage, API costs and equal token budgets were not measured in the retained native trials.
- Same-lab review, native model participation, scripted replay, public presentation checks and external replication are distinct claims.

## API reporting contract

A provider run should retain requested and returned model IDs, settings, prompt/code versions, a frozen case and repeat manifest, all assigned attempts including failures, declared outcome rules, raw execution records, provider-reported usage, elapsed time, costs with their price basis and denominators, uncertainty, redactions and review scope. Unavailable usage or cost is null/unknown, not zero. The exact fields are listed in `api_run_reporting_contract` in the evidence index.

This contract is documentation. It does not attest a completed API runner or an executed provider study.

## Maintenance

Keep this hub’s summaries consistent with the canonical study records. Do not relabel native sessions as direct provider API calls, or scripted executions as fresh model participants. Preserve every original study’s denominators, outliers, uncertainty and disclosure history.

The `cold-start` section and `native_cold_start_pilot` index entry link the executed two-context reproduction pilot, its frozen inputs, new receipts and complete answers. Its two native contexts are reported separately from the historical inventory. A same-lab fresh-actor pilot remains distinct from external replication.

The page is static HTML and CSS, works without JavaScript, and uses native expandable study records. It makes no external model calls and collects no telemetry.

## Cold-start reproduction pilot

[Read the executed two-context pilot](reproduction-pilot/index.html). Both assigned fresh native sessions reproduced the published Round 09 archive and correctly explained its main comparison and trust assumptions. One received the archive and one also received a reproduction card. Complete inputs, unedited answers, command logs and new verification receipts are preserved. This is a separate same-lab artifact-usability pilot, with no claim of a card advantage, population success rate or direct-provider API execution. The historical 232-context inventory remains unchanged.
