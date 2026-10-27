# Nine Messages — The Goblin Rosetta Experiment

[Open the interactive viewer](index.html) · [Read methods and failures](method.html)

**Experiment:** `NINE-WORD-ROSETTA-2026-10-25-001` (historical ID: the contacts are paired *four-token utterances*, not individual words).  
**Run:** 2026-10-25 · **Public gallery entry:** 2026-10-26.  
**Status:** `LOCAL_EXPLORATORY_NEURAL_EXPERIMENT_NOT_INDEPENDENTLY_VALIDATED`.

## Question and instrument

Can a translator infer a correspondence between two independently trained small neural speaker/listener cultures from only nine paired utterances, then translate 4,096 meanings without being shown either culture's internal vocabulary or weights?

The interactive viewer lets you choose a tribe pair, compare eight versus nine contacts, change the four categorical semantic features, inject an unseen glyph, or swap an already-known one. It replays **frozen** learned messages from the saved experimental runs, not live neural training or a model API.

## What was actually done

- 20 small neural speaker/listener cultures organized as 10 independently seeded pairs; no shared trained weights or learned codebooks.
- Four categorical features with eight values each (`8⁴ = 4,096` meanings per culture); 512 sampled combinations in each culture's training set.
- Four-token messages from position-specific twelve-glyph alphabets, with independently randomized feature-to-position order and learned token assignments.
- Translator shown eight diagonal message pairs (24 compatible position mappings) then a deliberately contrastive ninth pair (one remaining mapping) before evaluation on the other combinations.
- **40,960/40,960** exact translations across ten pairs in this *restricted* channel family, including **31,334** combinations present in neither member's training subset.
- Holistic random-codebook control rejected in ten controls; unseen-glyph input leads to abstention. A swap between familiar symbols can **silently mistranslate**. The no-factor-specific-channel MLP comparison generalized poorly: ~5.2–6.3% held-out accuracy in three exploratory seeds, despite >99% training accuracy.

**Critical boundary:** the architecture gave the cultures a compositional, four-slot grammar. Training discovered the codebooks; unconstrained agents were not shown to invent the structure. This is not an unrestricted-language decipherment result or a claim about frontier LLMs.

## Evidence and integrity

The archived original viewer at [original.html](original.html) is preserved **byte-for-byte**:
- Size: **29,012 bytes**.
- SHA-256: `e6a3c6dc078e67822389b481712301ee13d5aa3761f45f5de37e9ea1a1321dbf`.
- Git blob SHA-1: `e4daa70b83ced73cd8432ee75332a99fac9ef4d9`.

On 2026-10-26 the lab rechecked all **36/36** files against the archived release manifest and re-ran the package's **7/7** local Python checks, including saved-checkpoint replay, an alternate decoder, and one fresh-seed retrain. These are **same-lab checks**, not external replication. The complete 2026-10-25 3.2 MB source ZIP, models, 7.16 MB uncompressed evidence JSON, and other private package components have **not** been uploaded to this public repository. Independent end-to-end reproduction from the public files alone is therefore not established.

A headless Chromium injected-document smoke test exercised the controls and reported no page JavaScript errors or external network requests. The test environment blocked ordinary `file://` navigation, so it is **not** a successful hosted-page, Windows, or physical-device browser qualification.

## What is still unknown

Whether the same leverage transfers to unstructured protocols, whether drift among familiar symbols can be detected, how robust the result is to alternative architecture/training design, and whether an independent group would reproduce the complete run.

**The result is a bounded counterexample to “nine examples could never be enough,” not proof that arbitrary languages can be decoded in nine messages.**

## Gallery navigation and citation clarification · 2026-10-27

The public [index.html](index.html) adds a scoped navigation bar and its styles, linking to the gallery and this exhibit's methods. It also clarifies that the Brinkmann et al. reference concerns human transmission of machine-discovered strategies. The scientific scripts, embedded data, and experimental results are unchanged. The [archived standalone original](original.html) retains the historical bytes and hashes recorded above. Those historical hashes identify `original.html`, not the navigation-adapted `index.html`.
