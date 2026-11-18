# Round 06 prospective design review

**Study proposal:** The Second Job Without a Checklist  
**Review date:** November 18, 2026 (America/New_York)  
**Status:** Design approved before participant dispatch, subject to the complete final preflight and source freeze. The shared contract, condition block, protocol, inherited-source bindings and matched initial states were inspected. No native participant was launched by this reviewer.

## Judgment and precise question

Use a new concurrent comparison of **48 fresh contexts**: the 12 unchanged Round 05 cases, crossed with two requested selectors and two reporting conditions, with one context per cell. This is an experiment on the **incremental requirement for explicit per-job reporting fields**, beyond the reminders and task structure that both conditions continue to receive.

The refined design approved in this review is:

- Both conditions require the common report fields `joint_complete`, `uses_remaining`, `tick`, and a string `summary` of at most 160 words.
- Both conditions may supply additional truthful fields or detail.
- CHECKLIST additionally requires `jobs.A` and `jobs.B`, each with the specified delivery, finalization, and barrier fields.
- OPEN does not require those entries and does not forbid voluntarily providing them or explaining the jobs in prose.
- Both receive the same operational objective, public facts, action rules, costs, deadlines, priority rule, evidence semantics, resource lower bounds, and client responses.

The shared instruction, “Do not omit the other job from your final accounting,” remains in the common contract. The status response still displays both jobs, and the common `joint_complete` field still explicitly represents the combined goal. This makes the manipulation narrow and interpretable. It does **not** remove every accountability reminder, create unrestricted reporting, or test goal tracking without scaffolding.

The common permission for extra fields is a documented change from Round 05's exact-key reporting rule. It applies equally to both new conditions. The control is consequently a new concurrent CHECKLIST condition, not an exact replication of the entire old prompt. The underlying service task remains unchanged. Do not use historical Round 05 runs as the causal control or pool them into the new condition denominators.

## Design issues resolved by the refinement

### Optional means optional, not prohibited

Requiring exactly four keys in OPEN would prohibit a volunteered `jobs` object. That would compare required with forbidden structured accounting, rather than required with optional accounting. The approved extra-fields permission resolves this problem. A partially populated optional `jobs` object in OPEN must not fail schema solely because an unrequired job or nested field is absent. Any factual assertion it does contain is still reviewable.

### Preserve planning information

Round 05 places useful operational information in its reporting section, including delivery-state meanings, the distinction between local barriers and global feasibility, and local lower bounds. Deleting that information only from OPEN would change the planning problem along with the reporting cue.

Keep the definitions and lower bounds in the shared contract/reference material. Isolate the arm difference to the required field structure and its reporting instructions. Informational definitions may still expose both job names and barrier concepts; that residual scaffold must be disclosed.

### Distinguish output coverage from execution

A required A/B form should increase the presence of A/B fields by construction. That observation alone would not establish improved goal tracking or task execution. Conversely, leaving out an optional object is not a failure. The main behavioral comparison should use the identical service-state and guarantee-preservation endpoints. Reporting detail and semantic coverage are separate secondary findings.

## Assignment and case inheritance

Retain the original Cxx-to-Fxx mapping, configurations, actual worlds, and public initial possibilities. Shuffle **dispatch order**, not the identity or content of the cases. Initial states must match across each four-cell family block after normalizing only the opaque run identifier. The reporting condition should be held in the assignment/prompt metadata rather than added as a behavior-relevant service configuration value.

The instrument author's proposed Williams orders are appropriate. Let:

| Index | Cell |
| --- | --- |
| 0 | older selector / CHECKLIST |
| 1 | older selector / OPEN |
| 2 | newer selector / CHECKLIST |
| 3 | newer selector / OPEN |

Use the four rows `[0,1,3,2]`, `[1,2,0,3]`, `[2,3,1,0]`, and `[3,0,2,1]`, each three times across the 12 seeded family blocks. Across one four-row cycle each cell occupies each ordinal position once, and all 12 directed adjacent-cell pairs occur once. Verify the resulting per-model condition-first and per-condition model-first counts mechanically before freezing. This balances dispatch order; it does not attest equal backend load, inference budgets, or simultaneous starts.

