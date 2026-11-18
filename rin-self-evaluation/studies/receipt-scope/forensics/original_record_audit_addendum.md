# Addendum: the recovered w041 helper

This addendum supplements `round7-original-failure-audit.md` without changing that earlier audit. It records additional public-code evidence supplied after the first audit, distinguishes its provenance from the frozen Round 06 action log, and assesses its meaning for the failure. It does not contain a new native participant run or an inference about private reasoning.

## Newly available evidence

The original w041 context supplied a setup cell and the following helper, reporting that they were copied from its retained public tool-call record:

```javascript
for(const j of ["B","A"]){const run=async s=>JSON.parse((await tools.exec_command({cmd:load("p")+s+" --job "+j})).output);const r=await run("receipt");text(r);if(JSON.stringify(r).includes("ABSENT"))text(await run("commit"));text(await run("finalize"))}
```

The setup stores `python3 -B two-job-study/client.py --run w041 ` as `p` and requests initial status. The helper loops through B and then A, parses each receipt as JSON, prints the parsed result, searches the serialization of the **whole object** for `ABSENT`, conditionally commits, and then unconditionally attempts finalization. It does not test the top-level receipt status, bind the returned job to the requested job, or guard finalization on a resolved target receipt.

The equivalent recovered w042 helper searches the whole stdout string using `v.includes("ABSENT")`. Its additional `/ABSENT|COMMITTED/.test(v)` guard also searches the entire response. The two snippets differ in whether they parse JSON before searching, but both absence predicates have the same scope defect. Parsing JSON alone therefore does not distinguish the erroneous branch from a target-specific branch.

The source and provenance files were read and their hashes independently recomputed during this addendum:

| File under `delivery-study/forensics/` | SHA-256 |
| --- | --- |
| `w041_setup.js` | `91fb541e45b8f3ffeec4cb60338f61febe6d39bee69285f47ab51a47494f66d2` |
| `w041_helper.js` | `961d3af2e7d126fdb3c67af34778405342bacd72bde9a5c1aeac7c51966e3ba4` |
| `w042_setup.js` | `0588c4f760ac0233cd535cf60b1b6cbe08123d3a25489c646ebfe5846fa00ff1` |
| `w042_helper.js` | `bdaacadccb73bd85a71a8fe09896a4a2cdf370f7ff10272b10dd2106949095cd` |
| `extraction_provenance.json` | `bdd66d710f131e33ddb2acf11a5570b79621ebd6913d7f186c86ccb1cc975e27` |

The provenance records retrieval at `2026-11-18T22:47:09.449736+00:00`, identifies the original participant task names, and states that the requests forbade new commands, reads, edits, retries, and private reasoning. The expanded nested shell commands were not separately displayed in the extraction.

## What the retained observation makes these helpers do

The original audit established that the A receipt at event 4 has top-level `job: "A"`, `status: "COMMITTED"`, `transaction: "original-write"`, and `coverage: "AUTHORITATIVE_FINAL"`. Its complete nested status correctly contains both jobs:

| Field | A | B |
| --- | --- | --- |
| Original-write receipt | COMMITTED | ABSENT |
| Current delivery | present | present |
| Exactly one delivery | true | true |
| Fresh commits already made | 0 | 1 |
| Finalized | false | true |

B's historical absence is compatible with its later successful fresh commit and finalization. These fields do not demonstrate stale state or a contradictory receipt. They describe different jobs and distinguish an original write from current delivery.

Both recovered absence predicates evaluate true for this full A response because B's historical receipt is `ABSENT`. Both consequently request `commit --job A`, which produces a duplicate. Both then request `finalize --job A`, which the engine denies after consuming the final use. The correct target-status branch skips that commit and can finalize A at tick 7 with one use remaining. The original receipt itself leaves that route feasible.

This is now a concrete public-helper explanation consistent with the original action log, rather than a string-matching mechanism inferred only from actions. It remains a statement about the supplied code and retained observations. The extraction is **post-run and model-mediated**, not an independently authenticated platform export. Agreement with the action sequence does not independently authenticate the historical code text or establish an internal cognitive explanation.

## Separate deterministic comparisons retained by the investigation

The retained `forensics/retained/replay.json` and `forensics/README.md` report eight legacy-service executions: the two recovered helpers in each of four arms. I inspected these result records and the corresponding recovered source/provenance for this addendum. I did not launch additional participants or rerun that complete forensic suite as part of this read-only audit.

| Authored comparison | Retained result for each helper |
| --- | --- |
| Recovered helper, full combined receipt | Seven-event non-finish prefix exactly matches its original; B finalized, one duplicate, two unsafe attempts, tick 8, zero uses |
| Recovered helper, only receipt nested jobs projected to selected job | Both jobs safely finalized, no duplicate or unsafe attempt, tick 7, one use |
| Combined receipt, only absence predicate changed to the top-level status | Same safe endpoint |
| Combined receipt, additional returned-job binding and selected-status guard | Same safe endpoint |

The predicate-only edit is narrower than the hardened parser. For w041 it replaces `JSON.stringify(r).includes("ABSENT")` with `r.status === "ABSENT"`; it does not add a pending guard or a returned-job check. For w042 it changes only the absence condition to `JSON.parse(v).status === "ABSENT"`, leaving the pre-existing whole-response regex guard. These edits repair this particular recorded branch without establishing general parser safety.

The twelve separately retained routing fixtures compare recovered and hardened helpers on unrelated nested absence, target PENDING with unrelated COMMITTED, and a returned-job mismatch. Their outputs concern command selection; mock acknowledgements do not demonstrate delivery outcomes. The recovered w041 helper attempts finalization after PENDING without a guard, while the w042 whole-response guard may accept an unrelated resolved status. The hardened variants stop or reject the mismatch under those fixtures.

Neither recovered helper submits `finish`. The retained investigation separately replays the archived finish submission to compare the complete original sealed state. That extra replay is not an action generated by either recovered helper. The helpers also retain their fixed B,A loop; these deterministic results concern the original orientation and do not constitute reflected-case execution, new native error frequencies, or evidence of model retraining.

## Boundaries preserved

The original Round 06 records, prompts, receipts, and interpretation remain unchanged. The earlier audit's finding that action logs alone cannot identify a parser mechanism remains correct for those logs. The additional recovered code gives a specific sufficient mechanism with the provenance limitation stated above. It supports testing response scope and target-status selection separately, while leaving any broader conclusion about model competence, attention, or private reasoning unestablished.
