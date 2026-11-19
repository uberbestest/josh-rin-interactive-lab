# RLE Castle: The Faire — development overview

**Release:** November 19, 2026 · Presentation preview **0.2.0**. This is a version of the public overview, not the executable.

[Open the project overview](index.html) · [Read image and design provenance](provenance.json)

## What this release adds

The updated overview explains the full JRPG adventure, the intended first preview route from the Faire to the Castle entrance, and the optional Recursive Learning Environment (RLE) layer. It separates current public evidence, first-person play feedback, design goals, and capabilities that still require verification. The lab's [evaluation section](../../evaluations/) provides a separate home for actual research records.

The game remains the full adventure: exploration, narrative, combat, companions, secrets, minigames, world presentation and progression. The short preview route introduces that project; it does not replace or set the final scope of the game. The RLE layer is intended to observe ordinary actions and support replay and controlled comparisons while preserving normal human play.

This release contains an overview and one still-image crop. It contains no playable executable, replacement game, new Castle model-agent trial, or assertion that the current local build implements all the described goals.

## Provenance

The same screenshot crop published on October 31 supplies the preview image. Its precise build revision and capture time are unknown. `provenance.json` retains the original source hash, rectangular crop, encoding and output hash. Surrounding desktop, chat and notification overlays were excluded before resizing; no game content was generated or filled in.

Josh's October 31 footrace feedback is credited as a first-person report. The current game source and executable were not accessed or tested during this publication pass. Neither the rejected October 18 prototype nor the rejected car-racing screen is used.

The design update follows the revised November 14 scope record, `RLE-CASTLE-AGENT-LAYER-HANDOFF-2026-11-14-001-revision.1`, and Josh's November 19 request for a public overview and preview rather than a completed game. That handoff is a design record, not implementation evidence. Its private paths and unrelated internal material are not published.

## Website verification

Run from the repository root:

```sh
python projects/rle-castle/test_preview.py --output-dir /tmp/castle-preview-qa
```

The check validates the published crop hash, local page assets, image loading, anchor navigation, readable layouts at 320, 390, 768 and 1440 pixels, keyboard disclosure, and operation with JavaScript disabled. With `--output-dir`, the receipt and screenshots are written to the requested directory; omitting it writes to this project's usual review locations.

The initial November 19 attempt was blocked before page inspection because the local environment denied Chromium process socket creation. The committed `BROWSER-RECEIPT.json` records that limitation and the separately completed static checks. The committed `review/project-*.png`, `review/homepage-project-*.png`, and `review/browser-receipt-2026-10-31.json` remain historical October 31 presentation evidence. They are not validation of this updated overview. A later CI or browser receipt should identify its exact source revision and measured scope.

These are same-lab website checks. They do not establish current game behavior, visual acceptance by Josh, external replication, or API trial performance.
