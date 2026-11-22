# Two-call compatibility — PROPOSED, PAID EXECUTION NOT AUTHORIZED

Architecture baseline: `773c10571566457992534bbdb29aa69eaf6899ca`.
This is a separate instrument, not the two-job experiment shortened to two calls.
Its question is whether one requested model can complete one harmless function
exchange through the native Windows transport and accounting components.

## Frozen scope

`compatibility.json` assigns one `gpt-6.2-astra` context, at most two sequential
provider requests, medium reasoning, 4,096 output tokens per request, standard
processing, implicit 30m caching, `store=False`, and encrypted-reasoning inclusion.
There are no retries, repair turns, fallback models, extra contexts or concurrency.
The proposed local estimated allowance is $1. No key is created or persisted.

1. Request 1 forces `lab_probe`, a strict function with no arguments: an empty
   object schema with no additional properties. The initial instruction requests
   that the eventual answer contain only a JSON object with exactly the property
   `verification_value`.
2. Only after recording the full first response, validating it, pricing its usage,
   and validating its single function call, generate 16 random bytes locally as
   32 lowercase hexadecimal characters. Commit the receipt with its request and
   call identifiers before reserving the second request. The value is a disposable
   verification marker, not a credential. It must occur in neither Request 1 nor
   Response 1; its first occurrence in the exchange is the local receipt.
3. Request 2 preserves all first-response output items, including any encrypted
   reasoning, and appends the exact `function_call_output`. The tool definition is
   retained but `tool_choice="none"` disables further calls. Require an assistant
   message containing only JSON with exactly `verification_value` equal to the
   receipt. Whitespace around valid JSON is allowed; fences, prose, duplicate keys,
   extra fields and another function call do not pass.
4. Stop after Request 2 regardless of outcome. Any first-stage problem prevents
   Request 2. A third request is disallowed by both this fixed flow and the ledger's
   frozen two-request allocation.

The initial prompt and probe have no job, commit, finalize or service-mutation
operations. The original simulator and research prompts remain unchanged.

## Outcomes and evidence

**PASS** means this particular live tool exchange was acknowledged correctly,
both complete HTTP/model responses were accepted within the frozen identity/tier
and usage basis, all costs are priceable, and no safeguard was violated.
**NOT_DEMONSTRATED** covers a missing/malformed probe call, priced truncation,
incorrect format/value or premature termination. These are observations about
this exchange, not general model-reliability estimates.
**INFRASTRUCTURE_BLOCKED_OR_INDETERMINATE** covers HTTP/network/authorization
errors, unsupported response data, missing usage, unexpected billing identity,
budget refusal or provider/reservation limit violations. Unknown costs stay null
and reserved; no continuation or automatic retry follows uncertainty.

The evidence reports encrypted reasoning separately: whether it was observed,
included in the attempted second request, and demonstrated by a passing live
exchange. If no encrypted item was returned, a successful basic tool exchange
can still be PASS, but encrypted-reasoning replay is explicitly **not demonstrated**.
Even a positive replay flag does not attest the model's internal use of that state.

Private exports preserve the full frozen plan, source files/hashes, raw response
bytes (or marked partial bytes on transport failure), exact request JSON bodies,
receipts, expected/observed values, request IDs, UTC timestamps, elapsed times,
usage, pricing calculations, reserves and stopping reason. There are always two
planned request slots, each marked attempted or unattempted. An abrupt process
death leaves a partial run, the complete two-slot denominator and any durable
reserve; it does not permit relaunch. Credentials and authorization headers are
not included. The existing 4 MiB response-size bound remains a safety boundary;
an oversized response is partial/uncertain and cannot pass.

Verification rebuilds exact requests and full output-item replay from raw records,
recomputes charges, checks the local receipt's first occurrence and transaction
order, and derives the verdict rather than trusting a saved PASS label. Ledger
verification supplies the existing event-chain, row and budget checks. These are
local consistency checks, not independent provider billing attestation.

