# Agent Attention: methods, scope, and evidence hierarchy

**Study line:** AGENT-ATTENTION-LINEAGE-2026-10-31-001 · Halloween research synthesis · public, no accounts or purchases.

## The question

Where is an agent's **observable browsing activity** allocated when asked to shop with an open-ended goal? Which sources are surfaced but never opened; which are opened but not selected; when does a visited source change a later destination; and can the journey be reconstructed from the evidence actually delivered to the agent?

**Terminology:** These are logged operations, delivered excerpts, recorded visits, and stated decisions—NOT private cognitive attention, reading duration, endorsement, market share or causality. The unit of analysis is a browser operation within a session, not a human shopper or an independent research participant.

## Three evidence tiers

| Instrument | What actually happened | What it can support | What it cannot support |
| --- | --- | --- | --- |
| [Original shopping mall](../experiments/goblin-shopping/index.html), 2026-10-26 | 24 **scripted** shoppers in paired neutral/promoted worlds; 2,048 parameter cells, 98,304 deterministic policy executions | Given its exact coded preferences and catalog, changing promotional copy can redirect browse routes and final simulated selections, sometimes without the target earning a selection | Claims about real agent choices, purchases, population prevalence or independent models |
| [Crowd feedback follow-up](../experiments/goblin-shopping/notes/crowd-feedback/index.html), 2026-10-27 | Fixed 2,048-cell five-world intervention grid, 512-cell declared primary panel | Demonstrates within the authored generator that live popularity signals can amplify, tie, or suppress a promotional change | Empirical mediation claims for real agents or humans |
| [Single browser pilot](pilot-trace.json), 2026-10-31 | 15 agent-requested browser operations, researcher/operator mediation, personalized session; 3 contemporaneous note excerpts | A qualitative **reported** Google → guide → blanket → lamp/bulbs → search alternatives → blanket-return sequence | A clean agent replicate, an independently archived raw trace, proof of what content was mentally read, generalization to other agents |

These sources are not three replications of one result. The synthetic model deliberately controls its inputs. The real-world pilot only describes one path in an unisolated browser.

## October 31 pilot: the exact open-ended task

> I'd like something that would make my evenings at home a little nicer. I don't really know what I want. Try to keep it under $50. Find me something worth considering, but don't buy anything.

A separately tasked agent selected each browser operation. A researcher/operator executed those operations and relayed *selected excerpts and viewport descriptions* rather than passing complete browser output or screenshot pixels to the agent. The browser already had a signed-in Google session and location-influenced retailer settings; a clean, logged-out profile was not established.

The original report counted 15 agent-requested browser operations in 15m14s, including five search queries, with 15 snapshots and screenshots *reported*, and three contemporaneous agent notes. The full raw recorder history was **not exported to durable evidence files**; the present JSON is an auditable reconstruction of a saved narrative, not a recovered raw browser log.

**Explicit unresolved areas:** E03 affiliate click did not confirm navigation. E07 modal contents were not observed. E13's full original output had to be recovered from a transient capture rather than a second visit. E14 selected a larger variant but the capture mixed old/new state; E15 confirmed its price and URL, while the exact transition time remained unobserved. Search-only Target and SPETSBOJ options were *surfaced*, not visited or demonstrated as consciously rejected.

**Outcome:** the agent's final contemporaneous note selected an Amazon PAVILIA Latte 60×80 blanket, shown at $19.99 at the time. Shipping, tax and independent review quality were unresolved. No purchase occurred. Product links and prices are historical observation references, not contemporary buying recommendations.

## How the interactive graph is assembled

Nodes represent **operation event IDs** E01–E15, not websites as latent cognitive states; edges connect successive *reported* operations in chronological order and do not assert unseen redirects. Three lanes distinguish result pages, confirmed visits, and other/uncertain actions. Node E14→E15 has an uncertain transition time. A new search branch can be originated by the agent without an on-page click from the preceding retailer.

The visual's “opened only” filter suppresses search-only results and failed attempts. Those events remain in the underlying evidence series; filtering is a display choice, not a deletion. Each selected node has its source operation, observed result, evidence qualifier, and agent note **only when an agent note actually exists**. The two unanswered modalities—offscreen accessibility text and viewport images—must never be equated with cognition.

