# Direct-provider API pilot — receipt scope (PREPARED, UNRUN)

**What we're testing:** Whether two requested API model selectors safely complete two authorized synthetic jobs when a target's authoritative receipt contains an unrelated historical `ABSENT` fact. A target-only condition removes just the other-job nested field. This is a **new, Round-07-inspired smoke test**, *not* an exact replay or independent replication of Round 07's historical service/archive.

**What happened:** No API model has run. An offline deterministic fixture verifies the runner and service only. No provider token usage, cost, model ranking, or behavioral result exists yet.

**Outliers:** Not assessed on live model attempts. The service intentionally exposes a duplicate-write error if the operator treats an unrelated historical absence as permission to commit the target.

## Design and freeze

- `manifest.json`: four authored settings (A/B precommitted × combined/target receipt), crossed with two requested selectors (`gpt-6-astra`, `gpt-6.2-astra`): **8 assigned model contexts**, fixed order. One attempted run per cell, no opportunistic replacement.
- `runner.py`: isolated synthetic service and Responses API tool loop; status/coverage evidence, actual writes, attempted unsafe actions, duplicate effects and physical completion are separate endpoints.
- Each run saves a verbatim manifest, manifest/runner SHA-256, assigned attempts, provider-reported usage, returned model identifiers, tool events, estimated costs, failure records and trace hashes. Failed/incomplete assignments stay in the denominator.
- No claim of a pinned serving snapshot from a requested selector. The older selector is **not** proof of a GPT-6.1 snapshot. The results here cannot be pooled with the historical study.
- The simulator defines its own jobs/key/deadline logic. The linked Round 07 archive remains the authoritative record for Round 07, and must be imported separately for a faithful replication.

## Offline validation — safe, no key, no expense

```bash
cd evaluations/api-pilot
python3 -m unittest -v test_runner.py
python3 runner.py --dry-run
```

The second command writes a local `results/<UTC timestamp>/` fixture archive. The fixture **is not an LLM**, and dry-run completions are not scientific model results.

## Opt-in live execution (NOT performed here)

Use a dedicated project-scoped key from the **Josh and Rin lab** API organization, stored as a secret in the execution environment. Never paste a key in chat, commit it, or embed it in an artifact. The owner must first verify the credits have arrived and set an appropriate project usage alert. Project monthly spend limits are **soft thresholds**, not provider-enforced hard caps.

```bash
python3 -m pip install --upgrade openai
# Configure OPENAI_API_KEY securely in your runner environment; do not echo it.
python3 runner.py --live --confirm-live YES
```

- The default path makes **zero provider calls**. `--live` requires both the explicit `YES` flag and an environment key. The OpenAI SDK is imported only for live runs. No unattended scheduling or retries.
- The manifest has a **$5 maximum estimated-spend circuit breaker**. Before each call the runner reserves an intentionally conservative cost estimate for input + bounded output; after each completed call it records provider-reported usage and deducts an estimated charge. This local control limits exposure but **is not a mathematically guaranteed hard billing cap** (tokens/pricing can vary, errors can be billed, reported usage may lag). The platform's project-limit setting is also not a hard cap.
- Pricing is frozen to documented November 21, 2026 **standard short-context listed prices**: `gpt-6-astra` $10/M input, $1/M cached input, $50/M output; `gpt-6.2-astra` $8/M input, $0.40/M cached input, $40/M output. Validate price and access immediately before a paid run; running with a changed pricing basis requires an explicit manifest revision.
- No provider built-in tool usage is enabled; the sole function is the local simulated service. `store=False` plus manual replay preserves returned reasoning/tool items and keeps the service private. Raw traces and encrypted reasoning artifacts stay local under the ignored `results/` directory; human review/redaction is required before publishing.

## Research boundary and next work

A positive fixture result validates harness plumbing only. Next: manually inspect source freeze, check credit availability and rate limits, execute all eight fixed live assignments once, inspect all raw records, review failures, then publish a separate API results page and a redacted checksum-linked evidence archive if warranted. Any subsequent extended Round 07 replication requires a new manifest using the original exact service definitions and evidence archive—not these authored substitutes.

Source series: [Round 07](../../rin-self-evaluation/round-07.md), [evaluation hub reporting contract](../README.md). No edits to published study outcomes or denominators are made here.