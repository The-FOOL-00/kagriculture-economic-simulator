# V32 EXP-3 — RL FEASIBILITY (executed 2026-09-22, analysis + micro-bench)

No PPO run was launched: EXP-3's question is whether one is *worth* launching
on CPU-only hardware. Answer: YES at 1–10M scale, with three binding
constraints. Evidence:

## 1. Throughput (measured)

- Fast-expert legs: ~13.3 s → ~108 agent-steps/s/worker, ~1000/s on 10 workers.
- 1M agent-steps ≈ 17 min; 10M ≈ 2.8 h (+20–50% CPU PPO-update overhead).
- 50M ≈ 14 h — allowed ONLY after a positive 1M-step slope check.
- 1B/11B: 12–140 days — rejected, as the brief anticipated.
- BC data: 92 pairs/s serial (~20 min per 1M pairs on 10 workers). Not a
  bottleneck. (Full table: `V32_COMPUTE_FEASIBILITY.md`.)

## 2. Inference overhead (measured, single-thread)

torch 1.16M MLP: 0.71 ms/agent-step (+8% leg wall). torch 0.09M: 0.17 ms
(+2%). The environment dominates; no GPU needed for 1–10M feasibility.

## 3. The three binding constraints (all non-throughput)

1. **Opponent cost**: V22R1/AEC-class legs cost ~160 s (12×). A training
   mixture containing them collapses to ~90 agent-steps/s. V22R1 is
   eval-only for all V32 training (champion suite + promotion tests).
2. **Credit assignment**: terminal-only reward over 720-step episodes with a
   factorized (farmer + hands + market) action space. PPO must climb from a
   BC init; from-scratch PPO is not attempted (§9 of the brief).
3. **Engineering lift**: masked factorized sampler + PPO loop + CPU-stable
   updates + entropy/collapse monitors (§24) vs the §35 router (≤9-class
   output, legal by construction, supervised labels from the exact sim).

## 4. Missing infrastructure (honest)

No PPO implementation exists in the repo (no stable-baselines3; torch lives
in system python, the env in `.venv`). The 1M-step slope check requires
either a minimal masked-PPO implementation (~300 lines + tests) or a `.venv`
torch install. Neither was built: building it is Phase B work, gated on
Phase A (BC) reaching strong per-head DEV accuracy first.

## 5. EXP-3 verdict

RL IS TESTABLE (not blocked by compute), but NOT YET JUSTIFIED. Gate: (a) BC
up the ladder to DEV-evaluated W/L/T vs PASS/V3; (b) router baseline at ≥40
TRAIN seeds; (c) only then a 1M-step PPO slope check. If (a) succeeds and (c)
shows no slope after two HP settings → OUTCOME B; if the router matches BC+PPO
at far lower cost → OUTCOME C per §52(7). No 50M+ run without the slope.
