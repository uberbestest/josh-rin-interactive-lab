# Pre-freeze source audit

**Status:** No blocking defect found in the inspected source. This is a same-lab source review, not external replication or an endorsement of eventual experimental results.

**Scope:** Inspect the authored deterministic replay infrastructure and eight-case design before the principal matrix executes. No new study matrix, participant trial, or native-model call was run or inspected during this review. The reviewer read the previously completed Round 07 sources and the proposed Round 08 sources. Design arithmetic is prospective reasoning, not an observed result.

## Checks actually performed

- Read the complete new `execute.py`, `run_helper.mjs`, `reproduce.py`, all ten helper/setup files, case matrix, lineage records, and the inherited client. Read the existing engine, common contract, original recovered-source documentation, and legacy replay inputs.
- Ran the ten transport unit tests in `tests/test_transport.mjs`. All ten passed. The tests call the response transformation and command grammar directly and make **zero actual service calls and zero matrix executions**.
- Parsed all four Python sources (`execute.py`, `reproduce.py`, `input/client.py`, `input/engine.py`) with Python's AST parser. Compiled all ten helper/setup sources inside async wrappers using Node's VM parser without evaluating the wrappers. All syntax checks passed.
- Checked all ten lineage entries against both their declared SHA-256 values and the existing Round 07 source bytes. Separately checked the complete common contract, extraction provenance and legacy initial-state bytes against their inherited sources. All thirteen inherited-file comparisons passed.
- Confirmed eight unique cases, two helper identities, four arms and 64 assigned executions. Exactly two cases use the response adapter. All eight cases start with six uses.
- Confirmed each wrong-job case has the same config and actual world as its corresponding PENDING case. Confirmed the no-decoy case changes only A's initial receipt in the config relative to PENDING/absent, with the same actual world. Confirmed the legacy case's config, apart from the temporary run identifier, and its actual world match the archived C11 initial state.
- Confirmed each new status-only guard is exactly its inherited status-and-job guard with only the job-mismatch statement removed. Original loop ordering remains B,A. Recovered, predicate-only and status-plus-job sources retain their inherited bytes.
- Searched the reviewed text inputs for private scratch, runtime-home and export-directory absolute-path prefixes; none occurred. Temporary runtime paths are supplied to the harness but are not stored in its transport output. This was a focused path-disclosure check, not a comprehensive secret scanner.

## Execution and evidence integrity

The runner verifies the freeze before executing the matrix. Its required frozen-input set includes all executable helper/setup files, the matrix, client, engine, runner and reproducer. Each cell receives newly created temporary copies of the real unchanged Python client and engine. The helpers are executed as JavaScript, and their command strings pass a fixed grammar before `spawnSync` invokes the client directly. No shell is used. The VM is described correctly as an offered-interface restriction rather than an operating-system security boundary.

Each submitted command retains the exact canonical stdout and the exact shown stdout, with byte counts and hashes. The canonical client event journal retains the engine's original response. The wrong-job adapter does not edit service state or event files. It requires canonical B PENDING with A's exact-delivery evidence known and B's evidence unresolved; it changes only the top-level `coverage`, `job` and `status` fields. All nested local status remains canonical. Only the first selected B receipt is transformed. Other commands, A receipts, and later B receipts retain authentic output.

`analyze_run` independently reconstructs expected initial states, replays each canonical event chain, recomputes state transitions, verifies every raw and shown response, verifies command identity and source hashes, and checks the expected mismatch exception. Its outcome fields distinguish attempted/admitted operations, unsafe-attempt increments, actual new deliveries, actual finalizations, key/time costs, and continuation value. The response adapter's mismatch is not mistaken for an authentic B receipt.

The canonical engine's safety assessment remains appropriate for these selected mismatch cases: canonical B is unresolved, shown nested B is unresolved, and the substituted top-level receipt explicitly names A. Thus there is no target-matched exactly-one evidence for a B finalization. This conclusion is specific to these cases; arbitrary output substitutions would need a separately justified observed-evidence assessor.

