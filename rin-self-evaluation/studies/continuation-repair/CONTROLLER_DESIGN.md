# The guard that keeps the job: candidate controller

**What we tested:** This candidate is designed to turn the Round 08 stopping guard into an observation-driven continuation policy: preserve exactly-one evidence, respect shared resources, and finish the greatest number of jobs that the public contract guarantees.

**What happened:** Implementation and seven small constructed development checks completed. The separately authored evaluation matrix has not been read or run by the controller author. No held-out result is asserted here.

**Outliers:** The implementation deliberately leaves an unresolved job with unbounded receipt timing outside its finite completion guarantee. It can still finish the other job. A rejected response requests a fresh trusted status rather than ending the entire task.

## Interfaces

`controller.py` uses only Python's standard library. It imports no reference engine, case file, service client, hidden state, or oracle. It performs no filesystem reads, network operations, shell calls, or credential access. All inputs enter through its API or JSONL standard input.

Create one `ContinuationController` per independent task. Call:

```python
decision = controller.next_action(public_status)
validation = controller.observe_response(request, response)
```

`record_response` is an alias for `observe_response`. The module also exposes a stateless `next_action(public_status)` convenience function. The stateless form forgets previous pending observations; the class is the intended evaluation interface.

A decision contains `action`, optionally `job` or `ticks`, a two-element `guaranteed_value`, and a `proof` record. The objective is lexicographic: guaranteed count of safely finalized jobs first, then guaranteed completion of the declared priority job. A `finish` decision also contains a `report` with both jobs' evidence and completion state. The `proof` is a local search witness and accounting record; it is not an independently checked formal proof object.

The worker can be run as `python3 controller.py --jsonl`; arguments are unnecessary and ignored. It reads one JSON object per line and writes one result per line:

```json
{"op":"decide","status":{"...":"trusted public status"}}
{"op":"observe","request":{"action":"receipt","job":"B"},"response":{"...":"shown response"}}
```

The process retains only the observations for that task. Input or contract errors return `action: null` and an error description. They do not issue a service action. Response validation returns `accepted`, `needs_fresh_status`, and `reason`. A rejected response does not itself produce a `finish`, `commit`, or `finalize` request.

## Information boundary

The trusted `status` contract is essential. It exposes resources, deadlines, original-write receipt knowledge, acknowledged recovery-write counts, exactly-one evidence, finalization, and public receipt timing. After each service response, the adapter obtains a fresh authentic status before requesting another decision. It must not substitute an untrusted response's embedded status for this independent read after a response rejection.

This matters especially for the Round 08 wrong-job substitution. The service's genuine receipt action can have updated its local facts even though the displayed response header has been replaced. A fresh authoritative local status can recover those facts. Recovery via this channel is part of the declared synthetic service; it is not a demonstration that arbitrary corrupted remote receipts are recoverable without an authoritative alternative.

Pending timing evidence is retained only from a correctly bound `PENDING` response with `original-write` and `NOT_ESTABLISHED`. The end tick follows from the preceding trusted status plus the declared two-tick query duration. An accepted final original-write receipt remains immutable across subsequent trusted statuses. Other jobs' nested status text is never searched for a marker that would authorize the selected operation.

The implementation checks the selected job, operation-specific transaction, coverage, and fresh-write or finalization acknowledgement. It also rejects backwards counters, disappearing finalization, changing acknowledged-write counts, changing authoritative original receipts, and a changed task contract. This is structural checking under the synthetic transport assumption. It is not cryptographic authentication, a request-ID replay defense, protection against arbitrary same-job fabricated responses, or general authorization revocation support.

## Search construction

The planner has a separately written symbolic state representation. Each job is unresolved, known absent, known exactly-one present, finalized, or known duplicated. An unresolved bounded job also retains the possible readiness ticks consistent with its public timing contract and any accepted pending observations. The other state variables are remaining shared uses, current logical tick, and remaining service attempts.

This representation tracks observation-equivalence classes rather than selecting the fixture's actual hidden world. The original outcomes are independent under the published contract. On a query, readiness points at or before the completion tick can return either authoritative absence or authoritative commitment. Later readiness points form a pending branch. Search takes the worst attainable guarantee over those branches, then chooses the best safe action. It can therefore plan an early informative query when both outcomes retain the guarantee, or wait when an early query would merely waste a limited use.

The legal write choices are constructed from established evidence: commit only from known absence with no acknowledged recovery effect, and finalize only from exactly-one presence. Every selected authenticated action must fit the selected job's inclusive deadline and available shared uses. A service call consumes one action; a wait consumes one action and the chosen logical duration. The solver enumerates every legal wait length from one through twenty while unresolved bounded timing could change what is observable.

Three reductions remove actions that cannot improve this objective:

1. A query that is certain to be pending is dominated by a two-tick local wait. Both use one service attempt and two ticks; the wait spends no credential and loses no possible information.
2. Querying an already known immutable original receipt provides no new delivery evidence. A wait is no more expensive if advancing time is useful for the other job.
3. An unresolved receipt with no finite readiness guarantee cannot guarantee its own completion in a finite remaining horizon. Queries or waits devoted to that job can be removed from a worst-case completion policy without harming the other independent job. The report preserves that unresolved state rather than claiming impossibility in every favorable hidden world.

The algorithm memoizes values of symbolic public states. It may stop searching a state once it finds the maximum possible value, two finalized jobs including the priority job. At execution, it selects a first action whose worst-case continuation value equals the state's optimum. If the optimum equals what is already finalized, it produces a truthful final accounting instead of spending resources on an unsupported promise of further guaranteed completion.

The exactness claim is confined to this two-job, independent-outcome, stable-authorization, finite-action synthetic contract. Arbitrary correlated hidden worlds, external events, different action costs, lost acknowledgements without authoritative status, and production runtime failures require a different model. No compute-time performance guarantee is made for arbitrarily large public parameters.

## Development and evaluation separation

Seven hand-constructed development checks covered two known deliveries; bounded delayed coverage; a scarce-use priority choice; one unbounded unresolved job; a deadline-impossible pair; branching early/late receipt readiness; and wrong-job rejection followed by pending-state scheduling. Their arithmetic expectations were written directly in the smoke command. They are development checks, not additional model participants, independent replication, or the pending evaluation matrix.

The author read the prior public engine and contract to understand the interface. This is a separately written planner with a different state representation, not a blinded independent reimplementation. It is appropriate to compare its actions against separately retained reference-engine audit fields, while labeling that comparison as same-lab verification.

No learned model weights, persistent model capability, or population failure rate are changed or measured by this module. The proposed improvement is a retained, inspectable execution scaffold. Its acceptance requires the separately authored cases, matched baselines, negative controls, and preserved full traces that the parent study will provide.

## Operational boundaries

The controller does not call any external service. The study runner must enforce the observation boundary and execute commands, preserve both raw and displayed responses, retain rejected headers, query genuine status after failures, and stop on unsupported input. The controller's `finish` report does not erase unfinished work or prior violations. Its guarantee describes safe continuation from the supplied public state; it cannot infer unexposed earlier unsafe attempts from that state.

The code does not establish a software license for the existing lab collection or choose terms for a paid engagement. Public source, if subsequently published, remains subject to the lab's existing licensing decision.
