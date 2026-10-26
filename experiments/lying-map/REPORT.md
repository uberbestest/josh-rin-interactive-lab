# Goblin Games: The Lying Map

**Run:** RIN-GOBLIN-LYING-MAP-2026-09-30-001  
**Date:** September 30, 2026, America/New_York  
**Host:** Rin, for Josh  
**Status:** Primary and stress runs complete; post-hoc budget sensitivity complete; playable arcade built.

## The finding

The ranking changed when the action budget changed. With eight actions, the
Contact Repairer plus a rescue rope outperformed the Scout plus a rope. With ten
actions, the Scout plus rope solved every initially solvable case in the exhaustive
one-error family, while the Repairer plus rope did not.

This is a result about five fixed, host-written algorithms in a tiny finite world.
It is **not** a measurement of LLM intelligence, fresh-model-worker behavior, or a
model upgrade. The historical fresh-worker launcher was not exposed in this room.
Instead, this new variant used ten real deterministic Python processes. It does not
replace or retroactively reinterpret the earlier Hidden Lever games.

## What actually ran

The arena has four rooms: Camp, Mill, Pond, and the terminal Vault. Each nonterminal
room has two doors, and every door may lead to any room, including itself. Thus
there are 4^6 = 4,096 possible worlds. A player starts at Camp. Reaching the Vault
wins. Moving, inspecting a local door without entering it, and using the one-use
rope each cost one action. The original budget was eight actions.

Each map labels six door destinations. In the primary suite, a map is either fully
accurate or contains exactly one wrong label. Every world was paired with every
allowed map: 4,096 accurate controls plus 73,728 one-error cases, for **77,824
primary cases per policy**. Of the 4,096 worlds, 3,024 have a route to the Vault and
1,072 do not. Initially impossible worlds remained in the suite as negative controls.

Ten policies ran each case, giving **778,240 primary episodes**. A separate frozen
sample of 4,096 distinct two-error world–map pairs added **40,960 stress episodes**.
The sample contains 3,001 initially solvable pairs. Stress results are not exhaustive
and were not mixed into the primary rates.

The ten programs ran in two waves of five. All ten exited successfully, with unique
process IDs, and no retry or replacement. These are local processes sharing a
host-authored codebase, not security sandboxes or independent AI contexts.

## The five matched pairs

Each pair has the same decision rule with or without a rope. All policies have
access to the same move and inspection actions; some choose not to inspect.

| Slots | Policy | Decision rule |
|---|---|---|
| 01 / 02 | Map Believer | Follow the original map; never correct route planning. |
| 03 / 04 | Contact Repairer | Move, update a sign when observations contradict it, and replan. |
| 05 / 06 | Map-free Explorer | Ignore the map and seek the nearest unobserved door via observed edges. |
| 07 / 08 | Scout | Use the Repairer's plan, but inspect a new door before traversing it and replan after inspection. |
| 09 / 10 | Single-fault Detective | Begin as Scout; after finding one wrong sign, stop inspecting under the at-most-one-error assumption. Stop explicitly if a second wrong sign is detected. |

Odd slots have no rope; even slots have one. Every rope uses the same deliberately
conservative trigger: observations must establish that the player's current
reachable component has no unknown door and no path to the Vault. A return to Camp
costs one action and preserves observations. This is not an optimal rescue policy.

## Original scoreboard: eight actions

These rates use only the **54,432 initially solvable, exactly-one-error cases**.
They do not include accurate maps, impossible worlds, or the two-error stress set.

| Policy | Without rope | With rope | Additional wins from rope |
|---|---:|---:|---:|
| Map Believer | 48,186 / 54,432 — 88.525% | 48,186 / 54,432 — 88.525% | 0 |
| Contact Repairer | 54,012 / 54,432 — 99.228% | 54,390 / 54,432 — 99.923% | 378 |
| Map-free Explorer | 52,740 / 54,432 — 96.892% | 54,180 / 54,432 — 99.537% | 1,440 |
| Scout | 53,858 / 54,432 — 98.945% | 53,858 / 54,432 — 98.945% | 0 |
| Single-fault Detective | 53,900 / 54,432 — 99.023% | 53,928 / 54,432 — 99.074% | 28 |

Rope availability produced no paired success-to-failure reversals in the recorded
suite. The Believer never activated the rope in the solvable one-error cases: its
observations never satisfied the common trap-certification trigger. Zero gains
there do not establish that recovery tools are generally useless, nor do they
show what a different rope trigger would do.

In accurate-map controls, all map-based policies solved all 3,024 solvable worlds.
The map-free Explorer solved 2,930 without a rope and 3,010 with one. Its identical
rate across accurate and one-error maps is expected: it ignores those maps. Every
policy recorded zero wins in initially impossible worlds.

## Three concrete surprises

### 1. The correct answer can arrive one action too late

Relative to contact repair, Scout gained 326 wins but lost 480 other wins in the
solvable one-error set, without ropes. The net difference was 154 fewer wins.

In illustrative case **005621**, the map hides the real Vault exit. Repairer enters
that door on its eighth action and wins. Scout discovers the same exit with its
eighth action, but the action was an inspection. It is still outside the Vault when
the clock expires. A ninth action is enough to enter.

The witness was selected after the results. It is not a held-out discovery, and the
fixed policies were not optimized for the action budget.

### 2. Correcting the map does not move you out of the trap