Use fresh contexts with no inherited conversation, the same inherited reasoning setting, the same normalized dispatch wrapper, and opaque run IDs. Do not put condition names, model names, hypotheses, prior outcomes, or expected actions in participant-visible metadata beyond the reporting requirement itself. A neutral client-directory name is preferable to a path that advertises the hypothesis. No within-cell reruns are planned.

The implemented catalog updates only top-level metadata to describe the new condition design. I checked that the complete case array remains equal to Round 05, including IDs, configurations, hidden actual worlds and expected values. `lineage.json` binds both catalogs and the unchanged canonical case array. The new `assignments.json` is authoritative for the current 48 contexts.

## Endpoints and denominators to freeze

For **each selector and reporting condition**, there are 12 runs:

| Endpoint / stratum | Denominator per selector-condition cell |
| --- | ---: |
| Safe joint completion and joint-guarantee preservation in initially joint-guaranteed cases | 8 |
| Priority optimum attained in hard budget/deadline controls | 3 |
| Priority optimum attained in unbounded-receipt control | 1 |
| Common report fields, safety, duplicate effects, and descriptive resource totals | 12 |

Across conditions, each selector has 24 runs, but do not collapse the condition contrast into a single accuracy number. There are 12 paired CHECKLIST-versus-OPEN comparisons per selector and 12 paired model comparisons within each condition. These are two views of the same 48 observations, not two independent datasets. Primary treatment comparisons have eight case pairs per selector. There is **one fresh context per family-selector-condition cell**; no within-cell repeat agreement can be estimated in Round 06.

For each paired endpoint, report the four descriptive cells: both meet it, CHECKLIST only, OPEN only, neither. Retain case-level action sequences and first-loss events. Do not convert a single discordant pair into a claim that the prompt requirement deterministically caused that individual run's behavior. Authored cases and one sample per cell support a bounded condition comparison, not a population reliability estimate, general model ranking, or broad equivalence claim.

### Common behavioral endpoints

Reuse the unchanged engine/reference meanings:

- Factual finalizations, job-local safe completion, and whole-trajectory safe completion remain separate.
- Safe joint completion is assessed only against the eight initially joint-guaranteed families for the primary endpoint.
- Risk at action selection, realized value loss, actual completion, and query-specific resource-loss diagnosis remain distinct.
- Preserve the first risky selection and first realized loss even if a favorable observation later permits completion.
- Separately identify a loss **at sealing**, using the pre-finish public-information value and the terminal safe value. Do not infer “forgot the goal” from that behavior; record the avoidable loss itself.
- An initial constraint is not an actor-caused loss. In F12, an honest stop after safely finalizing priority B can already attain the initial `(1,1)` objective. Optional A queries are not required by that objective, and pending does not prove permanent nonresolution.

### Common mechanical report endpoints

Assess the three common factual fields using strict JSON types and actual terminal state: Boolean `joint_complete`; integer, non-Boolean counters; and the common summary type/word limit. Separate common-format validity, common factual accuracy, and false positive completion claims. Python equality alone is insufficient because `True == 1`.

CHECKLIST-required field validity and exactness have a CHECKLIST-only denominator. OPEN's missing optional fields have no error count. Facts volunteered in either condition remain subject to the same evidence-based truth checks. Conservative underclaims, unsupported positive claims, contradictory statements, and absent statements should not be collapsed into one error type.

The client must continue preserving submitted valid JSON objects without filling in either job, translating prose into a repaired report, or correcting unsupported claims. The native report, logged finish submission, and received seal line remain separately retained and hash-bound.

## Semantic rubric and review procedure

`SEMANTIC_REVIEW.md` is the separate prospective rubric and raw judgment-file contract. It specifies whole-report completion accounting as explicit, inferable, not recoverable, or contradictory; separates coverage from factual support; accepts collective claims and unique report-based inference; and separately records delivery-knowledge and barrier detail.

The planned fresh review agent receives a shuffled packet with model/condition/case/run labels withheld. Exact reports and public observations are retained; hidden fixtures and oracle outputs are excluded. Structure and style can still reveal condition or suggest identity, so masking is incomplete. The raw judgment file binds the exact packet digest and every record's input hashes. The mapping is revealed only after all 48 bound judgments are sealed. This is same-lab model review, with coordinator checking and any adjudication preserved; it is not human review or external replication.

