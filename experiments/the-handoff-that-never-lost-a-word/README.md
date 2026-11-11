# The Handoff That Never Lost a Word

**Josh & Rin's Lab · November 11, 2026 · v0.1.0 · offline synthetic audit**

**Record:** `BONDED-RSI-HANDOFF-LOSSLESS-2026-11-11-001`  
**Status:** EXECUTED SCRIPTED FIXTURES · NO LIVE AGENTS · SAME-AUTHOR VERIFICATION · INDEPENDENT REVIEW PENDING

[Open the interactive exhibit](index.html) · [Methods and limits](method.html) · [Machine-readable results](results.json)

## Question
Can a relay preserve every byte of its original scientific observation and every prior handoff note, yet still cause its receiver to treat *observed* as *verified* or *authorized*?

## Answer within this authored apparatus
3,584 deterministic chains × four receiver policies = 14,336 decisions. Among four intentionally misleading but byte-preserving conditions, latest-status and archive-presence heuristics falsely elevated all 1,792 cases each. The provenance-bound recovery returned the stipulated warranted tier for 3,584 of 3,584 scripted chains, but only because an external trusted reference and registry were supplied. This is an interface counterexample, not empirical AI-agent performance.

## Conditions and denominators

Each of eight conditions is crossed with 32 textual seed variants, hop lengths 2/4/8, and every possible insertion hop: `32 × (2+4+8) = 448` chains per condition. Each chain is separately read by four scripted receiver rules. Seeds vary fictional observation text, not attack mechanics; these rows are correlated design cells, **not independent subjects or an estimated failure rate**.

The original observation explicitly warrants tier 0 (OBSERVED). The two positive controls have a separate stipulated trusted verification or authorization registry. Tier -1 means quarantine/incomplete evidence.

| Condition | True warranted tier | Source exact | Latest falsely elevates | Archive-only falsely elevates | Strict quarantines | Recovery correct |
|---|---:|---:|---:|---:|---:|---:|
| `clean` | 0 | 448/448 | 0/448 | 0/448 | 0/448 | 448/448 |
| `missing_source` | -1 | 0/448 | 448/448 | 0/448 | 448/448 | 448/448 |
| `promoted_verified` | 0 | 448/448 | 448/448 | 448/448 | 448/448 | 448/448 |
| `promoted_authorized` | 0 | 448/448 | 448/448 | 448/448 | 448/448 | 448/448 |
| `misleading_receipt` | 0 | 448/448 | 448/448 | 448/448 | 448/448 | 448/448 |
| `legitimate_verification` | 1 | 448/448 | 0/448 | 0/448 | 0/448 | 448/448 |
| `legitimate_authorization` | 2 | 448/448 | 0/448 | 0/448 | 0/448 | 448/448 |
| `stale_receipt` | 0 | 448/448 | 448/448 | 448/448 | 448/448 | 448/448 |

The four semantic conditions—promoted verification, promoted authorization, misleading self-receipt, and stale trusted-looking receipt—are **deliberately constructed** to preserve the source text verbatim while adding unsupported claims. The source-preservation invariant therefore does not imply faithful inference. Source deletion in the missing-source arm is a contrast control, not a “lossless” result.

## Operationally different receiver rules
- **Latest:** reads the last advertised tier or a receipt's conspicuous words, ignoring provenance.
- **Archive-only:** requires an original source copy, but still trusts a newer unsupported tier.
- **Strict:** compares the surface tier with the warrant derived from an independent anchor and registry; quarantines disagreement.
- **Recovery:** reconstructs the warranted tier from the retained source and a **stipulated** trusted external record, downgrading unsupported upgrades while admitting genuine verification and authorization.

These are deterministic authored policies, **not actual language models**. The trusted record is supplied by the test harness, not derived magically from a checksum or handoff text. If the anchor is adversarial, unavailable or stale, these controls do not establish truth. No actor actually granted operational authority.

## What a recipient must preserve

1. Raw observations and the exact original statement, with its scope.
2. Receipt binding, issuer, and purpose—not the presence of an impressive word.
3. The difference between an observed result, an independent check and a real permission grant.
4. Contradictions and missing sources as explicit unresolved states.

The note demonstrates **a possible semantic authority-laundering path**, not its frequency in deployed assistants. No private continuity, real team handoff, live Rinball bridge, Castle, credentials, human subjects or paid model calls were touched.

## Reproduce

All scientific code and raw-case generator are published; the full aggregate and eight complete witness packets are in `results.json`.

```sh
node test.js
```

The tests execute the full matrix afresh and compare the entire regenerated JSON summary against the published evidence, not merely the headline totals. Or open `index.html` in a browser; it runs offline.

**Source:** `engine.js` · **Verification:** `test.js` · **Protocol:** `protocol.json`. The apparatus, scenarios and checkers were authored together; the test suite is same-author engineering verification, **not external preregistration, independent evaluation, or empirical prevalence evidence**.

*The sky is not for sale.*
