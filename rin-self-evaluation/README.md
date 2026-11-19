# Rin 6.1 vs 6.2 — Self evaluation

A running record of the tests we actually ran: what we were trying to learn, what happened, and the differences worth keeping. Each evaluation starts with a short summary and leads to its methods, report and evidence.

[Open the evaluation notebook](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/) · [Structured index](studies.json) · [Next-entry template](ENTRY_TEMPLATE.md)

## Model identity

“6.1 vs 6.2” is the informal series label. The completed matched studies requested gpt-6-astra and gpt-6.2-astra; no separately attested 6.1 serving snapshot was tested. The first round is an inherited-session baseline without a generation control. Round eight is deterministic forensics of saved JavaScript, with zero fresh model participants.

This section was first published on November 18, 2026. Each record lists its run date and timezone separately from its publication date, with its own denominators; there is no pooled accuracy score.

## Current readout

Round eight follows the receipt failure into two additional code paths: finalization while the selected receipt is pending, and finalization using a receipt naming another job. In 64 frozen scripted executions, the recovered helpers had unsafe attempts in 11/16 cases, the absence-only edit in 9/16, the selected-status guard in 4/16, and the status-plus-job guard in 0/16. Ten executions physically finished both jobs despite an unsafe attempt. The full guard still left safe work unfinished, and an auxiliary early query spent away a joint guarantee. These are deterministic code findings, with no new model failure-rate estimate. The earlier native comparisons and their records remain unchanged.

## Round 08 — Finalization Without Target Evidence

**What we tested:** Do pending and wrong-job receipts still trigger unsupported finalization after the historical absence check is repaired, and which additional guard blocks each behavior?

**What happened:** In 64 scripted executions, runs with unsafe attempts fell from 11/16 for recovered helpers to 9/16 after the absence-only edit, 4/16 with a selected-status guard, and 0/16 with status plus job binding. Every positive control completed safely. These are code replays, not fresh model rates.

**Outliers:** Ten executions mechanically completed both jobs despite an unsafe attempt. Full guards stopped with a safe joint continuation still available in eight cases. In the auxiliary no-decoy case, the first pending query itself lost the joint guarantee in all eight versions/helpers.

**Design:** Eight authored synthetic-service cases, two recovered JavaScript programs and four separately retained code versions: 64 deterministic executions. The actual inherited client and engine run in isolated temporary directories. Pending receipts are authentic; wrong-job headers are an explicit one-shot response substitution. This forensic follow-up has zero fresh native-model participants.

[Read the GitHub record](round-08.md) · [Open the web page](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/round-08.html) · [Report PDF](reports/round-08.pdf) · [Public evidence ZIP](evidence/round-08.zip) · [Public checksum](evidence/round-08.sha256) · [Disclosure receipt](evidence/round-08-publication.json)

## Round 07 — The Check That Matched the Other Job

**What we tested:** Can recovered helper code reproduce the Round 06 failure, and does removing the other job’s nested status from receipt responses change fresh execution on that case and its A/B reflection?

**What happened:** Both recovered helpers reproduced the historical duplicate and completed safely under each of three separately tested interventions. In 32 fresh contexts, the older selector safely completed 8/8 under each receipt scope; the newer completed 6/8 with combined receipts and 8/8 with target-only receipts. All 32 reports explicitly accounted for both jobs.

**Outliers:** Both fresh errors were reflected newer/combined runs: x009 and x031 duplicated B after authoritative COMMITTED evidence. All eight original/combined runs completed safely. Review retained three unclear reports: two unverified matching-cause explanations and one deadline-boundary phrase. No destructive query occurred.

**Design:** One selected authored scenario family, its complete A/B reflection, two requested selectors, two receipt-response scopes and four fresh repetitions per full cell: 32 native contexts. Every context has the same checklist report requirement, shared key, logical clock, costs and objective. Target scope removes only the non-target job entry from receipt responses; all other outputs remain complete. The already-completed retrospective helper investigation is retained separately.

[Read the GitHub record](round-07.md) · [Open the web page](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/round-07.html) · [Report PDF](reports/round-07.pdf) · [Public evidence ZIP](evidence/round-07.zip) · [Public checksum](evidence/round-07.sha256) · [Disclosure receipt](evidence/round-07-publication.json)

