# Candy Revolt — replay repair v0.1.1

## What was wrong
The original Play control advanced correctly in Chromium, but it displayed only
frozen evaluation policies. All 1,536 embedded thirty-round sequences repeated
one action/decision/bag record. In the default run every round was an accepted
three-candy transfer, leaving five candies for each negotiator. The existing
tests verified counter advancement but did not detect the uninformative replay.

## What changed
The default is now **Recorded learning / Early**. The exhibit embeds three
consecutive windows from the original saved training archive: rounds 1–30,
5,986–6,015, and 11,971–12,000. Those same windows are used for all 24 conditions
and all 64 seeds. No trajectories were selected by outcome and no new agents
were run. Changes include exploration, not just learning progress.

Frozen evaluation remains available, with an explicit repeated-outcome notice.
The display now includes receipt numbers next to Play, a progress indicator,
per-window cumulative bags, a recent-receipt ledger, speed controls, keyboard-
accessible receipt selection, and a data export with source SHA-256 hashes.
The existing all-seed figures are explicitly labeled final-evaluation summaries.

Window totals sum the displayed window up through the selected receipt, not
lifetime training or the number of times the viewer pressed Play. Rewinding
recalculates them. Recorded learning is a replay, not live training in the browser.

## Evidence preserved
All original embedded scientific data, protocol, baseline results, evaluation
records and statistics are unchanged. This is a presentation repair, not a
new scientific release, independent peer review, or a GitHub publication.
The original research ZIP and its checksums remain untouched.

## Verification
347 checks passed, including actual Chromium playback, pause/restart, scrubbing,
condition and seed changes, every original evaluation record against its raw
archive, every added training-window record against its raw archive, cumulative
accounting, export behavior, reduced motion, and page widths 320/390/768/1440.
Default training round 1 is accepted with bags 3 / 7; Play immediately advances
to recorded round 2, a refusal with bags 0 / 3. No external resource requests or
JavaScript errors were observed. Test loading used page.set_content; the user's
in-app preview and a public deployment were not tested.

## Files / reproduction
Open The-Two-Candy-Revolt-Fixed.html directly; it is self-contained.
To rebuild from the ORIGINAL research ZIP (requires Python and numpy):

    python build_replay.py --source path/to/Candy-Revolt-Research-Bundle.zip

The portable builder was executed and produced byte-identical output.
The source template and validation receipt are included. This compact repair
bundle does not replace or include the original raw-data archive.