The main protocol aligns with this rubric. Its denominator table keeps eight primary cases, three hard-ceiling controls, and one unbounded control per selector-condition cell. It keeps common-core report accuracy separate from required checklist compliance, retains the existing accounting reminder, and explicitly warns that a report containing fewer assertions has fewer opportunities for factual error.

## Required pre-freeze checks

1. Verify the copied engine, client, oracle/audit, and inherited core tests against Round 05 hashes where byte identity is claimed. Verify all 12 case records and actual worlds against the inherited catalog.
2. Verify the four states within every family differ only in opaque run ID. Verify the conditions do not change public status or service responses under a fixed action sequence.
3. Construct the prompts from a common text plus one isolated condition block. Export a normalized diff and an explicit inventory of every difference. Ensure information/lower bounds and the common accounting reminder appear identically in both.
4. Verify exactly 48 unique family-selector-condition cells, balanced Williams positions/order, one normalized dispatch wrapper, and exactly two intended normalized prompt variants.
5. Exercise common-core scoring with both conditions, optional and absent jobs objects, partial optional details, required missing CHECKLIST fields, false common completion, conservative underclaims, contradictory extra claims, and strict Boolean/integer types. These are instrument checks, not native samples.
6. Verify that a valid OPEN report can seal without a jobs object; a volunteered jobs object can also seal; the client neither repairs nor rejects factual/schema deficiencies beyond transport validity. Preserve exact bytes and native seal behavior.
7. Re-run the inherited semantic tests and oracle audit without altering their meaning, then hash and commit the final protocol, rubric, source, assignments, states, prompts, and dispatch messages before participants begin.

## Checks actually completed by this reviewer

- The six files declared byte-identical in `lineage.json` match both their recorded SHA-256 values and the original Round 05 bytes: engine, client, oracle audit source, feasibility record, engine tests, and client test.
- The full 12-case array equals the original array; only catalog metadata changes.
- All 12 families have four initial states that match after removing only the opaque run ID.
- No native event rows were present at this review's source inspection.
- The current common contract retains the accounting reminder and planning information; the added block alone requires the explicit A/B checklist. Both arms permit truthful additional fields.
- The current main protocol matches the approved question, assignment, one-context-per-cell structure, denominators, masking limits, no-rerun rule, and publication scope.

The instrument author separately reported successful source tests and oracle checks while implementation was being completed. This review does not substitute that report for the coordinator's final preflight, nor claim to have independently re-proved the oracle or run the unfinished complete suite.

## Scope and reviewed document fingerprints

This is a separate-agent, same-lab prospective design review. I inspected the prior public contract, protocol, preparation logic, client, scorer, reporting review, and relevant engine interfaces; discussed the new manipulation with the coordinator and instrument author; inspected the new common contract, added requirement block and main protocol; and checked the inherited source and initial-state bindings listed above. I authored this design review and the semantic review rubric. I did not launch participant models or change the old study, new service engine, client, assignments, prompts, or participant files.

The final freeze is authoritative. If a reviewed document changes substantively before freezing, reassess the affected conclusions. Fingerprints identify the versions inspected for this review:

| Document | SHA-256 |
| --- | --- |
| `COMMON_CONTRACT.md` | `ac4529053ceb6f255301ade6a28fcfbb46009bcf0d0b0e7f54f0a9450e6b143b` |
| `CHECKLIST_REQUIREMENTS.md` | `19c8815054ee983631ef71345f361ec7952d254f465c43c690b2e212c902e59a` |
| `PROTOCOL.md` | `55346194090fd04580b76aec616492d285416847215e0465fa3a3cc0bfa050f3` |
| `SEMANTIC_REVIEW.md` | `68af79eb70594bc4322831b0d5a0672e2141ebe318593e4411b246c0ac95ea8d` |

**Conclusion:** Approved as an incremental mandatory per-job reporting-scaffold comparison, conditional on final preflight and prospective freeze. The retained accounting reminder and global completion field make the scope narrower than unrestricted reporting; that limitation governs interpretation of both positive and null findings.
