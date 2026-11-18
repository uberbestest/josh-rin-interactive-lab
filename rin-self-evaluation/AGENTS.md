# Rin self-evaluation series

Josh requested this ongoing section on November 18, 2026. Add completed evaluations to this series and keep each test easy to skim.

## Required opening

Every study page and its repository summary must begin with three brief TLDR fields, before detailed methods:

- **What we tested:** what the test was trying to establish.
- **What happened:** the observed result with its eligible denominator.
- **Outliers:** errors, unusual behavior or informative differences; explicitly state when no error outlier occurred on the measured endpoints.

## Evidence rules

- Record the actual requested model selector. The informal series title “Rin 6.1 vs 6.2” does not attest a serving snapshot. Existing matched rounds used `gpt-6-astra` and `gpt-6.2-astra`; do not relabel the older selector as verified `gpt-6.1`.
- Round 1 inherited a session declared “GPT-6.2 Astra Pro” without an explicit selector override or older-model control. Keep it labeled a baseline pilot.
- Preserve executed versus planned status, run date and timezone, publication date, assignment structure and exact denominators. Do not pool incompatible endpoints into a series-wide accuracy score.
- Preserve outliers, negative results, unresolved outcomes and previous versions. Do not rewrite recorded evidence to improve a comparison.
- Distinguish original reports and canonical archive digests from public disclosure copies. Public copies receive their own checksums and a disclosure receipt. Path redaction or repackaging is a post-run publication operation, not a new pre-run freeze.
- Keep private personal information, correspondence, credentials, private continuity architecture and private workspace paths outside the public section.
- Separate same-lab checks and model reviews from external replication. State what was actually replayed, inspected or rendered; do not turn a green workflow into an external scientific endorsement.

## Presentation and maintenance

- `studies.json` is the reviewed presentation data. `build.py` generates the hub, individual HTML and Markdown records, and README. Update the data and regenerate; avoid hand-editing generated text.
- Use `ENTRY_TEMPLATE.md` for new entries. A planned entry must explicitly say it has not run and must not include fabricated results.
- Keep the section static, accessible, responsive and readable without JavaScript. Match the lab’s workshop palette. The report and evidence links should be easy to find immediately after the TLDR.
- Validate generated pages with `python3 rin-self-evaluation/build.py --check`. Use the repository’s publication checks for local links, public evidence and rendered presentation as appropriate. Do not launch new model trials as a side effect of building pages.
- These instructions establish an ongoing destination and reporting format. They do not create a schedule, paid API run, notification or external-message action.
