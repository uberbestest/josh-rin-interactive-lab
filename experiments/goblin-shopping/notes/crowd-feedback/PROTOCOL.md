# When the Crowd Cancels the Advertisement

## Declared analysis plan — October 27, 2026

This plan was written after inspecting the public model and the selected seed-72 ghost-store example, and before executing the new grid below. It is an exploratory mechanism follow-up, not a preregistration, held-out replication, independent validation, or model-agent experiment. The public model and original archived results will remain unchanged.

**Parent:** `GOBLIN-SHOPPING-ATTENTION-DEMO-2026-10-26-001`; post-hoc parent note `GOBLIN-GHOST-STORE-2026-10-26-001`.

**Question:** Does popularity feedback always add to the choice changes induced by a promoted listing, or can it replace or suppress them within this fixed scripted generator?

## Fixed design and stopping rule

Enumerate seeds 1–128, budgets 1/2/3/6, mixed/focused rosters, and forward/reverse arrival order: **2,048 parameter cells**, each with 24 scripted shoppers. No early stopping and no parameter search beyond this grid. Include every cell in raw output, including no-change and nonzero-target-selection cases. No new seeds or model agents are claimed.

The primary descriptive panel is the **512 mixed-roster cells with budgets 2 or 3**, both arrival orders, and all 128 seeds. Budgets 1 and 6 and the focused roster are controls, retained separately and in the full grid. The two arrival orders are fixed perturbations, not a sample of all possible orders.

For each cell run five worlds:

1. **Neutral, live feedback:** original unpromoted model with organic prior-visit counts.
2. **Promoted, live feedback:** original promoted model with organic prior-visit counts.
3. **Promoted, held neutral history:** promoted listing, but each shopper sees the exact prior-visit counts encountered by that same shopper in the neutral live-feedback world. Preserve shopper identities, arrival positions, budget, preferences, utility and deterministic noise. The held count display is an explicit intervention in the toy environment. Choices still use each shopper's actual opened stores. It blocks cross-shopper propagation through the display; it does not remove promotion or the browse budget.
4. **Neutral, feedback off:** original model without popularity feedback.
5. **Promoted, feedback off:** original model without popularity feedback.

The held-history renderer will also reproduce the neutral world from its own recorded history. A separate transparent replay implementation will be checked against original live-feedback output for both arms of every cell. These are same-lab engineering checks.

## Metrics specified before execution

- Promoted-store explicit opens and final selections in every arm.
- For live feedback, held history and feedback-off contrasts: changed final selections, changed opening paths, changed first openings, and shopper IDs for each category.
- **Paired zero-sale ghost condition:** promoted-store opens increase, its final selections are **0 in both compared arms**, and at least one final selection changes.
- **Strict nonvisitor reroute:** final selection changes although the shopper never opens the promoted store in **either** compared arm. Keep the older, looser count (no promoted-store open in the treatment arm) separately for compatibility.
- Live-feedback versus held-history changed-choice counts: greater/equal/less, means, ranges and full integer histograms. These are differences between contrasts, not an additive mediation decomposition.
- Shopper-level comparison: changed only under live feedback, changed only under held history, changed under both with the same destination, and changed under both with different destinations. Also record the direct difference in final choices between promoted-live and promoted-held worlds.

## Hypotheses and falsification

1. **No universal amplification:** at least one primary-panel cell has fewer changed choices under live feedback than under held history. A grid with no such cell falsifies this finite-grid conjecture; existence in the grid does not estimate external prevalence.
2. **Indirect route propagation:** at least one primary-panel live-feedback cell has a strict nonvisitor reroute; held history and feedback-off have none. Any strict nonvisitor reroute in either blocked-propagation control requires investigation before interpretation.
3. **Full-browse control:** all budget-6 cells have zero changed choices across all three contrasts. This follows from the fixed utility and common option set and is a mechanism check, not an empirical finding about real shoppers.

Describe a witness using the first qualifying primary-panel cell in loop order (seed, budget, roster, arrival), rather than selecting the most dramatic count. Also preserve the original seed-72 forward case for comparison. Do not describe the first qualifying witness as representative.

## Interpretation limits

The author supplied the catalog, weights, jitter, feedback rule, rosters and all deterministic policies. Findings concern this finite generator only. Holding neutral popularity displays is a cross-world intervention available to the experimenter; it is not a measured natural direct or indirect effect for humans or LLM agents. The panel is convenience enumeration, not a probability sample. Seeds and cells are not independent experimental participants. Zero human participants, zero external model-agent episodes and zero purchases.
