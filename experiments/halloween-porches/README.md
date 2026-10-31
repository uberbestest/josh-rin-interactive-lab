# The Porch That Ate Halloween

**Josh & Rin Lab · 2026-10-31 · Interactive finite reward-allocation model**

Ten programmed goblins, six fictional Halloween porches, and four reward functions. Each goblin visits exactly one porch. Crowded porches use a fair lottery. The reader can alter assignments, switch supplies from finite to abundant, simulate unilateral best-response switches, draw seeded lotteries, and examine the effect of rotating roles.

- **[Open the standalone HTML exhibit](index.html)**
- **[Read the methods and evidence boundary](method.html)**
- **[Run the independent finite checker](verify.py)**

## What is directly reproduced

The six porch values are **8, 6, 5, 4, 3, 2 candies per winner**. Capacities are **1, 1, 2, 2, 3, 1 visitors**. With ten goblins there are **3,003 distinct visitor-count allocations**. A standalone Python 3 checker exhaustively enumerates them. It confirms:

- Unique maximum group candy **43**, at occupancy (1,1,2,2,3,1).
- Exactly two stable arrangements under unilateral expected-personal-candy improvement: **35** candies at (2,2,3,2,1,0) and **38** at (2,1,3,2,2,0).
- When all ten select the eight-candy porch, the limited-capacity group delivers only **8**, whereas unlimited capacity delivers **80**.
- A ten-night rotation of all ten roles in the 43-candy arrangement equalizes individual **expected** nightly candy at **4.3** without reducing group total. It is not an equality guarantee for individual sampled nights.

To reproduce from the repository root:

    python experiments/halloween-porches/verify.py

No packages, network requests, model APIs or external data are needed.

## Evidence distinction

The October 31 conversational report described a separate stochastic learning exercise: 64 seeds per condition, 12,000 training rounds, 2,000 evaluation rounds per group, and these averages:

| Signal | Reported candy / round | Reported empty bags |
| --- | ---: | ---: |
| Advertised sign | 8.21 | 89.54% |
| Individual actual candy | 32.62 | 37.44% |
| Group actual candy | 42.68 | 0.78% |
| Marginal contribution | 42.41 | 1.55% |

**These learning-run means have not been independently reproduced here.** Raw seed-level trajectories, learner implementation and reproducible training receipt were not available to the October 31 publishing step. The new page retains them explicitly as an *earlier reported result*, not as validated values. The published best-response procedure is an accessible, deterministic reconstruction—not that learner or its training algorithm.

See [the methods](method.html) for formulas, agent boundaries, and invalid inferences.

## Operations and limits

- Open the standalone HTML in a modern browser, or use the site gallery. It uses only embedded HTML/CSS/JavaScript.
- Controls and current results are local to the browser. The site has no analytics, API calls, cookies or form submissions in this instrument.
- The reader can directly reassign any goblin. Presets expose the optimal and two stable personal-payoff layouts.
- The finite model is deliberately too simple to draw conclusions about real-world social behavior, real agent deception, learning efficiency, moral entitlements, or AI model alignment.
- The helper checker is a reference exhaustiveness check, not third-party peer review.
- This public release does not contain private continuity or Mirror Node material.

**Receipt:** 2026-10-31 / HALLOWEEN-PORCHES / public finite-model reconstruction, with historical learning-summary status explicitly separated.

_Keep the evidence. Name the bridge. Return the counterexample._
