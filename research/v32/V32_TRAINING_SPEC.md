# V32 TRAINING SPEC (v1, 2026-09-22)

## 1. Pipeline (matches §8 of the brief; CPU-conditioned)

- **Phase A — imitation init**: behavior cloning on TRAIN expert trajectories
  (teachers: E0/E1/E2/E3/E7). Small sweep FIRST: linear probe → 0.1M MLP →
  1M MLP. Transformer only if MLPs show a capacity bottleneck on DEV loss.
- **Phase B — self-play/RL**: PPO micro-feasibility (see V32_EXP3) before any
  10M+ run. Opponent mixture per §16 (expert/learner/champion mix).
- **Phase C — champion promotion**: per `V32_PROMOTION_PROTOCOL.md` (frozen).
- **Phase D — adversarial specialization**: only after a promoted generalist
  exists. Single targeted cycle first (strongest counter-family), then decide.

## 2. Model ladder (smallest-first, §2/§12)

| Rung | Params | Arch | When |
| :--- | :--- | :--- | :--- |
| R0 | ~10k | linear probe on `v32enc-v1` | sanity: is there ANY linear signal? |
| R1 | ~0.1M | 2-layer MLP | BC baseline; router backbone |
| R2 | ~1M | 3-layer MLP + heads | first serious BC/PPO candidate |
| R3 | ~5M | wide MLP / tiny Transformer | only if R2 underfits DEV |
| R4+ | 10–20M | hybrid Transformer | only with promotion-grade evidence at R3 |

No rung is skipped upward without a measured bottleneck at the rung below.

## 3. Data discipline

- TRAIN (249635–249674) for all gradient updates; DEV (249675–249694) for
  every architecture/HP decision; CONFIRM (249695–249734) single-touch.
- Imitation batches record (expert_id, seed, step, phase); sampling follows
  `V32_SAMPLING_PROTOCOL.md` (family-balanced, loss-prioritized replay).
- Checkpoints store: weights, optimizer, scheduler, step, RNG state,
  population-manifest hash, config hash, encoder version. Never overwrite the
  best-DEV checkpoint. `test_v32_checkpoint` asserts save/restore bitwise
  reproducibility of eval decisions.

## 4. PPO defaults (feasibility scale; ablate, don't worship)

Masked factorized policy (§V32_ACTION_ENCODER_SPEC), value head on R-C,
γ=1.0 (episodic, terminal reward — no discounting of the objective),
λ=0.95, clip 0.2, entropy bonus tuned to keep per-family entropy within
[0.5×, 2×] of the BC init (collapse guard). Deterministic eval for all
benchmarks. If PPO is unstable twice under two HP settings → STOP per §52(2),
pivot to router.

## 5. Compute reality (CPU-only)

All run sizes derive from `V32_COMPUTE_FEASIBILITY.md` measurements, not from
the PTCG writeup's 11B-step scale. First RL feasibility target: 1M–10M
agent-steps. Scale-up requires a measured learning curve with positive slope
on DEV W/L/T — not on training loss.