The reproducer first validates retained journals and recomputed analyses, then by default reruns all frozen helper sources in fresh temporary services. It compares states, actions, observations, oracles, commands, output bytes and derived results. It excludes wall-clock timestamps, hashes that bind those timestamps, and runtime version strings from cross-execution equality while verifying each individual event chain. Its verify-only option does not perform a new helper execution and must be reported accordingly.

## Interpretation requirements

1. The helper guard's `break` exits the entire B,A loop. `stopped_with: null` can mean this deliberate early stop as well as ordinary completion of the loop. Use actual finalization and continuation fields when describing completion. A stopped guard is not a completed recovery strategy.
2. In A-known PENDING cases, after the first query ends at tick 2 with five uses, a second B receipt ends at tick 4. If B is absent, commit B at 5, finalize B at 6, and finalize A at 7; if B is present, finalize B at 5 and A at 6. This prospective witness preserves both completions. The corresponding mismatch witness requires the explicit one-shot corruption premise and a later authentic receipt.
3. The no-decoy case leaves A uncertain. After its first PENDING B query, worst-case both-absent completion needs six further uses but only five remain. Do not reuse the A-known case's joint-guarantee claim. This case isolates the immediate source-routing response to available A evidence; it also changes the planning information and has its own continuation baseline.
4. The same unsupported B finalize can fail physically in the absent world or succeed in the present world. Report both. Physical success does not establish pre-action evidence retrospectively.
5. The inherited engine defines whole-trajectory safe utility as zero after any unsafe attempt. This does not erase an independently completed job, prove every physical continuation impossible, or independently identify a resource bottleneck. For the absent PENDING world, the clock arithmetic separately shows why spending tick 3 on unsupported finalization leaves no time for receipt, commit and finalization by B's deadline 6.
6. The all-ABSENT positive control deliberately makes A initially and actually absent. This prevents the later COMMITTED-A branch from serving as another historical-ABSENT spillover case. The controls are authored examples, not a fully crossed inference about source-variable effects.
7. The scope ends at these 64 authored executions. Recovered source is still a post-run model-mediated copy, not an authenticated historical platform export. No native incidence, internal reasoning, generic parser-safety claim, or retraining effect follows. Post-commit acknowledgement validation remains outside this repair matrix.

## Reviewed source identities

