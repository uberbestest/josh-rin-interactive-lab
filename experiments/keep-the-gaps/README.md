# Keep the Gaps

**Interactive finite-model reasoning workbench · Public exhibit, 2026-10-26**

[Open the standalone HTML](index.html)

## Question

What does the supplied evidence *require*, and where does a conclusion depend on an assumption that could be withdrawn? The interface contains **three synthetic ledgers**. Visitors choose a case, toggle available premises, change the claim being evaluated, and inspect compatible assignments and counterexamples.

This is not a source authenticator, probability estimator, causal engine, general-purpose truth detector, permission enforcer, or safety certification. The word "observation" in a synthetic ledger is a user-supplied designation, not independent verification.

## Artifact and provenance

- **Archived source:** [original.html](original.html) preserves the original standalone HTML from the packaged review candidate byte-for-byte, including its checker and original UI.
- **Archived source size:** 1,466,549 bytes.
- **SHA-256 (original.html):** `79eeac3bbd76c27916019d85867ddfe2c861205ad8f38210e7f1f383d6316901`.
- **Git blob SHA-1:** `9ba8c316f78e1d1cbac2c445fada0fb09ab388f0`.
- **Internal release receipt status:** `PASS_FINAL_PACKAGED_EXTRACTED_CANDIDATE_CHECKS` for `0.1.0-review.2` (not a public release certification).
- **Receipt-reported checks:** 92 canonical normal Python tests, 92 optimized Python tests, 13 fixture-fidelity tests, and 27 presentation tests passing in the candidate package. Those numbers report the packaged verification; they are not a fresh independent re-run on GitHub.

The HTML includes its own provenance and checker reports. Its embedded data is bundled; no remote evaluation service is implied.

## Known verification gaps

The packaged receipt explicitly leaves native report downloading in a normal browser to owner smoke testing. File-protocol execution, physical mobile devices, assistive technology, and a broad browser matrix are not established. Normal file-URL and localhost navigation were **blocked by the execution environment's navigation controls**. A narrower injected-document Chromium smoke check using `page.set_content()` rendered all three examples, exercised premise toggles and reset, exported parseable checker report JSON, and reported no JavaScript page errors. That check **does not** qualify navigation from an ordinary hosted page, physical browsers, or all downstream export semantics.

The finite model checks only its declared state variables and three included examples. Omitted variables and unsupported conclusions remain omitted; a green result must not be treated as proof outside the declared model.

## Try it

1. Open the HTML in a browser (or serve the repository with `python -m http.server 8000`).
2. Select each of the three ledgers.
3. Toggle a premise; compare the compatible cases and counterexample.
4. Change the claim. Look for `unresolved`, `entailed`, `refuted`, or `inconsistent` and inspect the stated scope.
5. If report export is available in your browser, verify the selected premises and claim match the downloaded record.

**Release status:** a publicly available packaged candidate, not independently validated. Successful GitHub hosting is not a substitute for the unresolved browser checks.

## Gallery navigation update · 2026-10-27

The public [index.html](index.html) adds only a scoped navigation bar and its styles, linking to the gallery and this exhibit's methods. The scientific scripts, embedded data, and original instrument content are unchanged. The [archived standalone original](original.html) retains the historical bytes and hashes recorded above. Those historical hashes identify `original.html`, not the navigation-adapted `index.html`.
