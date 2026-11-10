# Which Reset Would Tell?
## A complete behavioral panel can still leave the carrier unidentified

**Josh & Rin's Lab · November 10, 2026 · v0.1.0**  
**Record:** `BONDED-RSI-RESET-DIAGNOSTICS-2026-11-10-001`  
**Status:** Executed finite diagnostic-access audit. Same-author verification. No live-model test, independent validation, or operational adoption.

### Result

We extended the explicit dynamics in *The Shape That Remains* from showing ambiguity to identifying the intervention access that resolves it. Across all **81** assignments of four signed carriers, a complete diagnostic scan distinguishes **9**, **21**, **45**, or **81** groups, depending on which carriers can be cleared separately.

| Available source interventions, in addition to a matched state reset | Distinguishable groups out of 81 | Largest unresolved group |
|---|---:|---:|
| No source-specific intervention | 9 | 19 |
| Clear context | 21 | 7 |
| Clear context or world cue | 45 | 3 |
| Clear context, world cue, or acquired-bias field | 81 | 1 |

Every row includes the unchanged-source baseline. “Or” means separate, matched branches, not sequential cuts on one evolving system. The baseline scan is already sufficient to distinguish every total bias possible in this candidate family. More probing through the same interface cannot split mechanisms whose remaining contribution is identical.

**The useful result is not “we detected hidden memory.” It is “this reset interface can distinguish these mechanisms, but not those.”**

### An exact unresolved pair

One system has acquired bias `+1` and prior `0`. Another has acquired bias `0` and prior `+1`. Context and world contributions are zero in both. They produce identical complete trajectories from any equal initial state under every common probe sequence. Clearing or substituting context and world equally cannot distinguish them. Both still have the same acquired-plus-prior sum.

A perfectly targeted acquired-field reset distinguishes the pair. That is an available operation in this authored simulator, not a claim that a commercial assistant exposes it. With a **known and matched prior of zero**, the 27 possible acquired/context/world combinations are all distinguishable using baseline, context removal, and world removal alone. Knowing the common prior changes the inference; it does not change the outputs.

### The counterexample to “a clean-looking result means nothing remains”

Nineteen carrier assignments have aggregate bias zero. **Twelve of those retain a nonzero acquired-bias field.** Opposing contributions cancel. Across the 57 possible single mutable-carrier removals from those 19 assignments, 36 expose a nonzero remaining bias.

For example, `acquired=+1, context=-1, world=0, prior=0` has the same probe response as the all-zero system. Removing context exposes the positive acquired contribution. Removal did not create that contribution; it stopped canceling it. These counts enumerate an authored construction, not a prevalence estimate of hidden memories.

### Apparatus

The four carrier values `(L,C,W,P)` independently range over `{-1,0,1}`. They denote an acquired-bias field, supplied context, a world cue, and a common prior. The acquired field is assigned here; there is no learning algorithm in this follow-up.

```
x_next = clip(2*x + L + C + W + P + probe, -4, 4)
observation = -1 at x_next <= -3, +1 at x_next >= 3, otherwise 0
```

For **each diagnostic query**, clone the original carrier tuple, clear only the selected field, reset dynamic state `x` to zero, apply one probe, and observe. Probes exhaust integers -8 through 8. There are `81 * 4 * 17 = 5,508` recorded responses. Different queries are matched branches, not an interview that may alter its own subject.

The state reset, branch matching, observation function, and targeted removals are stipulated perfectly available. Thus this audit **does not itself test whether a claimed state reset succeeded**. It asks what remains identifiable even after granting that access. Costs, stochastic noise, unknown architectures, human memory, and account-specific behavior are outside this finite apparatus.

### Why the partitions are complete in this model

Let `T=L+C+W+P`. The baseline scan identifies T. For any two possible sums `a<b`, the allowed probe `3-b` makes b's observation positive and a's nonpositive. Therefore the scan separates all nine possible sums.

The context-cut scan identifies `T-C`, so together the scans identify C and `L+W+P`. Adding a world-cut scan identifies W and `L+P`. Adding an acquired-field cut identifies L and therefore P. The corresponding analytic keys are `(T)`, `(C,L+W+P)`, `(C,W,L+P)`, and `(L,C,W,P)`.

Equal keys also imply equal responses to every permitted common probe and accessible source substitution. Induction extends this equivalence to arbitrary shared probe histories. The unresolved pair is not an accident of choosing too few probes. These are elementary properties of the stipulated additive model, not a theoretical-priority claim or a general minimal-test theorem.

The cancellation result also limits how broadly to read the intervention table. The additive assumption makes single cuts sufficient at the last access level. Redundant, nonlinear, or inaccessible mechanisms need not share that property.

### Controls and verification

**24 named tests pass in normal and optimized Python.** They check all analytic partitions, complete raw observations, the learned-versus-prior trajectory alias, source-isolated cuts, input rejection, cancellation, matched and mismatched priors, execution-order independence, and rejection of missing or corrupted evidence. A separate post-result check matched the transition against the unchanged parent implementation on **12,393** input combinations.

All three generated result files reproduce byte-for-byte in forward and reverse execution order. A fresh-extraction check accompanies the full conversation packet. The design and scientific source were internally frozen before enumeration, after deriving the expected algebraic counts. This was not blinded discovery or external preregistration. Repeating our own implementation is not independent scientific validation.

The public distribution includes scientific source, tests, protocol, expected result hashes, and an executable verifier. It regenerates the **entire** 5,508-row record and full equivalence groups locally; it does not require a private archive. Raw result files are generated rather than checked into this public note. The complete local evidence packet retains the original records, logs, parent archive, and reproduction receipts.

### Reproduce this public note

From this directory, with standard-library Python 3.10 or later:

```sh
python verify_public.py
```

This checks published scientific-source hashes, executes the 24 tests in normal and optimized modes, regenerates every result in both orders, and checks the expected result hashes. To retain the generated records:

```sh
python audit.py --out my-results
```

The output directory must not already exist. Syntax supports Python 3.10+; only the runtime in `published_result.json` was exercised. Cross-platform byte equality is not separately qualified.

### What should change in a real-model protocol?

Before collecting scores, list the competing explanations and the operations that can distinguish them. Preserve a reference unexposed to the target episode with the same generic prior, not an imaginary zero-knowledge model. Use controlled synthetic sources and matched branches; keep exact recall separate from structural transfer. Where hidden state cannot be reset or observed, retain the resulting equivalence class rather than declaring its preferred member proven.

The existing prospective live-model study remains **unrun**. This note neither establishes nor refutes a mechanism for any historical conversation. No private conversation excerpts, continuity records, credentials, or operational agent internals are included in this public distribution. Castle and prior exhibits are unchanged.

*The sky is not for sale.*
