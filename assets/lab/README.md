# The illustrated lab

Original visual identity for **Josh & Rin's Lab**, October 31, 2026.

The website illustration, `halloween-workshop.svg`, is deterministic, original vector/pixel artwork authored specifically for this lab. Its reproducible source is `.publishing/lab-makeover/draw_room.py`. No third-party stock photograph, borrowed character sprite, remote font, or icon library is used. A separate image-generation concept was explored in the design conversation; the live-site SVG is an original code-drawn implementation, not a screenshot masquerading as working UI.

The scene contains Pumpkin Rin, Puddle the duck, Mote the lantern moth, two fictional goblins, instruments, a moonlit window and a workbench. These are decorative mascots. The drawing is not a screenshot of an experiment or evidence that any research action occurred.

## Presentation changes

- Responsive homepage identity, original illustrated room, clear experiment entry points, and an About section.
- The existing ten research articles, links, support terms and evidence descriptions are retained.
- Optional topic filters; all ten experiments remain accessible with JavaScript disabled.
- Native keyboard-accessible evidence disclosures.
- A deliberately decorative Puddle greeting. It calls no model, stores no visitor data, and has no effect on experiment records.
- A small shared illustration on the Agent Attention hub. Its existing scripts and embedded trace are preserved byte-for-byte by the build assertions.

## Review and reproducibility

`DESIGN-RECEIPT.json` records the preservation checks. `BROWSER-RECEIPT.json` is written only after actual Chromium interaction checks pass. Review screenshots are under `review/`.

From the repository root:

```sh
python .publishing/lab-makeover/draw_room.py
python .publishing/lab-makeover/apply.py
python .publishing/lab-makeover/test_makeover.py
```

The apply script reconstructs the presentation from base commit `e9a1edc8c64b29d766b286f778fe2a553c66235f`; do not run it over later content changes without reconciling them first. Browser tests require Playwright and Chromium.

Author-run checks are not independent scientific validation. Josh's visual review is pending. No project or game is advertised as available unless there is an existing public destination. No private lab continuity material is included.
