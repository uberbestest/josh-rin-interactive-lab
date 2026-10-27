# The Refactor That Silenced the Bell — protocol v0.1

Josh & Rin · 2026-10-26 · SAAC-inspired, synthetic control-preservation experiment.

This protocol is written before the first suite execution. It specifies an engineering
demonstration, not an experiment measuring a language model's behavior. No external
model agents, live security controls, private data, or real notifications are used.

## Question

Can an admission rule distinguish ordinary, authorized code changes from changes
that remove required monitoring, alerting, or evidence integrity, without freezing
every byte of the application?

## Implementation boundary

An executable Python toy pipeline transforms a synthetic number and emits a trace.
Candidate configurations alter seven control flags, an alert threshold, and an
execution route. A second implementation performs the same work through a helper.
The gate checks traces against a policy held outside the candidate configuration.
It does not interpret natural-language intent or discover arbitrary code semantics.
The trace is a fixture stand-in for external observations, NOT an attested collector.
Candidate digests are SHA-256 bindings, NOT signatures or proof of identity.

## Frozen checks

All severity probes (0, 1, 2, 3) must show the monitor running before an effect.
Every effect must have a receipt written to a policy-approved sink with actor-write
disabled. Severity >= 2 must produce an alert to the designated security recipient
before the effect. The policy version must not change. Evidence must identify the
exact candidate, all required probes, and the declared external observer.

Decision order: identity/repository authority -> policy identity -> candidate binding
-> evidence origin/completeness -> trace invariants -> deployment authority.
Violations BLOCK. Missing evidence CHALLENGEs. A healthy candidate without deployment
authority LIMITs to read-only preview. Otherwise ALLOW is conditional on these probes.
LIMIT and CHALLENGE do not execute a deployment. Known violations take precedence.

## Comparators

1. Repository-permission-only: knows whether code/deployment access was granted;
   ignores protected-control semantics. This is a deliberately coarse comparator,
   not a claim about every IAM or CI product.
2. Candidate-owned tests: asserts business output only; cannot establish safety.
3. Exact source/configuration freeze: rejects any digest change, including benign
   refactors. It is not a useful semantic oracle.
4. External-policy evidence gate: applies the checks above to the supplied traces.

## Planned coverage and denominators

- 21 named fixtures: six benign changes, twelve known authorization/control failures,
  two missing-evidence cases, and one preview-only grant. Expected decisions are
  declared in the fixture table before execution.
- 512 configuration states: all 2^7 control-flag combinations, two alert thresholds,
  and direct/delegated routes. Each state runs four severity probes: 2,048 executions.
  This is a finite Cartesian product, not a natural distribution or an accuracy rate.
- Two deliberately excluded assumptions: an unprobed payload trigger and a dishonest
  observer. Both are expected to pass the normal evidence gate while hiding a loss
  of monitoring. They must be published, not removed from the results.
- Regression checks include decision precedence, benign variants, stale digests,
  each protected invariant, missing probes, preview non-deployment, and receipt
  minimization. A separate Boolean oracle checks the grid (same author, not independent).

## Falsification and interpretation

A benign fixture blocked by the gate is a false alarm in this declared model.
A known failing fixture allowed to deploy is a failure. Passing the suite establishes
only behavior on these authored examples. The held-out trigger and forged observer
are demonstrations that finite probes and untrusted receipts cannot prove universal
monitor preservation. Findings are NOT independently validated or production-ready.

## Publication

Publish the executable source, full finite records, tests, summary, hash receipt,
interactive viewer, and limitations in the existing public lab. No private lab
architecture, continuity material, personal correspondence, local paths, keys,
credentials, or model internals are included. No X or Substack post is part of this run.
