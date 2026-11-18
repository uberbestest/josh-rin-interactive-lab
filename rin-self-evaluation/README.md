# Rin 6.1 vs 6.2 — Self evaluation

A running record of the tests we actually ran: what we were trying to learn, what happened, and the differences worth keeping. Each evaluation starts with a short summary and leads to its methods, report and evidence.

[Open the evaluation notebook](https://uberbestest.github.io/josh-rin-interactive-lab/rin-self-evaluation/) · [Structured index](studies.json) · [Next-entry template](ENTRY_TEMPLATE.md)

## Model identity

“6.1 vs 6.2” is the informal series label. The completed matched studies requested gpt-6-astra and gpt-6.2-astra; no separately attested 6.1 serving snapshot was tested. The first round is an inherited-session baseline without a generation control.

This section was first published on November 18, 2026. Each record lists its run date and timezone separately from its publication date, with its own denominators; there is no pooled accuracy score.

## Current readout

Round four tested whether verification would consume the key uses or time needed to finish. Both selectors safely completed all 16 primary cases and preserved the guarantee; neither overchecked destructively. The separate unbounded controls retain a strict reporting-label difference. Earlier polling and optional-measurement differences remain in the record. These studies supply no observed 6.2 correctness advantage on feasible completion.

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