Hashes below bind the exact inspected source snapshot. The principal matrix had not executed when this audit was written. A later source change should be identified rather than silently described as reviewed by this document.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `execute.py` | 17182 | `4606548cafaa541b8e751995caf7a2cc20840d0f0c409adfd040ab275bcdfde9` |
| `reproduce.py` | 3762 | `1edecea4aaae62d9454ce1a6984b506cfb1de765997d7949f7945aa0756ac17f` |
| `run_helper.mjs` | 4974 | `4ddf1bdf0ec4bc16f738dd7bc1b2fe5be58b30756818107f5188f96516f5eb29` |
| `tests/test_transport.mjs` | 2780 | `ff8fc82803e411b3385172607b5aa375c0cb87dea53b029647419c0b30dc00b2` |
| `protocol/cases.json` | 9341 | `59ca33a3818b5396c194cacb14134e4a174662795044d63b0ab112ecda9e5a32` |
| `protocol/lineage.json` | 2691 | `9482d6e12490ff07926ae90fe83431caf7704a39191df4a0ed53e7ac9a0045ed` |
| `input/client.py` | 4460 | `e35c9f76f8ee384cf62e8ab29e443c5d021768f7a51aea1c847d3b4ad4046e6a` |
| `input/engine.py` | 22989 | `91599442030c1066ff5f75c328b6c818dde1fd52a203074e6257f87faed6f2ec` |
| `input/COMMON_CONTRACT.md` | 7901 | `ac4529053ceb6f255301ade6a28fcfbb46009bcf0d0b0e7f54f0a9450e6b143b` |
| `input/legacy_initial_state.json` | 2666 | `a03674858c5f1d1fbf500fb98f105042d06e3c780726cbbd606dfd4b5bb1d7e5` |
| `input/extraction_provenance.json` | 1938 | `bdd66d710f131e33ddb2acf11a5570b79621ebd6913d7f186c86ccb1cc975e27` |
| `helpers/w041_predicate_only.js` | 237 | `0aa12cf51670379755c01cb8fc502c4a3c56ff520270ac08d75b2ca32e4b5f4a` |
| `helpers/w041_recovered.js` | 254 | `961d3af2e7d126fdb3c67af34778405342bacd72bde9a5c1aeac7c51966e3ba4` |
| `helpers/w041_setup.js` | 126 | `91fb541e45b8f3ffeec4cb60338f61febe6d39bee69285f47ab51a47494f66d2` |
| `helpers/w041_status_guard.js` | 290 | `d934c1a2ca9fe3a08c94c6f3f12878f30a586a7271a04b0ce11b9d4d97504cc3` |
| `helpers/w041_status_job_guard.js` | 343 | `c643539d7262144a871a7078f1db86ebc0e406ad5c777ba084b3f5998435575f` |
| `helpers/w042_predicate_only.js` | 262 | `f50c3a52c16fa89a51cf535508f4ca3886b9914823030bcc8d51f301408d101f` |
| `helpers/w042_recovered.js` | 251 | `bdaacadccb73bd85a71a8fe09896a4a2cdf370f7ff10272b10dd2106949095cd` |
| `helpers/w042_setup.js` | 126 | `0588c4f760ac0233cd535cf60b1b6cbe08123d3a25489c646ebfe5846fa00ff1` |
| `helpers/w042_status_guard.js` | 312 | `bea420b19908d34ac5d29bf88359599754c65fd968c4eebc0f64fc8570a3325c` |
| `helpers/w042_status_job_guard.js` | 371 | `ef6bac8ec14f487a0ced9d02f2979e0126ff3439e30eeb038a632856f77ddace` |

## Pre-freeze witness and protocol appendix

Reviewed at **2026-11-19T01:04:45.425528+00:00**. The 64-cell principal helper matrix had not executed. This appendix adds a review of the authored feasibility checks and prospective protocol; it does not add principal observations.

Ran `python3 -B receipt-guard-study/verify_witnesses.py --check receipt-guard-study/protocol/witness_checks.json` after the scope clarification. The retained record matched recomputation: **28 witness-world executions, comprising 20 initial canonical-service schedules and 8 post-pending trusted-recovery schedules**, all with safe joint completion in their stated settings. The same public worlds recur under paired case labels; these are arithmetic checks, not independent samples. No recovered helper or CLI service matrix was executed by this check.

The schedule choices are authored from public timing and receipt evidence. Their independent arithmetic tracks ticks, uses, action count, original receipts, fresh commits and finalization; each step is then compared with the inherited transition function. The optimizer does not choose the witness policy. Enumerating public-consistent worlds verifies both absent and present branches rather than only the selected actual fixture.

The no-decoy budget statement is correct: initially, waiting two ticks permits the B receipt at 4, B completion at 6 in the absent branch, and A completion at 10 in the both-absent branch, using all six uses. Querying B immediately adds a spent use without obtaining decisive evidence; the worst-case completion route then needs seven total uses. Five remain after that first query, while six more are necessary. This is separate from any later readiness error.

For the known-A absent PENDING case, unsupported B finalization after the first receipt consumes tick 3. The contract still requires an authoritative original-write receipt before the fresh commit. The earliest such receipt then ends at 5, commit at 6 and finalization at 7, beyond B's inclusive deadline 6. This proves the stated timing obstruction for B under the contract; it is not inferred solely from the engine's zero whole-trajectory safety score. The same argument does not describe the present-world case, in which unsupported finalization may physically succeed.

