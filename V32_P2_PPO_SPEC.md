# V32 P2 PPO SPEC (preregistered 1M slope configuration)

Driver: `scripts/v32_p2_ppo.py`. Core: `v32/p2/ppo.py` + `v32/p2/rollout.py`.
One primary run + one tiny smoke test. No sweep.

STATUS: NEVER EXECUTED — P2 stopped at the §29 BC gate (see
`V32_P2_DECISION_REPORT.md`). Only the smoke test ran (random init, 2
episodes, 1 update: loop + parity validated, no scientific signal).
Preserved verbatim for the follow-up phase.

## 1. Initialization

BC checkpoint `results/v32_p2_bc.npz` (architecture-aligned, CASE B).
All weights loaded EXCEPT the critic head (fresh random — BC fits no
value target). Critic trains jointly from iteration 0 (vf_coef 0.5).

## 2. PPO hyperparameters (fixed)

| Param | Value | Source |
| :--- | :--- | :--- |
| Total learner steps | ~1,000,000 | brief §38 |
| Episodes/iter | 24 (~17k steps) | throughput-balanced |
| γ / λ | 1.0 / 0.95 | V32_TRAINING_SPEC |
| Clip ε | 0.2 | stable default |
| LR (Adam) | 3e-4 | stable default |
| Epochs / minibatch | 4 / 2048 steps | stable default |
| Grad clip | 0.5 | stable default |
| vf_coef / ent_coef | 0.5 / 0.01 | stable default + guard |
| Reward | terminal money/1e5, else 0 | R-A, brief §37 |
| Entropy guard | halt-and-diagnose if mean rollout entropy exits [0.5×, 2×] of BC-init rollout entropy for 3 consecutive iters | V32 spec |

## 3. Schedule (deterministic round-robin, no RNGNeeded for coverage)

- Opponents: uniform round-robin over {V3, A7, V25P3, W72, W2015, DMITRII}.
- Seeds: round-robin over P2-TRAIN 249635–249649.
- Seats: alternate 0/1. Action sampling seeded per (run seed, episode idx).
- Smoke test: 2 episodes + 1 update on P2-TRAIN seeds (validates the loop
  + parity tripwire before the 1M launch).

## 4. Checkpoints and eval

Save at {0, 100k, 250k, 500k, 750k, 1M} learner steps + registry hashes.
Tier-1 screen per checkpoint: 6 opponents × P2-SCREEN seeds (both seats
for init/final; seat-0 for intermediates — cost control, preregistered).
Tier-2 (V22R1): seeds {249650, 249660, 249670} × {init, mid, final} only.
