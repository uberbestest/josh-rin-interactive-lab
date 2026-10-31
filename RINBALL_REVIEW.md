# Rinball inspection intake — public lab

This repository uses an event-driven **request queue**, not a fake automated peer review.

## Trigger

Every push to `main` in `uberbestest/josh-rin-interactive-lab` runs
`.github/workflows/rinball-inspection-intake.yml` and opens a GitHub Issue titled
`Rinball inspection: <new-commit-sha-prefix>`. Each request records the full
new SHA, prior SHA when available, a comparison link, changed file paths,
and its workflow-run link. Reruns check for existing issues with the same title.

A push may contain multiple commits: the review covers the complete
`before…after` range, not just the top commit. Changed-file lists are
convenience hints, not an authoritative inventory; the GitHub comparison API
may truncate large changes. A force-push or initial push needs manual ancestry
verification.

**A queued issue is not a completed inspection.** Creating the issue does
not call Rinball, guarantee that a dot saw it, execute a browser test, or
certify GitHub Pages deployment. The reviewer must actually ingest the queue.
GitHub Actions or repository permission failures remain visible in the
workflow-run history. Missing issues mean the intake failed.

## Independent reviewer contract (Rinball)

On each intake, read the exact commit contents and material affected by
the push before appraising the builder's description. Inspect all changed
experiment paths and homepage/index links. For non-experiment pushes, perform
scope/privacy and deployment-integrity checks; do not fabricate an experiment.

Review the following independently:

1. **Interaction.** Does the public page load? Can a real visitor operate the
   promised controls and reach meaningful outcomes? Test keyboard/mobile
   flows where possible. An HTML parse or mock DOM test is *not* browser proof.
2. **Science.** What was actually measured? Does the claimed result follow
   from the accessible code, data, methods, controls, and uncertainty? Can
   reported figures be reproduced? Label missing raw runs or unavailable
   external observations as unverified.
3. **Integrity.** Do links, relative assets, citations, and downloadable
   artifacts resolve? Does the new site index actually expose the exhibit?
   Separate repository state from observed live GitHub Pages state.
4. **Safety/publication scope.** No credentials, personal information,
   private continuity/Mirror Node/Cass-V material, or protected internal
   traces. Do not copy private bridge packets into public Issues.
5. **Repair path.** For a failure, cite the exact file/line or reproduction,
   expected versus observed behavior, and the smallest repair. Do not silently
   rewrite the canonical experiment.

## Receipt

Rinball comments on the intake issue with an evidence-backed receipt,
including:

- Reviewer, inspection timestamp, exact commit SHA and before/after range.
- Observed public URLs, files, operations, screenshots/logs or test commands.
- Explicitly separate **observed**, **inferred**, and **unknown** findings.
- Verdict: `PASS`, `NEEDS_FIX`, `NEEDS_EVIDENCE`, or `UNREVIEWED`.
- Severity and actionable reproduction for failures; remaining gaps.
- Private bridge receipt identifier *if one exists*, without public private data.

Close the issue after an actual completed review; leave it open if unreviewed
or materially unresolved. Never equate author self-tests, a green Actions job,
or an accepted builder summary with independent review.

## Rinball intake adapter

Rinball's existing periodic work must explicitly check open Issues with the
`Rinball inspection:` prefix in this repository, process each new full SHA
once, inspect (not merely summarize) the changed experiments, then issue a
receipt. If multiple pushes arrive between checks, process all queued issues
and account for gaps. The GitHub-native trigger survives a sleeping assistant;
**Rinball still needs its own polling or event subscription**. That integration
is not provided solely by this repository workflow.

The public request issue is intentionally not a substitute for the lab's
private Rinball↔Rin provenance/ACK bridge. Keep their identities and receipts
distinct; a GitHub issue is the source event, not a bridge producer record.
