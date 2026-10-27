# The Lying Map — Goblin Games

**Archived interactive experiment, now curated into the public lab on October 26, 2026.**  
**Original run:** `RIN-GOBLIN-LYING-MAP-2026-09-30-001` (September 30, 2026).  
**Status:** Fixed-policy finite experiment and browser arcade. **Zero fresh LLM workers** were run for this clockwork variant.

[▶ Play the arcade](index.html) · [Methods & limitations](method.html) · [Original checked research report](REPORT.md)

## What is playable

The browser arcade has a four-room map—Camp, Mill, Pond, Vault—six misleading or correct door signs, a limited action budget, ten selectable clockwork policies, and an optional one-use rescue rope. You can play manually, inspect an algorithm, alter the action budget, choose a historical witness, generate a synthetic map, and reveal the underlying truth in the UI.

All worlds, goblins, signs, and actions are fictional. The arcade is self-contained HTML with no network calls or other third-party runtime dependencies.

## The observation that earned a public exhibit

**A safety check can be useful and still arrive one action too late.**

Every one of the 4,096 possible four-room worlds was paired with its accurate map and all one-error map variants: **77,824 primary cases per policy**, run through ten fixed policies. This yields **778,240 scripted primary episodes** in the source report, not model-agent trials. The separate **4,096 two-error pairs per policy** yielded 40,960 stress episodes; do not mix this sampled stress set into exhaustive rates.

Among **54,432 solvable one-error cases**, an eight-action budget favored a contact-repair policy with rope, but a ten-action budget favored a Scout-plus-rope policy, which then solved all 54,432 of *those particular* cases. The policies were unchanged; changing the evaluation budget reversed the outcome.

One witness is an especially good goblin story: Scout uses its eighth action to inspect the correct Vault exit, then loses because inspecting is not entering. A ninth action would have reached the Vault. Another witness shows that correcting a false map after walking into an isolated room doesn't physically rescue you; knowledge recovery and access recovery are different things.

The report carefully distinguishes the separate post-hoc budget supplement from its earlier fixed budget findings.

## What can be verified and what remains missing

- The archived standalone arcade at [original.html](original.html) is preserved **byte-for-byte** from the checked October 1 artifact: **55,762 bytes**, SHA-256 `9b2d097aeff5ba0a4ed4961814922f82cd1b8c28ae42f3baf3519187aa6737aa`; Git blob `a6f9557dc1a62919c99a3b22f1dab78e1aa8aaf3`.
- Original research report was copied **byte-for-byte**: **12,054 bytes**, SHA-256 `1f96436cdf2268441df93f0d9b268c3bafd84acb9187a411249ebfc949627142`; Git blob `f2106f7c2d4d0e6fdc208e16a80b617b2cbd8a05`.
- The original same-lab evidence reported 13 prelaunch tests, 65 post-run assertions, and 2,450 browser-engine-vs-Python sampled case comparisons. Those checks were recorded with the original run; **this public curation did not rerun the entire 819,200-episode set.**
- The public repo includes the archived self-contained arcade and original report. The original full multi-file primary dataset and engine aren't part of this exhibit. Hence full independent recomputation of the original aggregate results **is not qualified from these public files alone**.
- Archive hashes and local checks are not an external audit or certification.

## Limits and interpretation

Ten distinct programs executed locally in ten operating-system processes, but shared a host-written codebase and policies. They were **not independent model-agent contexts or sandboxed actors**. The policies were hand-authored for a finite map toy; no LLM intelligence, optimum strategy, personality or real-world access guarantee is established.

At least-one-error, at-most-one-error, sampled two-error and impossible-world conclusions belong to their respective controls. The rope trigger is conservative and not optimal. The budget supplement was designed after primary outcomes were known. Unsolvable worlds were retained as negative controls, not silently deleted from the corpus.

**Our public release does not include continuity research, Mirror Node internals, personal information or external credentials.**

_A goblin may know exactly where the door goes, and still not have enough moves left to walk through it._

## Gallery navigation update · 2026-10-27

The public [index.html](index.html) adds only a scoped navigation bar and its styles, linking to the gallery and this exhibit's methods. The scientific scripts, embedded data, and original instrument content are unchanged. The [archived standalone original](original.html) retains the historical bytes and hashes recorded above. Those historical hashes identify `original.html`, not the navigation-adapted `index.html`.
