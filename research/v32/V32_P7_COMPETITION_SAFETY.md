# V32 P7 — COMPETITION SAFETY & ENTRY PROTOCOL

## 1. FROZEN PRODUCTION ARTIFACTS (ENTRY HASHES)

Entry verification runs `scripts/v32_common.py::assert_frozen` before any P7
evaluation or training. Expected digests (V32_BASELINE_FREEZE):

| Asset | Path | SHA256 (prefix asserted in full by harness) |
|:---|:---|:---|
| Production Slot A | `submission_aec_v22r1.tar.gz` | `6b879b3e…` |
| Production Slot B | `submission_a7_v30.tar.gz` | verified via P6 manifest chain |
| Benchmark V3 | `submission_Vj_kc_v3.tar.gz` | `845e0d10…` |
| A7 standalone | `candidates/v30_a7_standalone/main.py` | `51c1d252…` |
| P4 checkpoint | `results/v32_p4_arm1_balanced.npz` | `34587d45…` |
| P5 checkpoint | `results/v32_p5_arm2_early_weighting.npz` | `8bfb219e…` |
| P6 checkpoint | `results/v32_p6_arm2_rebalanced.npz` | hashed at Arm 0 repro |

P7 writes only new files (`results/v32_p7_*`, `V32_P7_*`, `v32/p7/*`,
`scripts/v32_p7_*`, `tests/test_v32_p7.py`). No overwrite of prior checkpoints,
no simulator modification, no submission packaging.

## 2. SEED GOVERNANCE

- Allowed: V32 TRAIN 249635–249674 (demonstration rows), V32 DEV screen
  249675–249684 (closed-loop), BC-val 249647–249649 (early stopping only).
- Refused (harness-enforced by `check_seed_allowed`): 214200–214249, 340000–340349,
  340090–340199, V32-CONFIRM 249695–249734 (single-touch, needs explicit flag that
  P7 never passes), anything below 249635 or above 249734.
- `scripts/v32_p7_eval_screen.py` calls `assert_frozen()` + `check_seed_allowed()`
  on every seed before execution, mirroring the P6 harness.

## 3. LEAKAGE RESTRICTIONS (P7-SPECIFIC)

Forbidden in model, mask, phase, loss, and eval code:

- route lookup / `routes[route][step]` replay / copied A7 route tape
- timestep → action or timestep → phase mappings (`if step == N: return X`)
- teacher trajectory injection into inference inputs
- hidden action arrays / `_TRACE` / action-tape splicing in rollout
- seed-specific rules or seed-ID features
- future-state access (using teacher s_{t+k} as input at step t)
- teacher-state overwrite during policy rollout
- step-indexed action overrides of any kind

Permitted:

- training trajectories as supervised labels (recorded rows only)
- trajectory-prefix window losses (uniform within window)
- state-derived phase features (deterministic function of current `ess`)
- current temporal features (online builder, same code path as P2/P3)
- simulator-generated rollout states under free-running execution

## 4. ARCHITECTURE & SEMANTICS FREEZE

- `v32/p2/features.py`, `v32/p3/codec.py`, `v32/p3/models.py::P3Policy`,
  `v32/p6/mask.py`, and the kaggriculture simulator are read-only in P7.
- New code lives in `v32/p7/` (prefix/metrics/state-distance/phase) and
  `scripts/v32_p7_*` (train/eval/diagnostics). No edits to frozen modules.
- PPO/RL entry points are not invoked; `v32/p2/ppo.py` stays untouched.

## 5. EXIT CRITERIA

`V32_P7_COMPETITION_SAFETY_EXIT.md` must verify: frozen digests unchanged,
holdout virginity (no refused-seed execution in any P7 result file), no simulator
diff, new-checkpoint registry with hashes, and full prior-suite pass status.
