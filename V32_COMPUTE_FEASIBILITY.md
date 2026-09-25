# V32 COMPUTE FEASIBILITY (measured 2026-09-22, CPU-only)

Hardware: 12 cores, ~7 GB RAM, no GPU. Runners: `.venv/bin/python`
(kaggle-environments 1.32.7). All numbers measured, not projected from the
PTCG writeup.

## 1. Environment throughput (measured, EXP-1)

| Leg type | Mean wall | n | Per-worker agent-steps/s |
| :--- | :--- | :--- | :--- |
| Adapter/file experts (V3/A7/W72/W2015/A1/A2/V25P3/DMITRII) | ~13.3 s | ~350 | ~108 |
| V22R1-involved (AEC counterfactuals) | ~160 s | 96 | ~9 |
| + torch-1M policy in the loop (projected) | +1.0 s | — | ~101 |

Leg = 720 env steps × 2 agents = 1440 agent-steps. 10 workers → ~1000
agent-steps/s aggregate with fast experts; a V22R1-heavy mixture collapses to
~90/s. **V22R1-class opponents are ~12× too slow for the training mixture**
and are restricted to eval-only lanes (champion suite, promotion tests).

## 2. Scale arithmetic (fast-expert mixture, 10 workers, rollouts only)

| Budget | Rollout wall | Verdict |
| :--- | :--- | :--- |
| 1M agent-steps (~700 legs) | ~17 min | trivially feasible |
| 10M (~7k legs) | ~2.8 h | feasible overnight incl. CPU PPO updates |
| 50M (~35k legs) | ~14 h | feasible as a weekend run IF learning slope is proven at 10M |
| 1B / 11B (PTCG scale) | 12–140 days | NOT feasible; explicitly rejected for V32 |

PPO update cost on CPU (1M-param MLP, minibatch updates per rollout) adds an
estimated 20–50% on top of rollout wall — it does not change the verdict.

## 3. Imitation-data throughput (measured, EXP-2 capture)

Serial capture (env + `v32enc` encode + JSONL): **92 pairs/s** → 1M pairs in
~3 h serial, ~20 min on 10 workers. BC data is NOT a bottleneck.

## 4. Inference overhead (measured, single-thread)

| Policy | ms/agent-step | Added wall per leg |
| :--- | :--- | :--- |
| torch 1.16M MLP | 0.71 | +1.0 s (+8%) |
| torch 0.09M MLP | 0.17 | +0.25 s (+2%) |
| numpy 1M (unoptimized) | 37 | +54 s (rejected path) |

Inference is not the bottleneck; the environment is. No GPU is needed for
rollouts at the 1–10M feasibility scale.

## 5. Feasibility verdict

- §52(4) (throughput makes training impossible): NOT triggered at 1–10M scale
  with fast experts. No GPU needed to TEST the hypothesis.
- Binding constraints are elsewhere: (a) terminal-only reward over 720-step
  episodes = severe credit-assignment risk for PPO; (b) masked factorized
  policy + PPO loop + stability engineering is large vs the router fallback;
  (c) V22R1/AEC-class opponents excluded from training by cost (eval-only).
- Decision: proceed with Phase A (BC) seriously; gate Phase B (PPO) on BC
  reaching strong per-head DEV accuracy AND a positive 1M-step PPO slope;
  build the §35 router in parallel as the §52(7) lower-cost comparator.
  DO NOT commit to 50M+ before the 1M-slope check passes.
