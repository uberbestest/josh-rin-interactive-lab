# Finalization Without Target Evidence

**What we tested:** Whether two recovered helpers still finalize on pending or wrong-job receipts after the historical absence predicate is repaired, and which additional checks prevent those operations.

**What happened:** The frozen 64-execution matrix found unsafe attempts in 11/16 recovered, 9/16 absence-only, 4/16 selected-status, and 0/16 status-plus-job executions. All sixteen positive controls completed safely. These are deterministic code executions, with zero fresh native participants.

**Outliers:** Ten executions physically completed both jobs despite an unsafe attempt. The full guard stopped with a safe joint continuation still available in eight cases. All eight auxiliary no-decoy executions lost their initial joint guarantee on the first pending query.

Record: **JRR-RECEIPT-GUARDS-2026-11-18-008**. Executed November 18, 2026 (America/New_York).

## What the result establishes

Readiness and job binding are separate checks. The recovered w041 helper finalizes unconditionally; w042 can accept another job's resolved status through a whole-response regex. Repairing the absence predicate removes the historical duplicate but leaves these paths intact. A selected-status guard blocks PENDING; matching returned and requested job blocks the explicitly misbound COMMITTED header.

Physical completion alone missed ten unsafe executions. Conversely, stopping before an unsupported action is only a guard: the full guard finished six of its sixteen tasks, then stopped in the other ten. Eight of those unfinished states still allowed both jobs to finish safely under the trusted-response assumptions. The two no-decoy cases had already spent away the worst-case joint guarantee. The service remains unsealed at each helper endpoint.

## Evidence and reproduction

The readable repository directory contains the source, protocol, summary and audits. The complete evidence ZIP contains all 64 run directories and their exact events and raw/shown transport records. Extract the complete archive before reproducing; the readable source index alone is not the full data directory.

From an extracted archive's parent directory:

```bash
python3 -B receipt-guard-study/reproduce.py --output reproduction.json
python3 -B receipt-guard-study/verify_witnesses.py --check receipt-guard-study/protocol/witness_checks.json
```

The output receipt must remain outside the extracted study. Reproduction validates retained records, then executes fresh deterministic copies; it does not call a model or add participants. Each chain is checked separately; cross-execution comparisons omit wall-clock timestamps, their dependent event hashes and runtime versions.

See [the protocol](protocol/PROTOCOL.md), [cases](protocol/cases.json), [source freeze](protocol/frozen.json), [source audit](protocol/source_audit.md), [observed results](results/summary.json), and [result audit](provenance/result_audit.md). The pre-run commit is `257591dd656e2fb8a54864e8139a0849d662c166`.

## Scope

Both helpers are model-mediated post-run recovered public source, not authenticated platform-log exports. Wrong-job receipts are explicit one-shot substitutions; the canonical service did not emit them. Canonical and shown bytes stay separate. Twenty initial witness-world executions concern canonical feasibility only; eight later-recovery witnesses depend on authentic subsequent responses. Thirteen isolated harness checks are separate from the 64 helper executions.

All comparisons are deterministic behavior of these authored programs and cases. They do not establish spontaneous model error rates, cognitive mechanisms, universal parser safety, independent replication or a complete recovery controller. Earlier studies and their recorded judgments remain unchanged.
