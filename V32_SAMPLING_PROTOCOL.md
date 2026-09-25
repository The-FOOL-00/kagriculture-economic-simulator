# V32 SAMPLING PROTOCOL (v1, 2026-09-22)

Kagriculture analogue of diversity-aware opponent sampling (§6 of the brief).
NOT TF-IDF on decks — structured behavior vectors on policies.

## 1. Behavior vector (per expert, from EXP-1 telemetry + registry)

`b(E)` = concat of: wash-size bucket (one-hot 6), sell-order count z-score,
sell-product mix (10-dim simplex), hire-count z-score, fertilize-count
z-score, plant-mix (5-dim simplex), pasture-ratio, terminal-cash z-score
(vs V3 self-play mean), loss-family exposure (6-dim: livestock/fert/sell/
strawberry/mirror/other from V31R2 taxonomy). All z-scores over the population.
Frozen in `V32_STRATEGY_FINGERPRINTS.json`.

## 2. Family assignment

Agglomerative clustering on cosine distance over `b(E)`, threshold 0.15
(near-duplicates merge; V30's P3000/P2900 identical tapes are the canonical
merge example). Each cluster = one sampling family with weight
`w_f = sqrt(n_f) / Σ sqrt(n_g)` — sublinear in member count so the big
V3-clone family cannot drown rare families, while singletons don't dominate.

## 3. Opponent sampling (training)

Per episode: sample family ∝ `w_f`, then expert uniformly within family.
Re-sample every episode (PPO) / every batch-shard (BC). Additionally:

- 20% of episodes: current frozen champion (anchoring).
- 10%: self (learner vs learner, both seats).
- Floor: every family appears ≥5% of episodes (rare-family protection).

## 4. Replay sampling (BC + loss-mining)

Priorities: losses ×3, close games (|d|<$2k) ×2, strong-opponent legs ×2,
catastrophic failures ×4 (cap 10% of buffer), wins ×1. Never wins-only.
`test_v32_sampling` asserts sampler reproducibility (seeded RNG → identical
sequence) and family-floor compliance over 10k draws.

## 5. Drift control

Population versions frozen per experiment (`population_manifest_hash` in every
checkpoint). Adding an expert mid-experiment = new manifest version + new
experiment ID; silently mutating the mixture invalidates all promotion claims.