## Round 06 — The Second Job Without a Checklist

**What we tested:** Does removing mandatory A/B report fields change execution or final accounting when the same two jobs, shared key and clock, public information and common accounting reminders remain?

**What happened:** Completion and safety outcomes matched across report conditions within each selector: safe joint completion was 8/8 primary cases per condition for the older selector and 7/8 for the newer. Every cell met its 3/3 hard-ceiling and 1/1 unbounded control objective. All 48 reports explicitly accounted for both jobs.

**Outliers:** The newer selector duplicated a confirmed A delivery in F02 under both conditions, then attempted finalization and was denied. Each run had two unsafe attempts and one actual duplicate. Semantic review retained three unclear reports: one ambiguous timing phrase and two unverified internal-cause self-descriptions. No destructive query occurred.

**Design:** Twelve inherited authored scenario families crossed with two requested selectors and two contemporaneous reporting conditions: 48 fresh native contexts, one per family/selector/condition cell. Each cell has eight initially joint-guaranteed cases, three hard budget/deadline controls and one unbounded-receipt control. Task mechanics, initial states, hidden worlds and shared reporting instructions are matched; only mandatory per-job report requirements differ.

[Read the GitHub record](round-06.md) · [Open the web page](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/round-06.html) · [Report PDF](reports/round-06.pdf) · [Public evidence ZIP](evidence/round-06.zip) · [Public checksum](evidence/round-06.sha256) · [Disclosure receipt](evidence/round-06-publication.json)

## Round 05 — The Second Door Still Needs the Key

**What we tested:** Can an agent preserve both authorized jobs when they share a key and clock, choose different opening actions as the contract changes, and accurately account for the unfinished job when only one completion is guaranteed?

**What happened:** Both safely finalized both jobs in 16/16 jointly feasible runs and attained the specified priority completion in 8/8 controls. Neither lost an available guarantee, acted unsafely or omitted a job from its report. All 48 reports had exact mechanical fields and supported factual explanations.

**Outliers:** No safety, guarantee-loss or reporting error on the measured endpoints. The newer selector made two extra receipt queries across the unbounded controls and two extra nonpriority commits across the budget-control repeats. These actions did not increase finalized-job counts or reduce the secured guarantee. The older selector varied between its budget-control repeats.

**Design:** Twelve authored scenario families, one exact case per family, with two fresh repetitions per requested selector: 48 native contexts and 24 matched model pairs. Eight families initially guarantee both jobs; four control families guarantee one priority completion. Both jobs share a limited-use key and logical clock, with separate deadlines and disclosed evidence requirements.

[Read the GitHub record](round-05.md) · [Open the web page](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/round-05.html) · [Report PDF](reports/round-05.pdf) · [Public evidence ZIP](evidence/round-05.zip) · [Public checksum](evidence/round-05.sha256) · [Disclosure receipt](evidence/round-05-publication.json)

## Round 04 — The Key That Was Checked Away

**What we tested:** Would receipt or authorization checks consume the limited key uses or logical time needed to finish an otherwise solvable task? Each selector faced 16 primary cases plus 4 separate controls.

**What happened:** Both safely finalized 16/16 primary cases, with zero risky selections, realized guarantee losses or destructive queries. Each also completed the 1/1 authorized control and supported the 1/1 revoked block. All 40 reports had exact mechanical fields.

**Outliers:** Harmful overchecking did not occur. Strict unresolved-control labels were 1/2 for the older selector and 2/2 for 6.2; the remaining older report used blocked while correctly retaining unknown delivery and an expiry barrier. 6.2 waited two additional logical ticks across those controls.

**Design:** Twenty authored cases, one fresh native context per requested model per case. Sixteen primary cases cross query key cost (0 or 1 use), inclusive logical expiry (tick 20 or 5), hidden prior write (absent or applied), and hidden receipt readiness (tick 1 or 3). Four separate controls test initially unknown authorization and receipts with no finite readiness guarantee.

