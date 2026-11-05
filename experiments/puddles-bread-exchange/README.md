# Puddle’s Bread Exchange

An offline-friendly playable exhibit about copied evidence, genuine independent evidence, and shared upstream faults. **Executed synthetic probability model, not a frontier-model-agent trial.**

## Open

Open `index.html` in a modern browser, or serve the repository with `python -m http.server 8000`. The top-level release also includes a one-file `puddles-bread-exchange.html` preview. No runtime dependencies, network APIs, browser storage, analytics, or credentials are required. Only deliberate clicks on external research/gallery links leave the exhibit.

## Reproduce (Windows, macOS, Linux)

Use Python 3.10 or newer, from this directory:

```text
python -m unittest -v test_engine
python -O -m unittest -q test_engine
python verify.py
python mutation_check.py
python reproduce.py --output reproduced
```

`verify.py` intentionally refuses optimized `-O` mode because its exhaustive checks use assertions. Unit tests use unittest assertions and were also run with `-O`.

The regenerated `results.json`, `results-data.js`, and `histories.csv.gz` should match the preserved files byte for byte. gzip uses a fixed zero timestamp. ZIPs use an explicit year-2000 timestamp; they do not inherit unsupported filesystem timestamps.

## Optional browser checks

```text
python -m pip install playwright
python -m playwright install chromium
python browser_checks.py --inline
```

Omit `--inline` to test a local HTTP-served copy. `--chromium PATH` can select an already installed Chromium. The executed checks in this release used `--inline` because the session blocked local HTTP navigation. They did not test a live website or bypass that block. The browser is a fresh local test instance, never a signed-in personal browser.

## Evidence map

- `protocol.json` / `protocol-freeze.json`: local freeze before computation, not independent preregistration.
- `engine.py` / `engine.js`: exact Python and paired numeric JavaScript model.
- `reproduce.py`: complete enumeration and deterministic output generation.
- `histories.csv.gz`: all 45,612 positive-probability histories, with exact rational weights, probabilities, and actions.
- `results.json` / `results-data.js`: all 72 cells, exact/decimal metrics, and browser data.
- `test_engine.py`, `verify.py`, `mutation_check.py`, `browser_checks.py`: executable same-author checks.
- `verification/`: executed receipts, unit-test logs, mutation outcomes, browser captures, and the HTTP-check limitation.
- `method.html`, `REPORT.md`: interpretation, full methods, source context, and limitations.

`CHECKSUMS.sha256` covers the exhibit files except itself and `evidence.zip` (avoiding self-reference). The outer release manifest records the evidence ZIP fingerprint. Do not treat passing tests as independent validation.

## Scope

True source lineage and model parameters are supplied. Copies add no observations; independent evidence has a positive control; different receipts can still share a fault. Display budget is fixed, not compute or information-acquisition cost. Holding has zero toy payoff and must be read with coverage. No real model agent, human participant, purchase, or API request was run.

Publication was **not performed in the authoring session**: the available GitHub integration exposed read actions only. The outer release contains a guarded publication helper and homepage/README inserts. Never mark deployment or traffic effects as observed until separately verified.

No public reuse license has been selected for the lab’s collected exhibits.