The only shared-code extension is an optional protocol verifier for the existing
fully-accounted halt review. Its accounting, closed-run, snapshot-hash and
zero-unresolved-cost guards are unchanged. For this instrument use
`compatibility.py report`, `export`, `verify` and `review-halt`; the two-job semantic
verifier deliberately does not grade this different protocol. A reviewed known
halt permits a different separately approved protocol; it cannot reset this run,
clear an unknown charge, or authorize another experiment.

## Offline checks

In the existing native Python environment, from `evaluations/api-pilot`:

```powershell
py compatibility.py check
py -m unittest discover -v
py compatibility.py dry-run --output results\compatibility-fixture
py compatibility.py verify results\compatibility-fixture\evidence.json
```

Default invocation is also an offline fixture. Its verdict is `FIXTURE_PASS`,
provider cost and provider attempted-request count are null, and the two scripted
exchanges have explicit zero local fixture settlements, not invented provider
usage. Fixtures are not evidence that a server accepted a request or a model ran.
Use a fresh output directory; exports never overwrite existing evidence.

`check` prints the plan hash and a **freeze hash binding the plan plus every source
file**, with no credential access or network traffic. After offline validation and
joint review, that exact freeze is the subject of a separate paid authorization.
Scoped Git attributes retain LF source bytes on Windows and Linux so native
checkouts agree on this identity; the attributes are also included in the freeze.
Changing source or plan invalidates it. A hypothetical authorized live invocation
requires `compatibility.py live --approve-freeze <approved-freeze-hash>`; this
document does not authorize running that command. It uses the existing hidden-key
prompt/environment handling and the same per-user live ledger as the research
runner. Noninteractive missing credentials fail before provider access.

## Connectivity is a separate local check

Run this only in ordinary PowerShell on the intended Windows computer; do not add
an authorization header or key. Save the output and native exit status separately
from compatibility evidence:

```powershell
curl.exe -q --silent --show-error --connect-timeout 10 --max-time 20 --output NUL --write-out "HTTP %{http_code}; remote %{remote_ip}\n" https://api.openai.com/v1/models
$LASTEXITCODE
```

A 401 after verified TLS indicates an authentication-requiring endpoint was
reached, not key validity, model access or billing safety. DNS/TLS/timeouts and
proxy rejection need investigation. Curl may use a different proxy/TLS path from
the runner's direct Python HTTPS client; curl success alone does not validate that
route. If needed, check that Python route with a separate unauthenticated GET using
the same `http.client`/`ssl` stack before any inference. No local Windows connection
has been tested from this cloud workspace.

## Estimated exposure and go/no-go

The public [Standard price table](https://developers.openai.com/api/docs/pricing)
was checked November 22, 2026, America/New_York: input $8/M, cached input $0.40/M,
30m writes $10/M, 12h writes $20/M and total output $40/M. Disjoint usage pricing
and the established reservation policy are reused. The first reserve is $0.32768
at 8,192 input and 4,096 output tokens using the highest frozen input category.
Two base reserves would total $0.65536, but the continuation reserve can grow with
reported token usage. Reservations settle into known estimates after each call;
the gate checks known spend plus the next outstanding reserve, not the sum of all
historical reservations.

Neither that illustration nor $1 is an invoice guarantee. The token allowances
are estimates, usage can be unavailable, and actual charges can exceed a reserve.
The previously verified $43 credit balance has not been rechecked. Current account
terms, credits, key/project permissions and model access remain unverified here.
No enforced account-level cap is assumed; the expected setting has been absent
from the owner's interface. The owner must explicitly decide acceptable residual
exposure, including whether billing can exceed credits or the local estimate.
Unrestricted paid billing, deliberate use beyond available promotional credits,
and further experiments are outside this proposal.

Paid authorization review requires passing offline checks, the exact source/plan
freeze, verified local connectivity, account checks and explicit risk acceptance.
A PASS authorizes no follow-on calls. Inspect the raw evidence before proposing
full-task calibration. PR #32, the original comparison/calibration plans, and
published historical results remain unchanged.

Technical request specification: [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling).
Real server acceptance, output adequacy and account-specific pricing are still untested.