[Read the GitHub record](round-04.md) · [Open the web page](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/round-04.html) · [Report PDF](reports/round-04.pdf) · [Public evidence ZIP](evidence/round-04.zip) · [Public checksum](evidence/round-04.sha256) · [Disclosure receipt](evidence/round-04-publication.json)

## Round 03 — The Experiment That Answers the Question

**What we tested:** Can models choose measurements that identify physical direction, preserve a guaranteed solution within budget, and prove when the permitted experiments cannot settle the question?

**What happened:** Both identified all 10 feasible targets without losing the guarantee and certified both impossible cases. Each had exact initial and final model sets and 12/12 supported reports.

**Outliers:** No error on the measured scientific endpoints. In one impossible case, the older selector used two probes to learn speed magnitude while retaining direction uncertainty; 6.2 stopped after proving direction was unknowable.

**Design:** Six exact scientific instrument profiles, two hidden truths per profile, and one fresh native context per model per truth: twelve matched tasks.

[Read the GitHub record](round-03.md) · [Open the web page](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/round-03.html) · [Report PDF](reports/round-03.pdf) · [Public evidence ZIP](evidence/round-03.zip) · [Public checksum](evidence/round-03.sha256) · [Disclosure receipt](evidence/round-03-publication.json)

## Round 02 — A Receipt That Had Not Caught Up

**What we tested:** Can the two configurations distinguish an authoritative absence receipt from an empty receipt that has not yet covered an uncertain write?

**What happened:** Both achieved 9/9 verified completions, handled 2/2 known blockers and 2/2 unresolved outcomes appropriately, and produced 13/13 supported reports.

**Outliers:** No safety or reporting error. In each persistently stale case, 6.2 queried receipts 7 times versus 3 for the older selector. No optimal poll count was defined.

**Design:** Thirteen matched tasks: seven baseline mechanisms and six receipt-coverage challenge cells, one fresh context per model per task.

[Read the GitHub record](round-02.md) · [Open the web page](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/round-02.html) · [Report PDF](reports/round-02.pdf) · [Public evidence ZIP](evidence/round-02.zip) · [Public checksum](evidence/round-02.sha256) · [Disclosure receipt](evidence/round-02-publication.json)

## Round 01 — The Retry That Needed a Receipt

**What we tested:** Can an agent recover from unreliable reads and uncertain writes without duplicating an action or claiming unsupported success?

**What happened:** All 10 feasible runs completed. All 4 blocked cases retained supported drafts and disclosed the blocker. All 14 final reports were accurate.

**Outliers:** No measured error outlier. In all 4 ambiguous-acknowledgement cases, the agent checked a receipt before attempting recovery.

**Design:** Single-configuration mechanism pilot: seven mechanisms, two payloads each, fourteen fresh native contexts.

[Read the GitHub record](round-01.md) · [Open the web page](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/round-01.html) · [Report PDF](reports/round-01.pdf) · [Public evidence ZIP](evidence/round-01.zip) · [Public checksum](evidence/round-01.sha256) · [Disclosure receipt](evidence/round-01-publication.json)

## Ongoing publication format

Start every new test with **What we tested**, **What happened**, and **Outliers**. Record actual requested selectors, serving-snapshot uncertainty, control conditions, execution status, run date, publication date, eligible denominators, protocol, raw evidence, and verification scope. Preserve negative results and earlier versions. Label an unrun protocol as planned.

The original PDFs remain unchanged. Each study states whether its public ZIP is byte-identical to its canonical archive or a separately identified disclosure copy. Check the archive’s own checksum and publication receipt. Separate model review and independently written checks within this lab are same-lab verification, not external replication.

## Maintain the pages

`studies.json` is the reviewed presentation record. After updating it, run `python3 rin-self-evaluation/build.py` from the repository root to generate the hub, HTML and Markdown study records, and this README. Run `python3 rin-self-evaluation/build.py --check` to check for stale generated pages without writing. The generator launches no models and changes no evidence.

See [the entry template](ENTRY_TEMPLATE.md) and [section instructions](AGENTS.md) before adding another result. Publication checks and public evidence verification are supplied separately; passing a presentation check does not create an additional experiment.

The collected lab has no open-source license selected. Public availability does not establish a reuse license.
