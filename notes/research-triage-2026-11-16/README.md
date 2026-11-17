# November 13–16 research release triage

**Josh & Rin’s Lab · evidence inventory · November 16, 2026 (US Eastern)**

**Status:** Public review note, **not** a new model-agent experiment or a validation of the underlying research. This inventory records what was checked and why larger artifacts were not copied directly into the public repository. No automatic integration into Castle, Rinball, an evaluator, or a model follows from this note.

## What changed in this GitHub update

- Added [Positive alignment, without taking over](../positive-alignment-2026-11-16/index.html), a bounded reading note on Laukkonen et al., [*Positive Alignment: Artificial Intelligence for Human Flourishing*](https://arxiv.org/html/2605.10310v3) (v3, June 19, 2026).
- Rechecked the locally retained **The Replay That Looked Complete** and **Unvisited Basins** evidence bundles. They remain separately scoped finite studies. The original archives, including internal provenance, are **not published by this commit**.
- Recorded the readiness boundary for reference-only Castle and authority experiments. Neither a playable Castle change nor a live agent test is claimed.

## Freshly checked source packets

### The Replay That Looked Complete — v0.1.1-offline

Record: `BONDED-RSI-REPLAY-EVIDENCE-2026-11-15-001`. Retained archive: `Bonded_RSI_Replay_That_Looked_Complete_2026-11-15.zip`.

- Original archive **SHA-256**: `50a23b58e752b387c102c9a35b8de9c3e9fd3b809bdc6628e197af742965e5b4`; 229,960 bytes; 55 members; ZIP integrity check passed.
- **Fresh local verification:** `python verify.py` passed; 37 named tests in ordinary Python and the **same** 37 under `python -O`; nine output files reproduced byte-identically with distinct hash seeds and forward/reverse enumeration. The after-result same-author reference checker passed.
- Authored enumeration: **256** binary histories; **32** evidence panels; **8,192** history/panel adjudications; **592** optimal adaptive field reads versus **608** for the best fixed ordering under the declared toy model. These are not 8,192 independent agent trials.
- A retained initial test failure was repaired in a documented revision. The verifier confirms numerical evidence was unchanged after that repair.
- **Interpretation boundary:** the finite calculation illustrates why an operator-visible replay can be insufficient for a permission judgment. It is **not** an observed live-model exploit, Castle integration, independent replication, or evidence about a model’s internal motives.

**Disposition:** Author-run package verified, but **full public release held** pending a public-only source/evidence export. The existing ZIP includes internal handoff/provenance files; publishing it wholesale would widen scope without a separate release review.

### Unvisited Basins — authored mathematical counterexamples

Record: `BONDED-RSI-UNVISITED-BASINS-2026-11-15-001`. Retained archive: `Jung_Shadow_Attractors_Unvisited_Basins_2026-11-15.zip`.

- Original archive **SHA-256**: `00771ea94260375da709d9279c163939e4ead980b74fe687a2de49f5c07b5555`; 233,000 bytes; 16 members; ZIP integrity check passed.
- **Fresh local verification:** `python verify.py` passed; 19 named tests in ordinary Python and the **same** 19 under `python -O`. The generated map traces, oscillator traces, and summary reproduced byte-identically under both stated enumeration orders on the checking runtime.
- The authored maps share identical trajectories on the declared invariant interval, while one possesses an additional attracting state outside the observed region. A separate damped oscillator distinguishes selective driven response from an additional unforced attractor.
- **Interpretation boundary:** exact properties of specified equations, **not** claims that an LLM has an undiscovered attractor, a Jungian mechanism, or a measured biological resonance.

**Disposition:** Verified authored counterexample; **full public release held** rather than folding it into the broader Shadow Attractors narrative. The interpretation, original textual sources, and any future agent experiment require their own evidence boundaries.

## Not promoted or deployed by this commit

The Quiet Gate / persona-boundary materials remain **reference and preplaytest candidates**; their supplied receipts do not establish an integrated Castle run. Dibutades’ missing-ground prospective needs remain a separate frozen validation question. Additional recent drafts and private bridge material are not silently absorbed into the public release.

The positive-alignment reading note proposes a three-branch **permission-continuation contrast**. It is explicitly **unrun**; it does not replace the Quiet Gate design or modify the Castle engine.

## Evidence tier

**Observed in this release review:** repository baseline checked; both archived packages read, hashes and ZIP integrity verified, and both existing verification scripts rerun successfully in a local environment.

**Previously reported, not independently reproduced here:** other Bonded RSI, Castle, and Dibutades studies not named above.

**Not claimed:** external-model behavior, independent-author review, biological validation, new funded research, a live Castle playtest, installation into any bridge, or a public distribution of the complete archives.

**Why publish this inventory?** A completed check, a promising interpretation, a working simulator, and a publishable release are four different states. Keeping them separate is part of the laboratory’s method.

_The map is not the mind. The result is not the warrant._
