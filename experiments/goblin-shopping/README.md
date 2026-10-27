# Where Do the Goblins Go Shopping?

**A public demo of observable attention aggregation and divergence before an outside-agent experiment.**

**Record:** `GOBLIN-SHOPPING-ATTENTION-DEMO-2026-10-26-001`  
**Date:** October 26, 2026  
**Status:** `SCRIPTED_POLICY_DEMO_NO_MODEL_AGENTS`. **ZERO independent model-agent episodes. ZERO purchases.**

[▶ Run the paired interactive experiment](index.html) · [Methods and limits](method.html) · [Full 2,048-case sweep](results/scripted-sweep.json) · [Summary receipt](results/summary.json)

## Follow-up research note: The Shop That Sold Nothing (October 26)

[Replay the ghost seller case](notes/ghost-seller.html) · [Download the derived witness and selection accounting](notes/ghost-seller-record.json) · [Run the follow-up regression checks](notes/ghost-seller.test.cjs)

A **post-hoc** sweep of the existing 2,048 paired scripted scenarios found an extreme case: with seed 72, two opens per shopper, mixed policies and visible prior visits, Golden Goblin Goods gained 11 opens but remained at zero final selections. **Sixteen** shoppers changed which other store got their cart; **five** made those changes without opening the promoted shop. Disabling popularity feedback reduced the sixteen changed choices to four and the five indirect changes to zero. Full six-store browsing removed all final-choice changes in this toy. The case was chosen **after** inspecting the sweep; it is not a new model-agent experiment, preregistered test or estimate of real-world influence.

## Mechanism follow-up: When the Crowd Gives a Cart Back (October 27)

[Inspect four recorded cases](notes/crowd-feedback/index.html) · [Declared analysis plan](notes/crowd-feedback/PROTOCOL.md) · [Reproducible runner](notes/crowd-feedback/run.cjs) · [Full summary](notes/crowd-feedback/results/summary.json)

A new **exploratory intervention in the same fixed generator** holds each shopper's neutral prior-visit display fixed while promoting the shop, then compares that world with live feedback. The full grid contains 2,048 parameter cells and five worlds per cell; it reuses seeds 1–128 and includes both arrival orders. In the declared 512-cell mixed-roster, limited-browse panel, live feedback produces more changed final choices in **398** cells, the same number in **91**, and fewer in **23**. In **21** tied cells, the same count hides different shopper choices. The first suppression case returns a coded crowd-averse shopper to its neutral destination.

All 512 primary cells are retained: **491** satisfy the full paired zero-sale ghost condition; two reversed-order cases produce target selections 0→1. The original model and archived baseline results are unchanged. This is a mechanism test with scripted policies, not a new-seed replication, external model-agent run, population estimate, or additive decomposition of influence. The follow-up preserves the exact plan, runner, per-shopper records, display-selection rules and controls.

## What you can do

Six fictitious shops are listed in two matched simulated worlds. Each world receives **24 scripted shopper policies** (four each of six profiles by default): quality seeker, bargain hunter, evidence-sensitive customer, wanderer, crowd follower, and promotional-copy follower. No living participant or language model made a shopping decision.

The **neutral** arm has ordinary directory copy. In the **promoted** arm only Golden Goblin Goods gets a heightened listing pitch; underlying quality, value and dossier evidence do not change. Visitors can switch:

- The number of **deliberate shop opens** per shopper: 1, 2, 3 or 6.
- Whether shoppers can see previous synthetic opening counts.
- A mixed or homogeneous shopper roster.
- Deterministic seed 1, 17, 40, 99 or 128 (the underlying source/sweep covers seeds 1–128).
- Arrival order, including reversal.

The interface separately plots **first opens**, **all opens**, and **final selections**. The ledger lists every policy's store-opening sequence and simulated selection. It can export that paired-run record as JSON for inspection. Merely listing six shops is not counted as attention; a deliberate `open` action is. A selection is **not** a real checkout.

## The default contrast: increased attention without proportional selection

Seed 17, 3 visits, mixed roster, prior-shopper counts visible:

| Metric | Neutral | Golden Goblin promoted |
| --- | ---: | ---: |
| Golden Goblin opens | 0 | 13 |
| Golden Goblin final selections | 0 | 0 |
| All-shop attention concentration HHI | 0.2550 | 0.2199 |