Metrics are deliberately nonexclusive across stages. An operation count includes searches, clicks and inspections; it is not a denominator of independent page visits. Elapsed timestamps bracket operations, **not time spent reading**.

## Mall result interpretation

In the original seed-17 scripted mall demonstration, with three opens per shopper and visible prior-visit counts, the promoted listing increased Golden Goblin Goods' opens from **0 to 13** while its selections remained **0**. Four of 24 final destinations changed. Concentration of recorded opens across *all* stores (HHI) declined from **0.2550 to 0.2199**. The target's greater visibility therefore coexisted with lower *overall* concentration in this particular authored setup.

In the **post-hoc selected** seed-72 ghost seller, the target gained **11** additional opens and still received zero selections, but **16** simulated shoppers selected a different *other* store. The five indirect changes use the original looser "never opened promoted store in treatment" definition, not the later stricter condition of never visiting in either arm. In the formal follow-up, strict nonvisitor reroutes are reported separately.

The held-neutral-history study compared live social feedback with each shopper seeing its neutral prior-visit counts. Across the *declared* 512-cell mixed-roster, budget-two-or-three panel, live feedback yielded more changed final selections in **398**, ties in **91**, and fewer in **23** cells. In **21** ties, which individual shoppers changed differed even though the aggregate count did not. This panel is an enumeration of authored cases, not a probability sample. Removing feedback entirely is a different intervention from holding the neutral visible history fixed.

**Important:** A 0-cart target may still alter the allocation of other carts. But the mechanism here was authored; it does not establish that real agents behave this way.

## Next empirical experiment: protocol, not a result

1. Use the task above *verbatim* for a single pilot with a demonstrably fresh-context agent and **isolated, logged-out browser**; record model/version, tool configuration, locale, viewport, and environment.
2. Append **every** requested operation, result, failure, link target, timestamp and delivered excerpt to JSONL *before advancing*. Capture screenshot pixels and accessibility output durably with content hashes and event pointers. Do not substitute a post-hoc narrative.
3. Ask for brief decision notes after five operations and at completion; record these as **statements** rather than explanations of hidden causal reasoning.
4. Stop at 20 minutes or 50 agent-requested browser operations. No purchases, logins, personal-data submissions, or interactions requiring unsafe bypasses.
5. Have a separate reviewer reconstruct paths from the archived data, recording absent screenshots, missing transitions and contradicting summaries; classify outcome and trace quality independently.
6. **Only after the instrumentation passes** run ten independent contexts under the same assignment, preserving all cap/abort/no-recommendation outcomes. A larger agent cohort, attention-market measurements, and causal interventions are *not yet conducted here*.

**Minimum public schema:** [record-schema.json](record-schema.json). Every event must distinguish `observed`, `stated`, `inferred`, and `unknown` fields, as well as delivery to the agent versus retained only by the recorder.

## Original sources and context

- [Where Do the Goblins Go Shopping? model and data](../experiments/goblin-shopping/README.md)
- [The Shop That Sold Nothing, post-hoc witness](../experiments/goblin-shopping/notes/ghost-seller.html)
- [When the Crowd Gives a Cart Back, fixed protocol](../experiments/goblin-shopping/notes/crowd-feedback/PROTOCOL.md) and [full findings](../experiments/goblin-shopping/notes/crowd-feedback/FINDINGS.md)
- [August 27, 2026, Wharton Generative AI Labs](https://gail.wharton.upenn.edu/research-and-insights/technical-report-agentic-shopping/): separate model-shopping experiments on source context/order/presentation; not a replication or direct validation.
- [October 29, 2026, Microsoft Clarity](https://clarity.microsoft.com/blog/agentic-analytics-what-agents-do-on-websites/): observations of agent-classified sessions; warns those sessions can include human actions, so session labels do not by themselves identify autonomy.

The pilot chronology originally appeared as a saved **October 31 conversational report**. It lacks an exportable raw source archive. We have not silently upgraded that source to independently verified telemetry. This public reconstruction intentionally omits signed-in account identity, retailer location specifics and private lab materials.

**Integrity principle:** A map's arrows should be earned by recorded transitions. Do not infer a reading-time heatmap, attention percentage or causality from these partial observations.
