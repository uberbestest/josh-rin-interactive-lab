# Pre-execution harness check

**What we tested:** The response adapter and command boundary used by the authored deterministic helper experiment, before any assigned service replay.

**What happened:** Ten isolated transport unit tests and three isolated infrastructure-failure retention tests passed. Python source compilation and Node syntax inspection also passed. These checks made **zero actual service calls and zero assigned study executions**.

**Outliers:** None among these thirteen isolated checks. Study outcomes had not been measured during this check.

## Checks and limits

`node tests/test_transport.mjs` verifies exact-byte identity transport, the three-field one-shot misbinding, unchanged nested local facts, unchanged nonreceipt and job-A responses, restoration of authentic output after the first substitution, rejection of unexpected source states, rejection of an unknown adapter, and the restricted historical command grammar.

Python and Node syntax checks cover `execute.py`, `reproduce.py`, and `run_helper.mjs`. This is a same-lab implementation check, not independent validation of the inherited service or a scientific outcome.

`python3 -B tests/test_failure_retention.py` injects a subprocess timeout, nonzero exit, and malformed output using mocked process calls and sentinel files that are not study states. It verifies that available initial state, current state, and event bytes are copied before temporary cleanup. A sanitized `harness_error.json` retains error type, execution stage, case/helper/arm identifiers, return code when available, and the names of retained files. Private paths, exception messages, stderr, and stack traces are excluded. No replacement execution occurs after such a failure.

The harness copies the unchanged inherited client and engine into temporary service directories. The canonical client writes and hashes its own events. The adapter changes only the text returned to the helper; raw output and presented output are both retained, with their own byte counts and SHA-256 digests. Its single permitted substitution requires a canonical pending B receipt, known committed A evidence, and unresolved B evidence.

Every study execution is verified against the canonical event replay and an independently implemented Python expectation for the displayed response. The runner does not assume a particular safety or completion outcome. It explicitly records no-op/postterminal requests, admitted attempts, unsafe-attempt increments, fresh write effects, newly finalized jobs, resources, first value loss, and residual canonical continuation value. A parser stopping safely is not counted as task completion. Zero whole-trajectory utility after a safety violation is not called proof of physical irreparability.

`reproduce.py` verifies all retained event chains and recomputes their summaries. By default it also repeats all authored helper executions in new temporary service instances and compares states, action/observation/oracle records, transport bytes, and derived results. The fresh comparison excludes wall-clock timestamps and the event-chain hashes that bind those timestamps, plus runtime-version metadata. Each individual event chain is still verified using its own retained timestamps and hashes. `--verify-only` skips fresh helper execution and reports that distinction.

The known-source JavaScript VM exposes only the replay proxy and the historical `store`, `load`, and `text` interface. It is not represented as an operating-system security boundary. This experiment invokes no native participants or model APIs.