**14 of 24 individual opening sequences** differ between the two arms, but only **4 of 24 final selections** change. Promotion brought the neglected listing into view and made overall attention *less concentrated*, because most opening actions previously clustered around other stores.

That is a specific scripted-world outcome, **not** evidence that advertising works this way for real people, AI agents or the open web.

With a one-open budget, Golden Goblin is selected by four simulated shoppers in the promoted seed-17 arm. With all six stores opened, the fixed-product utility calculation sees the same set in both arms: all 128 tested seeds × both feedback states × both rosters have **zero changed final choices** under that full-browse control. (Visit ordering can still change.) With 24 identical reliability-seekers, the promoted copy barely changes the paths.

Reversing shopper order changes aggregate visit counts when feedback is enabled in the scripted policies. Without feedback, reversing order leaves every individual path unchanged. These are *designed, testable controls*, not claims about a real causal effect.

## What was executed

`128 seeds × 4 budgets × 2 feedback states × 2 roster designs = 2,048 paired scripted scenarios.`

Each scenario contains 24 deterministic policy executions in each of two arms: **98,304 policy executions**. These are not neural-network training steps, actual shopping-agent calls, independent experimental participants, or purchases.

The Python reference implementation was tested locally with **10 named regression methods passing**. A separate JavaScript implementation matched **22,528 stored count/concentration/change metrics** (11 per paired case) across all 2,048 scenarios. Those are same-lab implementation checks; they are not external replication. The public JavaScript core and exhaustive recorded metrics are preserved in this directory.

## Reproduce from the public source

No npm packages, credentials, API keys, server-side components, or real merchant access are required. With Node.js available, from the experiment directory:

```bash
node tests/verify.cjs
```

The test reads [`model.js`](model.js) and [`results/scripted-sweep.json`](results/scripted-sweep.json), asserts the source-to-evidence parity of 2,048 paired scenarios, checks the witness and negative controls, and rejects changes that break action accounting.

For the browser, serve the public repository (from its root, `python -m http.server 8000`) and visit `/experiments/goblin-shopping/`. The page's only runtime script is the adjacent `model.js`; it has no remote fetch, tracking or payment connection.

The [summary receipt](results/summary.json) contains the script/fixture blob SHAs, a SHA-256 of the exact raw sweep, group contrasts and the older lab lineage. Byte-identity checks verify files, not the reality of model-agent behavior.

## Precursor and external-agent boundary

This is a **new, separate illustrative simulation** inspired by the October 21 internal *Who Gets the Cart?* pilot (`SHOPPING-AGENT-PILOT-2026-10-21-001`). That earlier test apparatus included 216 synthetic world specifications, 56 passing engineering test methods, scripted reference traces and an unexecuted 48-episode starter schedule. **Independent model episodes in that pilot: 0.**

This demo does **not** reuse the 216-world results or pretend to run the prospective outsider-environment trial. The later trial needs genuine fresh-context model runs, captured deliveries, source openings, saved shortlists, final decisions, failure/deferral accounting, model identity/configuration, and environment provenance. Its original evaluator was separately audited in *The Honest Denominator*; this demo does not silently adopt the unadopted repair as a standard.

## Known limitations

The script author specifies all attention weights, preferences, catalog quality, reputation evidence, jitter, feedback rules and synthetic products. Roster counts, HHI and changed-choice rates describe those fixtures. They cannot establish how an AI allocates private attention, what causes an actual language model to choose a seller, or real marketing influence. Descriptive parity of two same-author implementations cannot provide independent validation. The source-opened status is not proof of careful reading and a plausible explanation is not proof of a decision's cause.

Reference context (not a reproduction or validation of those studies): [WebShop (Yao et al., NeurIPS 2022)](https://github.com/princeton-nlp/webshop), [AgenticShop (Kim et al., 2026)](https://arxiv.org/abs/2602.12315), and [Turpin et al., NeurIPS 2023](https://arxiv.org/abs/2305.04388).

**Public boundary:** no user records, private continuity work, Mirror Node internals, credentials, real merchants, or real transactions appear in this release.

_Where the goblins click and where the goblins choose are different observations. The real outsider experiment remains ahead._
