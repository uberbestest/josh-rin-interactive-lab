# Agent Attention — research section

**Public entry:** [Interactive Agent Attention Map](index.html)  
**Methods:** [Evidence hierarchy, pilot protocol, and limitations](method.html)  
**Structured pilot reconstruction:** [15 recorded events and 3 agent notes](pilot-trace.json)  
**Proposed future raw event schema:** [record-schema.json](record-schema.json)

This section connects three distinct observations without laundering their evidence grades:

1. **Scripted mall worlds** (October 26): 2,048 paired parameter cells of 24 deterministic shopping policies, demonstrating attention/selection divergence in the *authored model*.
2. **Controlled mall follow-up** (October 27): a held-neutral-history comparison that finds both amplification and suppression in the same scripted generator.
3. **One actual web-shopping feasibility pilot** (October 31): 15 reported browser operations, three contemporaneous notes, real public sites and product listings, but personalized browser and incomplete durable raw evidence export. This is neither clean isolation nor a multi-agent external benchmark.

The map visualizes operation events, not mental attention or reading duration. E03, E07 and E14→E15 remain qualified. Target and SPETSBOJ were search-only, not opened retailers. No purchase was made; observed item price was historical, not verified current.

**No new outside-agent runs were executed in producing this section.** The section is an evidence-led synthesis and interactive mapping audit. A fresh clean-browser multi-agent study is an explicitly separate next phase, gated on raw-capture verification.

## Research findings visitors can investigate

- Opened ≠ selected: seed 17 Golden Goblin Goods acquired 13 promotional opens and zero selections in the fixed scripted world.
- Promoted ≠ rewarded: the selected seed-72 ghost seller gained 11 opens without a target selection while final choices of 16 other shoppers changed.
- Feedback is not monotonically amplifying: the October 27 512-cell panel includes 23 instances where live feedback reduces changed final choices versus held neutral history; all are scripted outcomes.
- Real navigation isn't fully explained by clicks: the actual pilot included fresh Google queries, retailer re-entry, search-only branches, failed/unconfirmed actions and a delayed URL transition.

These are **different datasets and designs**, not an independent three-study replication. Full methods and original links are in [method.html](method.html).

## Reproduction / checks

From repository root:

```
python3 agent-attention/audit_map.py
```

The checker verifies event IDs, classifications, known anomalies, encoded graph data, navigation links, and required uncertainty labels. It does not pretend to reproduce missing browser pixels.

Run the broader deterministic mall replay independently through its existing [tests](../experiments/goblin-shopping/tests/verify.cjs) and [follow-up runner](../experiments/goblin-shopping/notes/crowd-feedback/run.cjs).

**Publication boundary:** public-source and qualified site material only; no private continuity, personal browser identity, credentials, or protected lab notes. The working project has no general open-source license selected.
