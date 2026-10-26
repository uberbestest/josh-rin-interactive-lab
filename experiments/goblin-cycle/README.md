# The Goblins Accused an Innocent Messenger

**Record:** `GOBLIN-CYCLE-2026-10-26-001`  
**Created:** October 26, 2026 · **Status:** `OFFLINE_SYNTHETIC_EXPLORATION_NOT_EXTERNAL_VALIDATION`  
**Question:** Can a network identify a faulty translation channel without access to a ground-truth dictionary—and what happens when the assumed error budget is wrong?

[▶ Open the standalone interactive experiment](index.html) · [Methods and limits](method.html) · [Raw per-case sweep](results/sweep-records.json) · [Run receipt](results/run-receipt.json)

## The unexpected failure

Four nodes have privately permuted alphabets over the *same synthetic latent symbols*, which only the generator knows. Six reversible translators claim complete symbol-for-symbol dictionaries. The auditor is restricted to those **claimed pairwise tables**. It tests whether direct A→C translation agrees with A→B→C and repeats across four triangular loops.

When exactly **one link** has a pair of outputs swapped, two triangles fail. Their shared edge identifies the bad link; other routes reconstruct it. On the finite test sweep, **768/768** single-fault cases were localized and repaired exactly.

When **two** distinct links are independently tampered with, **11/768** trials produce a wrong *unique* accusation: a link that the generator says was untouched. The proposed repair makes every triangle pass even as the number of wrong links increases from **two to three**. The remaining **757/768** two-link trials do not produce a unique one-fault repair.

**Reproduce the false conviction:** select **Two bad messengers**, alphabet **8**, seed **40**, then reveal the oracle. The generator changed **A–C and B–C**; the conditional auditor blames **C–D**, an innocent link. After the proposed repair, all four triangles close with **three wrong links**.

This is the punchline: internal consistency can *increase* while correspondence to the generating ground truth gets *worse*. A second path vote also endorsed the innocent link in the same case; two implementations using the same relative evidence are not independent external validation.

## Complete finite sweep

| Planted condition | Cases | Blind audit status |
| --- | ---: | --- |
| One swapped link, fully connected four-node graph | 768 | 768 uniquely localized, exact oracle repair |
| Two independently swapped links, four nodes | 768 | 757 ambiguous; 11 falsely localized innocent link |
| One swapped link, three-node triangle | 768 | 768 ambiguous |
| One swapped link, star graph with no triangles | 768 | 768 unobservable |
| All three links incident to one node coherently relabeled | 768 | 768 cycle-consistent, though all three differ from oracle |
| No tampering | 768 | 768 cycle-consistent |

**Total: 4,608 deterministic cases** = 6 conditions × 3 alphabet sizes (8, 16, 32) × 256 seeds (1 through 256). These frequencies are **not** population probabilities or claims about real systems.

## Provenance and reproduction

All source is included in this directory:

- [`research/core.py`](research/core.py) — deterministic synthetic language generator, triangle test, repair logic, separate oracle, and alternative path vote.
- [`research/run.py`](research/run.py) — enumerated finite sweep and JSON receipt.
- [`tests/test_core.py`](tests/test_core.py) — six stdlib unit-test methods including the specific false-accusation witness.
- [`results/sweep-records.json`](results/sweep-records.json) — all 4,608 per-case observations, not a sampled summary.
- [`results/run-receipt.json`](results/run-receipt.json) — tested source hashes and result checksum.

From the experiment folder, with Python 3.10+ and no packages to install:

```sh
python research/run.py
python -m unittest discover -s tests -v
```

**Local evidence:** Six focused Python test methods passed on October 26. The browser's independent JavaScript port reproduced the same status histogram; its regenerated 4,608 JSON rows matched the Python-run output **byte-for-byte** as a Git blob (`7081b5154663dbb7f4451d51ae85ea274c45bd07`; SHA-256 `917a88b5d8546595b83f9e0755296e8cbfa4b36aa1cf793c3013a09c7a7310ce`). Agreement between ports is a useful implementation check but not independent scientific replication.

## Authority and limitations

This is a *small synthetic permutation-synchronization puzzle*, not an experiment on large language models, actual neural languages, social deception, security vulnerabilities, or human behavior. All village alphabets are permutations of a shared latent alphabet; the auditor is artificially blind to the generator's oracle but the reader can reveal it. The planted changes are not intelligent adversaries. All claims refer to complete reversible tables and noiseless triangles, not partially learned translations.

The unique-localization result is **conditional on exactly one faulty edge in the full four-node graph**. The false verdict demonstrates why that condition cannot be silently inferred from a clean repaired scoreboard. Relative consistency cannot establish original semantic truth: coordinated changes are unobservable without external anchors. A clean triangle is not a certified correct translator.

**Related literature:** Gilad Lerman and Yunpeng Shi, *Robust Group Synchronization via Cycle-Edge Message Passing* (2022), [DOI: 10.1007/s10208-021-09532-w](https://doi.org/10.1007/s10208-021-09532-w). Cycle consistency and robust group synchronization are established subjects; no novelty or theorem claim is made here.

**Privacy:** all symbols are synthetic, no participant data or credentials, no external runtime services. Public-facing exhibit and public source only; private Continuity work and Mirror Node architecture are absent.

_The crime was real. The goblin the auditor named was innocent._
