# Agent evaluations

**What this hub presents:** Seven historical native model-agent studies (Rounds 01–07), two historical scripted studies (Rounds 08–09), and two distinct, newly completed direct-provider API studies from November 22, 2026. Their execution types and denominators remain separate.

**Execution status:** A two-request strict tool exchange passed, followed by an eight-session live receipt-scope behavioral pilot: **4/4 safe joint completions in both receipt arms**, zero unsafe attempts and duplicate effects, 48 real provider requests, and a **$0.246104 estimated provider cost**. The separate compatibility estimate was $0.004696. These are usage-based estimates, not invoices. The [public write-up](live-api/index.html) and [redacted manifest](live-api/summary.json) are now visible; raw requests, responses and ledgers remain private. The earlier native, scripted and cold-start studies retain their provenance.

**Inventory:** 232 assigned native contexts across Rounds 01–07; 301 primary scripted executions across Rounds 08–09. Round 09’s six post-hoc diagnostic executions are separate. These counts are an inventory, not a pooled accuracy score or independent task-family count.

## Read the evidence

- [Evaluation hub](index.html)
- [Full original study series](../rin-self-evaluation/index.html)
- [Original presentation data](../rin-self-evaluation/studies.json)
- [Machine-readable evidence index](evidence-index.json)
- [Live API results and methods](live-api/index.html)
- [Redacted live results manifest](live-api/summary.json)

Each expanded study card links to its original methods, PDF, evidence archive, checksum and publication receipt. Recorded outcomes and outliers are copied from the reviewed presentation data; the short headlines retain the same denominators.

## Source provenance

- Historical study source as-of date: November 19, 2026, America/New_York.
- Direct API studies reported: November 22, 2026, America/New_York (executions early November 23 UTC).
- Source revision: [8f5aaa28346f4c9d1a605fda85b36d1bacbbeb84](https://github.com/uberbestest/josh-rin-interactive-lab/tree/8f5aaa28346f4c9d1a605fda85b36d1bacbbeb84/rin-self-evaluation).
- Source `studies.json` SHA-256: `f5c997bbbb96089a67fc73d2198898a0978348fffa928b941e8834eb888462fe`.
- Matched requested selectors: `gpt-6-astra` and `gpt-6.2-astra`. These are requested identities, not independently attested serving snapshots. The informal “6.1 vs 6.2” label does not establish an older 6.1 backend.
- Round 01 inherited a session declared “GPT-6.2 Astra Pro” without an explicit selector override or older-model control.
- Provider token usage, API costs and equal token budgets were not measured in the retained native trials.
- Same-lab review, native model participation, scripted replay, public presentation checks and external replication are distinct claims.

## API reporting contract

A provider run should retain requested and returned model IDs, settings, prompt/code versions, a frozen case and repeat manifest, all assigned attempts including failures, declared outcome rules, raw execution records, provider-reported usage, elapsed time, costs with their price basis and denominators, uncertainty, redactions and review scope. Unavailable usage or cost is null/unknown, not zero. The exact fields are listed in `api_run_reporting_contract` in the evidence index.

The contract still governs future studies. [Two completed provider studies](live-api/index.html) now have explicit model observations, outcome denominators and usage-based cost estimates, with raw archives retained privately.

## Maintenance

Keep this hub’s summaries consistent with the canonical study records. Do not relabel native sessions as direct provider API calls, or scripted executions as fresh model participants. Preserve every original study’s denominators, outliers, uncertainty and disclosure history.

The `cold-start` section and `native_cold_start_pilot` index entry link the executed two-context reproduction pilot, its frozen inputs, new receipts and complete answers. Its two native contexts are reported separately from the historical inventory. A same-lab fresh-actor pilot remains distinct from external replication.

The page is static HTML and CSS, works without JavaScript, and uses native expandable study records. It makes no external model calls and collects no telemetry.

## Cold-start reproduction pilot

[Read the executed two-context pilot](reproduction-pilot/index.html). Both assigned fresh native sessions reproduced the published Round 09 archive and correctly explained its main comparison and trust assumptions. One received the archive and one also received a reproduction card. Complete inputs, unedited answers, command logs and new verification receipts are preserved. This is a separate same-lab artifact-usability pilot, with no claim of a card advantage, population success rate or direct-provider API execution. The historical 232-context inventory remains unchanged.
