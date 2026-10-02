# V32 P7 — COMPETITION SAFETY EXIT VERIFICATION

## 1. FROZEN DIGESTS: UNCHANGED (`assert_frozen` PASS)

`scripts/v32_common.py::assert_frozen()` passes after all P7 work: all 12
frozen paths (Slot A/B tarballs, V3 tarball, A7 standalone, backbone adapters,
interface/utils/config, wash adapter) + engine 1.32.7 verified.

## 2. BASELINE CHECKPOINTS: UNTOUCHED (READ-ONLY)

| Checkpoint | SHA256 (exit) | Status |
|:---|:---|:---|
| `results/v32_p4_arm1_balanced.npz` | `34587d45…7470` | matches P6 manifest |
| `results/v32_p5_arm2_early_weighting.npz` | `dc939b29…bed` | **manifest erratum** (P6 recorded `8bfb219e…`; file is P5-era mtime/meta and behavior-verified: order-sensitive probe 240/240 wash, 0/240 S2 — content authentic, bytes never modified in P7) |
| `results/v32_p6_arm2_rebalanced.npz` | `355b9975…17af` | P7 entry hash (no prior manifest value; behavior reproduces P6 exactly) |

No baseline checkpoint was written by any P7 command (mtimes predate P7).

## 3. NEW ARTIFACT REGISTRY (P7 WRITES ONLY)

| Artifact | SHA256 / note |
|:---|:---|
| `results/v32_p7_prefix4.npz` | `89d80a6a…49a` (Arm 1, epoch 4, λ4=10) |
| `results/v32_p7_prefix4.npz.curve.json` | training curve |
| `results/v32_p7_prefixes.json` | prefix dataset (train legs only) |
| `results/v32_p7_eval_arm0.jsonl` / `*_arm1.jsonl` | 120-leg screens |
| `results/v32_p7_trace_arm0.json` / `*_arm1.json` | paired 24-step traces |
| `results/v32_p7_counterfactual_arm1.json` | A/B/C counterfactual |
| `v32/p7/*.py`, `scripts/v32_p7_*.py`, `tests/test_v32_p7.py` | new code/tests |
| `V32_P7_*.md` (16 files) | phase docs (Prefix8/12/24 docs NOT created — arms not run per §42) |

Frozen modules untouched: `v32/p2/*` (mtimes 2026-09-22), `v32/p3/*`
(mtimes 2026-09-23 03:xx), `v32/p6/*` (2026-09-23 09:14) all predate the P7
session (first P7 file 10:22); P7 added files only under `v32/p7/`. (Note:
`v32/` is untracked relative to git HEAD `d818fb1` (V29-era), so git cannot
attest these paths; integrity rests on mtimes + `assert_frozen` + exact P6
behavioral reproduction through the v32/p3+v32/p6 path.) Simulator and
submission packages untouched.

## 4. HOLDOUT VIRGINITY: VERIFIED

Seeds appearing in any `results/v32_p7_*` artifact: 249635–249649 (recorded
demonstration legs incl. BC-val, legitimate training data) and 249675–249684
(development screen) only. Refused ranges (214200–214249, 340000–340349 incl.
340090–340199) and V32-CONFIRM (249695–249734): ZERO touches. Every P7
evaluation/train entry point calls `check_seed_allowed`; the counterfactual
and Mode-B probes use dev/train seeds exclusively.

## 5. LEAKAGE AUDIT: CLEAN

- No `_TRACE`, `routes[`, step-indexed action returns, seed-specific rules,
  future/teacher-state access in `v32/p7/` (pattern audit + AST tests).
- No new per-step loss spikes (no s3/s4/lambda_s3/lambda_s4 mass anywhere).
- Phase detector: AST-verified free of step/teacher/seed/future references.
- Teacher executions occur ONLY as (a) separate-episode metric references,
  (b) the explicitly permitted §33 counterfactual intervention, (c) Mode-B
  probes on train seeds. No teacher output ever enters policy inputs.
- Prefix labels are recorded demonstrations only; rollouts are free-running
  simulator execution with honest predictor recurrence.

## 6. TEST STATUS

`tests/test_v32_p7.py`: 13/13 pass (incl. truncated==env.run equivalence on
both seats). Prior suites re-run in-session, all pass: P6 + semantic mask +
P4 + P3-codec + P3-models + freeze + protocol (53/53), P5 + P2 + harness
(28/28). Total 94/94. (`test_v32_router.py` not re-run: router path untouched
by P7 — no imports, no shared files.) PPO/RL entry points never invoked. No
submission packaging performed.
