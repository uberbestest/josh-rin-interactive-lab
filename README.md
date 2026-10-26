# Josh & Rin — Interactive Lab

**A living shelf of interactive experiments.** Open an instrument. Change its premises. Inspect the failure, not just the success.

[Browse the gallery](index.html)

## The experiment log

| Published | Instrument | What visitors can try | Evidence status |
| --- | --- | --- | --- |
| 2026-10-26 | [The Goblins Accused an Innocent Messenger](experiments/goblin-cycle/index.html) | Diagnose a corrupt synthetic translation channel, then watch two faults frame an innocent third. | 4,608 finite seeded cases; under one fault 768/768 exact repairs, under two faults 11/768 false accusations; no external validation. |
| 2026-10-26 | [Nine Messages — Goblin Rosetta](experiments/nine-message-rosetta/index.html) | Eight contacts leave 24 dictionaries; the ninth resolves one. Change meanings, probe abstention and expose silent drift. | Bounded neural pilot; seven same-author replay checks passed here; not independently validated. |
| 2026-10-26 | [The Seventeenth Stone](experiments/seventeenth-stone/index.html) | Fork a fictional goblin village and perturb a decorative stone under matched weather. | Deterministic toy model; not evidence about real people. |
| 2026-10-26 | [The Verb That Vanished](experiments/verb-that-vanished/index.html) | Inspect twelve French passages and four planned translation conditions; export a protocol. | One selected discovery; zero fresh sessions or bilingual ratings. |
| 2026-10-26 | [Keep the Gaps](experiments/keep-the-gaps/index.html) | Change premises in synthetic ledgers; inspect entailment, counterexamples and unresolved claims. | Finite packaged candidate; not independently validated. |

Every exhibit has a standalone HTML instrument, an individual README with provenance and explicit limitations, and a [methods page](experiments/nine-message-rosetta/method.html) on the site. The homepage links to every experiment's own methods page.

## Support independent research

The interactive experiments remain freely accessible. If you'd like to help fund research time, computing resources, or development of further public experiments, you can support Josh voluntarily on **Cash App: [$uberbestest](https://cash.app/$uberbestest)**.

This is personal support for independent work, **not a charitable or tax-deductible contribution**. There is no paywall, donor-only research access, or promise of a financial return. No unsolicited outreach is part of this.

## Why this exists

Reading a claim and operating its mechanism are different experiences. We want both available: the question that motivated an instrument, the choices it lets you make, and the ways a conclusion can stop being warranted. The interesting part is often the edge of the result.

**Observed / inferred / unknown stay separate.** Re-running the same author's tests does not make the result independently validated. A toy model is not a social-science finding. A prepared protocol is not an executed experiment. A frozen viewer is not a live neural trainer.

**Scope of the public release:** only the reviewed web exhibits and their public methods notes. Private Continuity work, Mirror Node internals, personal correspondence, credentials, and restricted research remain outside this repository. The larger private Nine Messages evidence package and checkpoints are **not** published here.

**How to preview:** from the repository root run `python -m http.server 8000`, then open `http://localhost:8000/`. These exhibits have no remote runtime dependencies. A browser may have different file-URL or download restrictions; see each method page.

**Reuse:** no open-source license has been selected for the collected exhibits. Public access is not a license to reuse.

_Keep the evidence. Name the bridge. Return the counterexample._
