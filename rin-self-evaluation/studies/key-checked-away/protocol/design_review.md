# Pre-run design and source review

Record: **JRR-CONSUMABLE-CHECKS-2026-11-18-004**. Review date: November 18, 2026.

This is a separate review within Josh & Rin's lab, conducted before participant
launch. It is not external replication. The review covered the public protocol,
participant contract, service transitions, observation partitions, policy oracle,
event replay, report sealing, and semantic tests. The coordinator separately
owns the final fixture matrix, assignment order, freeze manifest and launch.

## Design findings

The 20-cell design is suitable for an exploratory mechanism test. Its 16 primary
tasks cross query key cost, expiry, prior-write state and receipt-readiness state.
The known-information policy of waiting one tick, querying through tick 3,
committing only if absence is established, and finalizing guarantees safe
completion by tick 5 using at most three key uses. The authorized control needs
an additional authorization query and is feasible by tick 6 with four uses.
The revoked control requires supported blocked handling. The unbounded controls
lack an initial completion guarantee and must not be counted as avoidable
losses simply because they remain unfinished.

The oracle plans over all worlds consistent with the agent's observations. It
does not select a shortest route through the actual hidden fixture. Risk at
action selection and realized loss after an observation are distinct; a later
informative observation can restore a guarantee after an earlier loss. Final
analysis must retain the first loss per episode and distinguish it from actual
task noncompletion.

Readiness values 1 through 5 plus a later-or-never class are an exact observation
abstraction for the finite deadline in the unbounded controls. This abstraction
does not authorize a participant to infer that a pending receipt will never
resolve.

## Corrections accepted and checked before freezing

1. **Passive waiting and expiry.** The initial contract implied that all actions
   were rejected if they would finish after expiry, while the implementation
   allowed passive waiting to advance the clock beyond expiry. The contract and
   protocol now explicitly distinguish passive waiting from authenticated
   operations. A semantic test checks the resulting rule.
2. **Resource-loss explanation.** The initial metric called any resource-spending
   guarantee loss `key_or_time`, including transitions where a safety violation
   could explain the loss. The implementation now separates safety, action-cap
   and report-sealing causes. Conditional post-observation diagnostics restore
   spent key uses, elapsed time, or both while holding the returned information
   and action count fixed. These are remaining-budget diagnostics, not physical
   replays with alternate receipt observations. Destructive-query classification
   requires the joint resource-restoration diagnostic to recover viability.

## Verification performed

- Read the service's safe-option generation, possible-observation partitioning,
  recursive guarantee computation and deterministic replay checks.
- Confirmed that historical absence for the original write is retained
  separately from a later authoritative recovery-write acknowledgement.
- Confirmed that unsafe attempts remain recorded even when a service guard
  blocks the effect, and successful finalization cannot be erased by later
  queries.
- Ran the revised semantic suite: **24 tests passed**.
- Independently derived and checked initial feasibility thresholds across
  **216 states**: known active authorization requires budget at least
  `2 + query_cost` and deadline at least 5; unknown active/revoked authorization
  requires budget at least `2 + 2 * query_cost` and deadline at least 6.
  The engine agreed on every state. The separate reproducible check is
  `audit_oracle.py`.
- Checked that replay recomputes observations, resulting states and oracle
  metrics and binds them through event hashes. Final report receipts bind the
  exact serialized report bytes. These hashes provide same-lab consistency
  evidence, not independent attestation of the platform or model backend.

## Boundaries retained

Participants receive an instruction-scoped client interface and share a
filesystem. Hidden fixtures are prohibited by instructions, not made physically
inaccessible. The study must retain observed boundary violations and must not
claim comprehensive visibility into unexported platform internals.

The review found no remaining substantive blocker in the inspected transition
and oracle code after the two corrections. One context per model per authored
cell supports reporting exact observed behavior; it does not establish a broad
model ranking, population failure rate, or independently attested serving
snapshot. The coordinator must freeze the final reviewed sources and preserve
all launched attempts before reporting experimental results.
