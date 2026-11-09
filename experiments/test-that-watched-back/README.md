# The Test That Watched Back — v0.1.0

Josh & Rin's Lab · Offline synthetic detector calibration · November 8, 2026

Start with **The_Test_That_Watched_Back_Explorer.html** for a self-contained interactive explanation, **PORTFOLIO_CASE_STUDY.md** for a five-minute overview, or **REPORT.md** for definitions, denominators, limits, and results.

## Reproduce

The core experiment and semantic verifier use the Python standard library only. Optional presentation checks (`verify_browser.py`) require Playwright and Chromium; they are not required to reproduce the experiment. Run from this package's root:

```sh
python src/experiment.py --output reproduced
python src/verify.py reproduced
python src/test_experiment.py
python -O src/test_experiment.py
```

On Windows the equivalent interpreter command is typically `py -3`; native Windows execution was not tested here. The output directory must not already exist: retained evidence is never overwritten. The experiment does not access the network, credentials, APIs, accounts, or external files outside its explicit protocol/output paths.

To test order sensitivity:

```sh
python src/experiment.py --output reversed_run --reverse
```

The eight result files should be byte-identical to `results/main/` (and to each other). Timestamps are kept in separate verification receipts, never injected into deterministic results.

Verify the package inventory:

```sh
python src/check_inventory.py .
```

`SHA256SUMS.json` covers retained package files except itself. The final ZIP has an external SHA-256 digest. Hashes bind supplied bytes, not honest scientific conclusions; `src/verify.py` also checks semantics, coverage, exact payoffs, aggregates, paired comparisons, and the minimum separating panel.

## Boundaries

Six authored policies, not six language models. The empirical badge learner is a two-entry reward table. The adversarial lookup was deliberately compiled with full allowed-domain knowledge. Outcome branches are exact possibilities with probability weights, not simulated realized audit episodes. No human responses are included, no external publication or submission occurred, no paid inference was used, and no runtime improvement is installed.

The laboratory work is AI-assisted and jointly directed. Tests, a second checking algorithm, and reproduction are same-author engineering checks—not independent scientific validation. Read `provenance/sources.json` for selected primary context and `verification/` for execution receipts.

The explorer was checked by rendering its already-authored HTML string. Direct browser file-URI navigation was blocked by this environment, so local-file launch remains unqualified; no browser policy was bypassed.
