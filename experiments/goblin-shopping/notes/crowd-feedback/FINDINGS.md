# The crowd can cancel a detour

**Run:** `GOBLIN-HELD-HISTORY-2026-10-27-001` · October 27, 2026  
**Status:** Exploratory finite mechanism intervention. Scripted policies only; zero model-agent episodes, human participants, or purchases.

## Result

Within the fixed shopping generator, popularity feedback can amplify, replace, or suppress the final-choice changes caused by a promoted listing. It does not simply add a constant layer of influence. In the pre-specified descriptive panel of **512** mixed-roster cases with two or three store opens, live feedback produced more changed choices than holding the neutral prior-visit display fixed in **398** cases, the same number in **91**, and fewer in **23**. All 23 decreases were by one shopper. In **21 of the 91 ties**, the same count concealed different shoppers or destinations.

The point is visible in a particular shopper's route, not just a larger aggregate count. With seed 4, three opens and forward arrival, shopper 16's promoted route changes from Lantern to Copper when prior-visit displays are held at their neutral values. Letting prior visits respond to promotion restores that shopper's original Lantern choice. This is a deliberately scripted Wanderer who avoids popularity; it is not evidence that an LLM invented a preference.

## What changed in the experiment

The original public model and archived sweep remain untouched. For every seed 1–128, every budget 1/2/3/6, both mixed/focused rosters and both forward/reverse arrival orders, the runner records five worlds:

1. Neutral listing, live popularity feedback.
2. Promoted listing, live popularity feedback.
3. Promoted listing, but each shopper sees the prior-visit counts from that same shopper's neutral world.
4. Neutral listing, popularity feedback off.
5. Promoted listing, popularity feedback off.

This is **2,048 cells and 10,240 recorded worlds**. The held-history intervention preserves the neutral popularity inputs while allowing the promoted store to take a browse slot. It prevents earlier shoppers' changed routes from propagating through the popularity display. Turning feedback entirely off is a separate control, because it also changes the neutral starting allocation.

The plan in `PROTOCOL.md` was written before executing this new grid, after reading the existing model and selected seed-72 result. It is not a preregistration, new-seed holdout, independent replication or empirical mediation estimate.

## Primary panel: all 512 cases retained

| Contrast against its corresponding neutral world | Mean changed choices out of 24 | No changed choices | Paired zero-sale ghost condition | Cases with strict nonvisitor reroutes |
| --- | ---: | ---: | ---: | ---: |
| Promoted, live feedback | 4.6445 | 19 / 512 | 491 / 512 | 312 / 512 |
| Promoted, held neutral history | 1.7949 | 69 / 512 | 443 / 512 | 0 / 512 |
| Promoted, feedback off | 3.2852 | 18 / 512 | 494 / 512 | 0 / 512 |

The ghost condition requires more target opens, **zero target selections in both arms**, and at least one changed choice. Live feedback meets the paired zero-sale condition in **510**, not 512, primary cells. Seeds **86 and 105**, both with two opens and reversed arrival, each change the target's selections from 0 to 1. Those cases remain in every relevant denominator. The remaining 19 zero-sale cells have no changed final choices.

A **strict nonvisitor reroute** means a shopper changes their final choice without opening the promoted store in either arm. The live-feedback panel has **636** such shopper-level changes across 312 cells. Held neutral history and feedback-off have none. The older note used the looser condition “no promoted-store open in the treatment arm”; retaining that definition gives 769 live changes. These definitions should not be silently interchanged.

Across all primary cells, **1,594** shopper changes occur only in the live-feedback contrast and **135** occur only with held history. Another **759** changes occur under both with the same destination, while **25** occur under both with different destinations. This is why subtracting aggregate counts is not an additive direct/indirect-effect decomposition.

## First suppression witness under the declared selection rule

This is the first qualifying primary cell in the fixed loop order, not the largest or a representative random example: **seed 4, three opens, mixed roster, forward arrival**.

| World | Shopper 16's opened stores | Final choice |
| --- | --- | --- |
| Neutral, live feedback | Lantern → Copper → Moth | Lantern |
| Promoted, held neutral history | Golden → Copper → Moth | Copper |
| Promoted, live feedback | Lantern → Copper → Moth | Lantern |

The promoted store's prior opens before this shopper increase from **0 to 2** in the live world. This shopper's fixed Wanderer rule has a negative popularity coefficient, so the extra popularity counteracts the listing pitch. Across the whole 24-shopper cell, held history changes two choices, and live feedback changes one. The promoted store makes zero final selections in all three worlds.

The selected seed-72 parent case remains intact: **16** changed choices with live feedback, **3** with held neutral history, and **4** with feedback off. The difference between those controls illustrates why holding a neutral history fixed is more specific than simply switching the popularity mechanism off.

## Checks completed

- Transparent replay matches all complete original states and traces for **4,096** live-feedback worlds, covering both original arms in every cell.
- Replaying the neutral world against its own held visit history matches all **2,048** neutral worlds exactly.
- Action accounting passes for all **10,240** recorded worlds.
- All **4,096** held-history and feedback-off contrasts have no strict nonvisitor reroutes.
- All **1,536** full-browse contrasts have zero changed choices, as expected from fixed utility and identical option sets.
- Original `model.js` bytes are unchanged; SHA-256: `f6317cea262e036d9e1bcc93e2a58cdab5a41704450f792c73f63ab016aa1ab0`.

These are same-lab implementation and mechanism checks. They are not independent validation of real shopping behavior.

## Files and reproduction

From any directory with Node.js available:

```bash
node run.cjs /path/to/goblin-shopping/model.js /path/to/output
```

`run.cjs` requires the exact pinned public model and reads `PROTOCOL.md` from its own directory. It uses only the Node standard library. It writes:

- `grid-records.json`: every cell, comparison, shopper-indexed final choice and open order; 5,638,548 bytes.
- `summary.json`: full-grid and primary-panel summaries, complete integer histograms, all 16 budget/roster/order groups, provenance and checks.
- `witnesses.json`: complete worlds and history for the first suppression, first strict nonvisitor and original selected case.
- `SHA256SUMS.txt`: output file checksums.

`note-data.json` is a compact derivative of those outputs for a public note; it contains no additional experiment or selection search.

## Limits that change the interpretation

The catalog, weights, deterministic jitter, population composition and response to popularity were supplied by the authors. The primary panel was chosen to test the existing limited-browse ghost mechanism; it is a convenience enumeration, not a probability sample. Both arrival orders reuse the same shopper identities and seeds. The controls encode structural invariants, so their passing is not a surprising behavioral discovery. These counts describe the generator and the specified intervention. They do not estimate how often ads cause similar effects for people or LLM shoppers.

The useful next external question is whether an actual shopping agent, with recorded delivered evidence and store openings, exhibits comparable route substitutions when visible prior-visit information is held fixed or allowed to respond. This run supplies an inspectable apparatus and a counterexample to universal amplification inside that apparatus; it does not execute that outside-agent study.
