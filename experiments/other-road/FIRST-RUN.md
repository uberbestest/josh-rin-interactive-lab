# First-run and publication record

November 6, 2026. Version 0.1.0. Protocol and runner frozen locally before first execution; not externally preregistered.

Original protocol SHA-256: `4d93966694f8d04ed0dda925622fccb59774c032626aa6add6214b833dddf4d5`.
Original runner SHA-256: `0f1891a6f387cd1462fe31d61ef1b06fdd126df9313ff7f5f31a1924b5fc26db`.

Scientific first run: 24 cells × 64 seeds × 3,000 rounds. Every cell and seed retained. No excluded or restarted scientific run; no parameter tuning. Expected data digests in `expected-data-sha256.txt` preserve the first run. All final learned actions matched the expected-score oracle.

Software verification followed the science run. A second same-author replay checked every event byte and 18,432 learning snapshots, plus 38,178 rational-arithmetic grid cells. Six deliberate invalid event records were rejected. These checks are not independent scientific replication.

The first local HTTP browser test was blocked by the execution environment. Local browser verification therefore used in-memory offline rendering with the same page and recorded data. It found mobile horizontal overflow; the CSS was corrected without changing scientific source or output. The repaired interface passed 1,827 checks at desktop and phone widths. The publishing workflow separately requires HTTP-served Chromium tests before merge/publication. `browser-verification.json` records which transport was actually tested.

The public report intentionally distinguishes real local computation from an unexecuted live-language-model study. No paid API calls, private lab records, personal messages, credentials, or user account contents are in this release.