A scope issue was found and corrected before freeze: the initial schedules call the canonical engine directly, and the delayed first B query falls outside the adapter's required PENDING exposure. These rows now explicitly state `transport_adapter_exercised: false` and describe canonical-service feasibility only. Post-pending recovery rows discard the first result and require authentic later responses; the wrong-job versions explicitly retain the one-shot fault assumption. Transport tests and the principal matrix separately exercise the adapter. The protocol now states these limits. No arbitrary persistent-fault guarantee is implied.

The freeze builder's initial self-scan contained the same literal private-path prefix it intended to reject. This was caught by source review and corrected before execution by constructing the prefix from separate components. A read-only emulation of its candidate path scan passed for 28 current files. The freeze builder itself was **not run by this reviewer**. Its Python syntax and the witness verifier syntax both parsed successfully.

Read the complete prospective protocol. It preserves all 64 assigned records, separates physical from evidence-compliant outcomes, gives the no-decoy case its own baseline, treats guard stops separately from completion, and limits claims to deterministic programs in these selected cases. No model ranking or native error rate is planned.

| Additional reviewed file | Bytes | SHA-256 |
| --- | ---: | --- |
| `verify_witnesses.py` | 8755 | `841011c2304422cff8ba4a3fe9659ffc0bada2c648e4b8b1931b1579b2f82303` |
| `protocol/witness_checks.json` | 48445 | `b380467806746e5f21b6e2be09d7ce85d055e39b2d2455859871141cb14cbe13` |
| `protocol/PROTOCOL.md` | 12163 | `e0374865d6f4a6f32d4b2bbd045efe260f35957be6fde335276a4b3a55a82e0d` |
| `freeze.py` | 1930 | `6ec487c179aed2ae5c85e778be4e5bbfe7db9ffc2a6d671f124f2e8de8e7230f` |

## Infrastructure-retention correction and final source closure

Reviewed at **2026-11-19T01:05:40.953168+00:00**, before the principal matrix. A second source defect was identified before freeze: the original runner copied temporary canonical files only after a successful harness subprocess. A timeout, nonzero harness exit, or malformed transport result could therefore remove useful diagnostic state when its temporary directory closed. This was inconsistent with the protocol's stated retention of infrastructure failures.

The corrected runner copies every available canonical initial state, current state and event journal in a `finally` block before temporary cleanup. Decoded transport is saved before canonical copying and analysis. Any failure writes the assignment identity, failure stage and type, process return code when known, and the names of available retained files; it then stops without a replacement run. Exception messages, raw process stderr, stacks and absolute command paths are excluded from the public error receipt. The correction changes infrastructure-failure retention, not service behavior or helper choices.

Read the complete corrected `run_one` path and the new isolated retention tests. Ran all three tests: mocked subprocess timeout, nonzero exit, and malformed JSON; **all three passed**, preserving sentinel canonical files and excluding injected private diagnostic text. These tests mock the subprocess and initializer and execute **zero real client calls, zero helper programs and zero principal matrix cells**. Parsed the corrected runner and test file with Python's AST parser. The resource aggregate also now subtracts recorded initial resources rather than a literal budget; all assigned initial budgets remain six.

No blocking source defect remains in this reviewed snapshot. The final runner hash below supersedes the earlier runner hash in the initial table; that earlier snapshot is retained to make the review sequence explicit. The immutable principal cases, inherited source and helper choices were not changed by this infrastructure correction.

| Final reviewed file | Bytes | SHA-256 |
| --- | ---: | --- |
| `execute.py` | 18854 | `6e75624f018171e6c7468e950c3c740710f3a07abfe94205805f4fe7b8f55c63` |
| `tests/test_failure_retention.py` | 3265 | `ccb5bc7814df05232164a3c0e6e4fb69ff78a2faaba9703cb7adbff3b1566713` |
