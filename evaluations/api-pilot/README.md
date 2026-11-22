# Native API pilot — prepared, unrun

**What this tests:** a new synthetic receipt-scope experiment with eight assigned contexts. The service asks an agent to finish two authorized jobs without repeating a committed job. One condition includes unrelated historical `ABSENT` evidence in receipts. This is inspired by Round 07; it is not a replication of the historical study.

**What happened:** this replacement runner is being validated offline. No paid provider run or model-behavior result is claimed. Scripted fixtures and fake HTTP responses test infrastructure only.

**What changed:** execution uses ordinary Python on Windows or Linux. Python's built-in SQLite keeps the authoritative financial record and complete run history. There is no SDK installation, WSL requirement, database server, or third-party Python package.

This implementation follows the reviewed architecture decision: keep SQLite, the Windows-compatible runtime, simulator and small replaceable HTTPS adapter, and correct the scoped accounting/stop-policy defects. [Draft PR #32](https://github.com/uberbestest/josh-rin-interactive-lab/pull/32) remains intact as an audit record. Historical results, denominators and publication pages are unchanged.

## Start offline on Windows

Use Python 3.11 or later with its standard `sqlite3` and TLS modules. In the downloaded repository's `evaluations/api-pilot` folder, run:

```powershell
py runner.py check
py runner.py dry-run
```

If Python is invoked as `python` on your computer, use that instead of `py`. On Linux, `python3` is conventional. No package installation, Git installation, API key, or provider connection is needed for these commands. Running `runner.py` with no arguments also selects the offline fixture.

`check` validates the plan and local transactional storage, then prints the exact plan hash and proposed limits. `dry-run` exercises every frozen assignment and prints its evidence-file path. The expected comparison fixture completes 8/8 synthetic contexts, with zero model participants and null provider cost.

To verify an evidence file later:

```powershell
py runner.py verify results\<run-id>\evidence.json
```

The file contains the complete frozen plan, Python source bundle, exact JSON requests, response bytes, timing, service actions, calculations and hash-chained events. It is an evidence copy; the spending ledger remains authoritative.

## The design

The runner separates three concerns:

1. `protocol.py` contains the authored service, blinded prompt, tool schema, prices and reservation estimates. Initial prompt bytes, tool schema and simulator behavior are preserved from `4387aa2`.
2. `ledger.py` commits run claims, request reservations, raw response envelopes and settlements as SQLite transactions. It requires WAL mode and `synchronous=FULL`; a storage error stops progress. No application-written Unix directory synchronization is used. SQLite provides the native filesystem implementation.
3. `runner.py` advances the fixed assignments through a small HTTPS transport. `verifier.py` replays the evidence and accounting. The transport sends one request, does not follow redirects, and does not automatically retry.

SQLite is a local file supplied through Python, not another service to install. Its guarantees depend on the operating system and storage honoring synchronization. Subprocess termination tests establish process-crash behavior; they do not certify physical power-loss behavior on a particular laptop.

## Spending and restart behavior

The proposed comparison has a **$5 estimated total ceiling and $0.625 per assigned context**. `calibration.json` is a separate proposed single-context check with a **$1 estimated ceiling**. Neither plan grants authorization to execute it.

Before dispatch, one transaction commits the exact request and its spending reserve. The schema-v2 plans freeze `reservation_policy`: an initial allowance of 8,192 input tokens; continuation requests use the larger of that allowance and the preceding priced response's `input_tokens + output_tokens + 1,024`. The margin allows for the local tool result and request framing. Continuations require preceding priced usage. Opaque encrypted-content length and receipt serialization do not size continuation reserves. A separate initial sanity check requires the fixed prompt/tools to fit the initial allowance under a padded UTF-8 estimate (`2 × bytes + 4,096`); this rejects oversized initial text before dispatch without changing the frozen initial reserve. Requests still reserve the full output allowance and use the highest frozen input/cache-write rate. Decimal strings are used for money.

The initial allowance and margin are explicit, uncalibrated estimates, not provider-enforced input bounds. Real usage may exceed them; charges above the monetary reserve stop the whole run. This policy removes the demonstrated dependence on opaque replay bytes without ignoring actual token growth. Equal dollar allocations still buy different capacity at different model prices. Case-budget/call/token limits remain resource censoring and must not be counted as unsafe model behavior. These controls cannot guarantee a provider invoice limit.

After a response, its status, selected nonsecret headers, raw bytes and timing are committed before JSON decoding or usage validation. The runner prices ordinary input, cache reads, disjoint cache-write categories and total output once.

| Stopping condition | Scope and accounting |
| --- | --- |
| Valid, priced response truncated at its output limit; invalid tool arguments or identity | Current case fails; no invalid tool action is applied; later assignments proceed. |
| Case spending allocation, case call limit, or continuation estimate outside the frozen pricing basis | Current case stops; later independent allocations remain available. A refusal before dispatch costs zero and is not model participation. |
| Timeout, partial body, invalid JSON, missing/unpriceable usage, unknown output types or unexpected billing identity/tier | Global halt; retain the unresolved reserve and null cost. No later paid requests. |
| Run spending ceiling, monetary reserve overrun, provider-reported output exceeding the requested cap, or unexpected response status | Global safety halt. Preserve known charges when usage is priceable. |
| Storage failure | Stop the process; a committed reservation survives if a request may have been sent. No automatic restart. |

`CASE_FAILED`, `CALL_LIMIT` and `STOPPED_EARLY` are case outcomes, not global financial halts. The run's storage lifecycle can be `COMPLETED` while the experiment is unsuccessful. Summaries separately report `successful`, `case_failures` and `blocked_contexts`; the raw outcomes and stop reasons distinguish model errors from resource or infrastructure limits. For run commands, exit code **0** means every assigned case completed successfully, **2** means a recorded unsuccessful/blocked run, and **1** means a caught setup/storage/validation error. Read-only verify/report commands can return 0 for structurally valid failure evidence; that does not make the experiment successful.

All assigned cases remain in the plan. A controlled halt writes blocked outcomes for the remaining cases. An abrupt process death can leave a partial history without a final summary; the frozen assignment list still preserves the denominator.

The live ledger has one default location per local user:

- Windows: `%LOCALAPPDATA%\JoshRinLab\api-pilot\ledger.sqlite3`
- Linux: `$XDG_STATE_HOME/JoshRinLab/api-pilot/ledger.sqlite3`, or `~/.local/state/JoshRinLab/api-pilot/ledger.sqlite3`

Changing repository folders does not silently create a new live budget. A live protocol identity can be claimed only once. Any unfinished or unreviewed globally halted live run prevents another live run through this ledger. There is no reset, automatic resume, retry, or deletion workflow. Unknown charges remain blocked and require a separately reviewed reconciliation procedure; the review command below cannot settle or release them. Deleting or replacing the database, using another OS user, overriding the state environment directory, or switching computers defeats that local coordination. It is not a provider-wide spending limit.

### Reviewing a fully accounted global halt

First use `report --run-id <run-id>` and `export` to inspect the original stop reason, every raw response, pricing calculation, and total. `report` prints the current `snapshot_sha256`. Only after the owner has reviewed a **finished live global halt with zero unresolved requests**, record the review locally:

```powershell
py runner.py review-halt <run-id> --snapshot-sha256 <current-snapshot-sha256> --reviewer "Josh" --note "Describe the reviewed charges, failure and next-step rationale; no secrets"
```

This makes no provider requests and reads no credentials. It recomputes retained usage/costs and appends a hash-chained `halt_reviewed` receipt binding the exact snapshot, reviewer, note and known estimated spend. It does not edit the original halt, summary, charges, requests or evidence. Stale hashes, duplicate reviews, running/unclosed runs and unknown costs are refused. The receipt is a local operator acknowledgement, not an authenticated provider invoice or new paid authorization.

A review permits consideration of a **different protocol identity**, which still needs its own exact plan-hash approval and separate paid authorization. The old protocol remains single-use and cannot resume, reserve more requests, or relaunch. Prior costs remain in the same ledger. Successful closed runs and case-only failures already permit a separately approved new protocol; they need no global-halt review. The command deliberately does not recover an abruptly interrupted, unclosed run.

Use local storage in the user's private profile. Windows access follows the profile's inherited permissions; Unix permission bits are not presented as Windows ACL guarantees. The API key is read from the existing process environment or a hidden interactive prompt and is not intentionally written to the ledger, export, source or logs. Model inputs and outputs can themselves contain sensitive data, so raw evidence stays private until reviewed.

## Proposed protocol and limits

`plan.json` keeps eight model-major assignments: A/B precommitted × combined/target receipts × two requested selectors. Local case IDs are neutral; condition mappings stay in the frozen plan. Each context permits at most eight requests with medium reasoning and a 4,096-token output ceiling. These constraints are not empirically calibrated on real models.

The replacement explicitly requests encrypted reasoning content for stateless continuation, then retains every returned output item in subsequent history. This is a declared request change from the earlier runner. Requests use the global direct Responses endpoint, standard processing, implicit 30-minute caching, `store=False`, and one function call at a time. No built-in tools are requested. The fixed request/usage contract is tested with local fake responses; real server acceptance remains unverified.

The revised reserve and stopping policies have distinct `002` protocol identities and schema-v2 frozen plans. Source/prompt/simulator semantics are retained; experimental stop semantics have intentionally changed. Old proposal files must not silently authorize the revised protocol. Original schema-v1 exports can still be examined with their original bundled source; their bytes and historical records are not migrated or rewritten.

Requested and returned model identities are recorded separately. Each accepted returned identity is explicitly listed in the frozen plan; an unlisted identity stops the run for a pricing review. The selected aliases do not independently attest an immutable serving snapshot.

The prices were copied from the prior draft's November 21, 2026 record. Their provenance and source URLs are retained in the plans; they have not been independently reverified for a new paid run. The comparison and calibration have distinct protocol identities and must be reported separately. A single context per comparison cell cannot support a model ranking or population error rate.

## A later authorized paid run

Offline readiness does not establish API connectivity, current credits/prices, account-specific model access, adequate tokens, or paid authorization. The owner's account interface has not exposed the expected enforced-spending settings; no enforced limit is assumed or claimed. Evaluate the actual billing protections and the residual risk of a narrowly scoped proposed experiment. A local estimated ceiling cannot replace a guaranteed invoice cap. If enforcement is unavailable, any decision to accept that exposure belongs in separate explicit paid authorization; these code changes do not provide it. Do not install another system or direct the owner through hypothetical controls.

For a separately approved plan, `check --plan calibration.json` prints the plan SHA-256. The paid entry point requires that exact hash:

```powershell
py runner.py live --plan calibration.json --approve-plan <reviewed-plan-sha256>
```

The three existing environment variables are `OPENAI_API_KEY`, `OPENAI_ORG_ID`, and `OPENAI_PROJECT_ID`. An interactive terminal prompts for missing values; the key prompt is hidden. A noninteractive run fails before network access if any are missing. No key creation or key persistence is performed. This command is documented for later authorized use, not a request to run it now.

After execution or interruption:

```powershell
py runner.py report
py runner.py export <run-id> <private-evidence-file.json>
```

Exports never overwrite an existing file. Export failure does not reset the live ledger or permit another paid run. Evidence checks establish internal consistency, not independent attestation or protection against replacing the entire archive with a new forged archive and checksum.

## Offline verification

```powershell
py -m unittest discover -v
```

Tests cover forced subprocess termination, competing run claims, cross-directory restart refusal, missing usage, HTTP errors/timeouts, invalid JSON, cache pricing, output limits, malformed calls, UTF-8 evidence, exact request histories, simulator replay and tampered archives. Mock transports forbid real API access. The GitHub workflow runs the suite and fixture commands on native Windows and Linux without provider credentials, paid API requests, or artifact uploads.

The [evaluation reporting contract](../README.md) remains the publication contract. Raw records require disclosure review, and model claims require semantic review before any future results are published.
