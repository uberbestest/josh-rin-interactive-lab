# The Refactor That Silenced the Bell

Josh & Rin · published 2026-10-27 · protocol v0.1

[Open the instrument](index.html) · [Methods](method.html) · [Full results](results/full-results.json) · [Protocol](PROTOCOL.md)

**A synthetic, SAAC-inspired engineering demonstration. Zero external model-agent runs.**
The gate is a short Python rule function, not a semantic model or a production SAAC
implementation. The public viewer replays its recorded results offline.

## Question

A legitimate code change can preserve business behavior while removing security
monitoring. Can a gate admit benign refactors but reject loss of the required controls,
without treating every changed byte as a threat?

The toy workload doubles a synthetic number. It emits in-memory markers representing
a monitor hook, an evidence receipt, a security alert, an effect, and optional ordinary
outreach. No real messages, deployments, protected-system accesses, or security
controls are performed. An alternative helper-based implementation provides a benign
refactor. Candidate flags change the modeled control behavior.

The gate checks a separately held policy: a monitor and approved, non-actor-writable
receipt must precede the business effect; severity 2 and 3 also require a security
alert before the effect. Evidence must bind the candidate and contain every declared
probe. Identity, repository authority, and deployment grants are explicit fixture
inputs. Missing deployment authority yields LIMIT to preview; missing observation
evidence yields CHALLENGE. Neither permits deployment.

## Observed results

| Denominator | Result | What it does not establish |
| --- | --- | --- |
| 21 predeclared named fixtures | 21 expected decisions matched: 6 ALLOW, 12 BLOCK, 2 CHALLENGE, 1 LIMIT | Real-world accuracy or agent behavior |
| 6 benign fixtures | All admitted; exact-build freezing rejected 5 | A production false-positive rate |
| 21 business-test checks | All passed, including all 12 declared failure cases | Sufficiency of business testing for safety |
| 512 finite configurations / 2,048 severity-probe executions | 3 ALLOW, 509 BLOCK; zero disagreement with the separate Boolean oracle | Universal control preservation; the oracle is also same-author |
| 2 assumption-breaking witnesses | Both falsely ALLOWed despite actual control loss | Observer authenticity or completeness of finite probes |
| 32 same-author Python regression tests | Passed in normal and optimized Python execution | Independent validation |
| Published-browser verification | 21 scenario decisions, 84 fixture views, 16 counterexample views; downloaded receipt matched | Mobile, offline browser execution, or independent validation |

The grid enumerates seven Boolean control flags, two alert thresholds, and two
execution routes. Its extremely unbalanced constructed population is not a deployment
distribution. It must not be presented as a 100% security or detection score.

### The two failures are central, not footnotes

1. **Unprobed trigger.** The four declared probes vary severity but all use payload 7.
   A hand-authored condition silently removes monitoring for payload 999. The ordinary
   evidence gate ALLOWs the build. The held-out payload produces no monitor, receipt,
   or required alert. This is an intentionally planted witness, not a discovered exploit.
2. **Dishonest observer.** A forged report supplies a good trace with the bad candidate's
   digest. The gate trusts the string identifying the observer and ALLOWs an unmonitored
   build. There is no signed attestation, authenticated collection channel, or real
   non-bypassable admission endpoint in this implementation.

## Positioning implication — inference, not validation

The meaningful authorization question is not just “may this identity edit this repo?”
but “does this exact proposed change preserve the protected controls under the delegated
task?” In this bounded model, a separate control-preservation policy distinguishes
selected safe changes from selected unsafe ones, while exact-build freezing cannot.

For Semantic Agent Admission Control, this suggests making protected-control preservation
an explicit condition of the action grant; binding decisions to candidate and policy;
keeping routine outreach separate from required security escalation; and distinguishing
insufficient evidence (CHALLENGE) from known failure (BLOCK). LIMIT must constrain the
permitted action, not merely label it. Here it means preview only.

That is design motivation, **not evidence that SAAC already solves semantic authorization**.
Unknowns include real agent behavior, natural-language delegation interpretation,
cross-system provenance, authentic observation, time-of-check/time-of-use binding,
operating-system enforcement, and production false-alarm rates.

## Trust and privacy boundary

The fixture traces are not real external observations: the candidate toy pipeline emits
them. Receipt integrity and sink custody are modeled fields, not enforced storage
properties. SHA-256 binds bytes but authenticates neither agent nor observer. No chained
delegation, cryptographic identity, or signed receipt implementation is included.

The minimal decision record contains case ID, candidate/policy/evidence digests, decision,
reason codes, a deployment-permission Boolean, and `signature: null`. It contains no
prompts or conversations. This demonstrates a narrow record schema, not a proven privacy
protocol: hashes can still identify or correlate data and are not anonymization. The
full downloadable results deliberately contain **synthetic** traces for inspection.

## Reproduce

From the repository root, using Python 3.10 or newer (tested with Python 3.12.14):

```sh
python -B -m unittest discover -s experiments/silent-bell/research -p 'test_*.py' -v
python -O -B -m unittest discover -s experiments/silent-bell/research -p 'test_*.py' -v
python -B experiments/silent-bell/research/experiment.py --check
python -B experiments/silent-bell/research/build.py --check
node experiments/silent-bell/research/static_check.cjs
```

To regenerate the records, HTML, and checksum manifest:

```sh
python -B experiments/silent-bell/research/build.py
```

The browser instrument is self-contained and can be opened directly from a file or served
with the repository's `python -m http.server 8000` preview. It makes no network calls,
uses no tracking or persistent storage, and does not run a model. Downloaded receipts
are generated locally in the browser. Browser-specific download policies can vary.

The [release verification record](results/release-qa.json) separates executed checks from
unexecuted coverage. We checked the live published site in cloud Chromium; the standalone
`research/browser_check.cjs` was not executed because the local Chromium download was
unavailable. It is provided for optional reproduction and requires Playwright plus Chromium;
neither is needed for Python reproduction or viewing. Mobile rendering and offline file-URL
execution were not verified. `results/SHA256SUMS.txt` hashes
every exhibit file except the manifest itself and Python cache files. The protocol hash
is also embedded in the results. These are reproducibility aids, not signed attestations.

**Publication status:** public source, authored fixtures, complete grid, both counterexamples,
same-author tests, and interactive replay. No live deployment of SAAC, independent review,
or new external-model experiment is claimed. No open-source license has been selected
for this exhibit; public visibility is not a reuse license.
