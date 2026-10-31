# Data format and reanalysis guide

All `.npz` files are compressed NumPy archives, loadable with `numpy.load(path, allow_pickle=False)`. There are no pickled objects. Original metrics are also available as JSON and CSV.

## Bargaining arrays

In `results/primary/summary.json`, `cells` defines the ordered 24-cell grid. The seed vector is ordered 2000..2063. The flattened run index is `cell_index * number_of_seeds + seed_index`.

`training_trace.npz`:

- `action`: shape `(12000, 24*S)`, uint8. Action 0..8 means promise that amount and honor it. Action 9..17 means promise `action % 9` and deliver zero. Escrow conditions can choose only 0..8.
- `accept`: same shape, uint8, 0 = reject, 1 = accept. No-refusal cases are always 1.
- `proposer`, `receiver`: same shape, uint8, actual realized personal candy bags, not scaled/shared training rewards.
- `seeds`: independent seed IDs.

The eight bystanders jointly receive 33. The shared objective is `(33+proposer+receiver)/10`. This includes outside supply. The personal objective is the appropriate recorded bag. Outside candy exists only on rejection and is 0 or 3 by cell. Original neighborhood candy is `33+proposer+receiver-outside_candy`.

`policies.npz`:

- `qp`: `(24*S,18)` proposer action values; illegal escrow actions remain zero and are masked out.
- `qr`: `(24*S,9,2)` receiver action values; last axis reject/accept.
- `proposal_probability`: `(24*S,18)` frozen greedy probabilities with uniform ties.
- `acceptance_probability`: `(24*S,9)` frozen acceptance probability for each announced offer.
- `metrics`: `(24*S,13)` exact expectations; names and order are in the summary JSON.
- `seeds`: seed IDs.

`checkpoints.npz`: `qp`, `qr`, and `rounds`, saved every 200 rounds including the final round.

`evaluation_trace.npz`: action, accept, proposer, receiver and seeds, same conventions as training, but 600 rounds and no learning. The exhibit embeds the first 30 rounds for every cell/seed without selecting a preferred trajectory.

`per_seed.csv`: one row per cell/seed, all 13 exact metrics. The bootstrap treats seeds as the replication unit.

`shock_trace.npz`: `shock` and `control` arrays of shape `(30,12*S,6)`; columns are action, accept, proposer bag, receiver bag, neighborhood candy, outside candy. `cell_ids` identifies the twelve original outside-zero cells. `seeds` identifies runs. The shock supplies outside option three on zero-indexed rounds 10..19. Both arms update values with learning rate 0.05 and epsilon 0.05; common random draws pair them.

Robustness folders follow the same format with S=32 and seed IDs 3000..3031. No seeds were deleted. Primary uses alpha=0.05; sensitivity folders use 0.02 and 0.10.

## Baseline arrays

Reward order is sign, personal, shared, marginal; each has 64 seed IDs 1000..1063. Flattened run index is `reward_index*64+seed_index`. Within each run there are ten independently learning agents.

`training_trace.npz`:

- `action`: `(12000,256,10)` uint8 porch choice, zero-indexed among six porches.
- `actual_candy`: same shape, actual won candy, with lottery losers receiving zero.
- `unscaled_reward`: sign payoff, personal candy, total group candy, or marginal contribution, according to the reward cell. Only shared rewards are divided by ten for the Q update.
- `seeds`: independent seed IDs.

`policies.npz`: `q` has shape `(256,10,6)` and `seeds` identifies the within-cell seeds.

`evaluation_trace.npz`: action and actual_candy arrays with 2,000 rounds, no training.

`checkpoints.npz`: Q tables and round numbers every 200 training rounds.

## PRNG and reproducibility

NumPy `default_rng(SeedSequence([seed, stream]))` generates each seed's complete uniform stream. Within-seed draws are shared across experimental cells. Stream IDs are 11 (bargaining training), 22 (bargaining evaluation), 33 (shock/control), 44 (baseline training), and 55 (baseline evaluation). Bootstrap RNG seed is 10312026.

The baseline lottery ranks per-agent independent uniform priorities at each porch and selects up to its capacity. There is no dependence on agent dialogue or model-generated randomness.

`results/environment.json` gives the actual Python and NumPy versions and training-source SHA-256. `results/rerun_receipt.json` records the separate two-seed, different-batch-size reproduction. `SHA256SUMS.txt` covers the final bundle files, excluding itself.