In case **008407**, Camp B correctly leads to Mill. At Mill, door A is falsely
labeled Vault; it actually leads to Pond, whose two doors both return to Pond.

Repairer takes that door, notices the mismatch, and corrects its map. It is now
correct about where it is, but there is no ordinary route out. Without a rope it
loses. With a rope, it records both Pond exits, returns to Camp, and reaches the
Vault through Mill B in seven actions. Scout inspects Mill A before entering,
changes its plan, and wins in five actions.

Across the solvable one-error suite, the no-rope Repairer entered a no-exit region
in 390 cases. In 136 cases its first detected contradiction coincided with a move
arriving in such a region. Knowledge recovery and physical recovery are different
operations in this environment.

### 3. A verified local destination is not a verified route

Scout still entered a no-exit region in **64** solvable one-error cases. In witness
**030770**, the first door really does lead to Mill, just as its sign says. Scout
checks that fact and enters. The false sign is deeper inside Mill, where it promises
an exit that does not exist. Checking that deeper door now is too late to avoid
entering the closed region.

Scout plus rope activated its rope in all 64 such cases at the eight-action budget,
but gained no additional wins at that budget. In the displayed witness it reaches
the right door, inspects it on action eight, and again has no action left to enter.

## Post-hoc supplement: change only the action budget

After observing these failures, a separately documented supplement reran the same
54,432 solvable one-error cases for Repairer and Scout, with and without ropes.
It used a maximum of twelve actions and recorded first-arrival time. These policies
do not receive the remaining budget, so shorter-budget results can be read from
the same action prefixes. This added **217,728 supplemental episodes**.

The derived eight-action success/failure IDs matched the frozen original runs
exactly, not merely their aggregate counts. The supplement was planned after seeing
the primary results; it is a sensitivity check, not preregistered confirmation.

| Policy | 8 actions | 9 actions | 10 actions |
|---|---:|---:|---:|
| Repairer, no rope | 54,012 | 54,042 | 54,042 |
| Repairer + rope | 54,390 | 54,420 | 54,420 |
| Scout, no rope | 53,858 | 54,314 | 54,368 |
| Scout + rope | 53,858 | 54,360 | **54,432** |

Every denominator is 54,432. The no-rope ranking reverses at nine actions; the
rope-equipped ranking reverses at ten. At ten actions, Scout plus rope solves all
cases in this finite solvable one-error family. This is not a universal guarantee.

One diagnostic explains a remaining Repairer failure: after using its rope, it can
traverse another unobserved door back into an already known trap. The algorithm
explores unknown doors without first checking where they lead. The selected trace
is retained separately; no policy was patched and no original result was replaced.

## Stress test: an assumption that saves work can also invalidate the plan

Detective's shortcut is legitimate inside the stipulated at-most-one-error family.
After one sign is disproved, the other unobserved signs must be accurate under that
assumption. Compared with Scout without a rope, Detective gained **42 wins and lost
none** on the solvable one-error cases. On their 53,858 common successes, it used
10,662 fewer actions in total.

On the **3,001 solvable sampled two-error cases**, Scout without a rope won 2,917
(97.201%), while Detective won 2,845 (94.802%). The paired comparison was 48 wins
gained by Detective and 120 wins lost. This deliberately violates Detective's rule.

The implementation explicitly stops when a second wrong sign is observed, and
that stop itself accounts for some failures. Thus the stress result combines
reduced inspection with a specified assumption-failure response. It does not isolate
“trusting too much” as a single cause, and an honest stop is not an undisclosed error.

## Receipts and validation

The bundle contains exact inputs, code, raw per-case outcomes, worker receipts,
case-level supplemental outcomes, and illustrative traces. Primary code and inputs
were hashed before workers launched. Local hashes are not external timestamp
attestations, and these checks are not an independent audit.

Thirteen prelaunch tests passed, including a separate brute-force enumeration of
paths of length at most three to check the reachability oracle for all 4,096 worlds.
Sixty-five post-run assertions passed, including ordered case IDs, action limits,
rope permission, raw-return hashes, impossible-world controls, and absence of
second-contradiction stops inside the one-error family.

The self-contained browser arcade has manual play, all ten clockwork policies,
five selected cases, fresh one-error worlds, a spoiler-protected display of the
true map, move receipts, the original scoreboard, and an exploratory budget control.
The spoiler display is a user-interface choice, not a technical secrecy boundary.

Its JavaScript engine matched all outcome fields in **2,450 sampled Python results**
covering all policies and all three error levels. Manual play, replay controls,
budget controls, desktop/mobile layout, and absence of script exceptions and
external network requests passed the recorded checks. The initial direct file-URL
navigation attempt was administrator-blocked. That failure is preserved. Browser
rendering and interaction were tested through Playwright's supported HTML-content
API; direct file-URL opening was not verified in this environment. No browser access
policy was changed.

## Interpretation boundary

The useful result is not “caution wins” or “speed wins.” These particular policies
show different interactions between correction, inspection, recovery, and the
budget under a fully specified task. A benchmark's action budget can change their
ranking without any change to the policies.

No claim is made about model improvements, AI-agent personalities, optimality,
real-world deployment reliability, independent validation, or security-grade
isolation. The host wrote the environment, policies, and tests. The example traces
are illustrative post-hoc selections. The stress set is sampled; only the stated
primary family is exhaustive.

**Actual star ledger: unchanged. Awards remain Josh's decision.**
