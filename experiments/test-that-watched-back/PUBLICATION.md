# Public release — The Test That Watched Back

This publication packages the completed November 8, 2026 v0.1.0 synthetic study. It is not a new experiment, a live-model trial, an independent review, or an operational adoption.

## Original artifact and unchanged science

Original conversation archive: `Bonded_RSI_The_Test_That_Watched_Back_2026-11-08.zip` (588,315 bytes), SHA-256 `6741636dce21a99f62b69158280668b4e2293ef5aa2301da5436e4c9ad16a782`. Its inventory and release receipt are retained under `provenance/original_SHA256SUMS.json` and `provenance/original_release_receipt.json`.

The frozen experiment, protocol, tests, semantic verifier, reports and original explorer builder are unchanged. All eight public result files and the original standalone explorer are regenerated and must match the original recorded SHA-256 digests before publication proceeds. Original verification receipts are historical records, not new independent validation.

## Publication-only differences

- `index.html` adds gallery navigation and download links around the unchanged explorer. The unmodified standalone explorer is also retained as `The_Test_That_Watched_Back_Explorer.html`.
- `method.html` and `portfolio.html` render the original Markdown, with this publication boundary stated separately.
- Four original presentation PNGs are not copied into the public source transport. The original inventory preserves their hashes; their original bytes remain in the conversation archive. New HTTP-served desktop/mobile screenshots and a fresh browser receipt are placed under `verification/publication/` and are explicitly publication-time checks, not the original captures.
- The public ZIP is a separately assembled distribution, not a byte-identical copy of the original ZIP. `SHA256SUMS.json` covers the public distribution; `publication_receipt.json` records its archive digest. Scientific data equivalence is checked separately from packaging equivalence.
- Statements in the original README/report that no repository push or publication occurred refer to the original study execution. This later publication was authorized separately.

No private human-response file, credentials, operational memory, Castle source, account records, or private continuity material is included. No reuse license is added by this publication; public access is not an open-source license.

## Reproduction

From this exhibit directory run `python src/experiment.py --output reproduced`, `python src/verify.py reproduced`, `python src/test_experiment.py`, and `python -O src/test_experiment.py`. Compare the eight reproduced files against `results/main/`. Run `python src/check_inventory.py .` for the public inventory. Python 3.13/Linux is qualified by the recorded checks; native Windows remains unqualified.
