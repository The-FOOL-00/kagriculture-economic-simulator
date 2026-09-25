# V32 R1 TRAINING REPORT (2026-09-22)

Runner: `scripts/v32_router_train.py` (system python3, torch 2.13.0+cpu,
CPU-only, 12 cores). Registry: `results/v32_r1_runs.json` (16 runs, 41 s)
+ `results/v32_r1_runs_oh.json` (16 runs, 36 s, opponent-holdout).
Git HEAD `d818fb1` (working tree: untracked V32-R1 files only; no tracked
file modified except the additive test/allowlist note below).
Dataset hash `5e5eb020…efa9ac`, TRAIN 60 rows / VAL 30 rows per label mode.

## 1. Configs and VAL soft-CE (primary run)

| Config | Regime/stack/mode/model | Params | VAL soft-CE | Epochs |
| :--- | :--- | ---: | ---: | ---: |
| M2_logistic_aid | A+ID / — / b1 / logistic | 40 | 1.4367 | 2000 |
| M3_small_b1 | B / longer / b1 / small | 21,061 | 1.4181 | 359 |
| M3_small_b1_s1 | B / longer / b1 / small | 21,061 | 1.3774 | 245 |
| M3_stack_none_b1 | B / none / b1 / small | 9,541 | 1.4142 | 384 |
| M3_stack_short_b1 | B / short / b1 / small | 15,301 | 1.3973 | 250 |
| M3_shuffled_b1 | B / longer / b1 / small, shuffled | 21,061 | 1.3841 | 266 |
| M4/M5/M6 b2 family (8 cfgs) | B / */ b2 / small/med | 9,541–48,133 | 1.6094 = ln 5 | 536–895 |
| M4_hard (b2, hard CE) | B / longer / b2 / small | 21,061 | 0.3851 | 1042 |
| M4_prefC (b2, TARGET C) | B / longer / b2 / small | 21,061 | 1.6094 | 542 |

Optimizer: full-batch Adam, lr=1e-3, wd=1e-2, VAL early-stop patience 200
(max 2000 epochs). Deterministic (seeded, fixed order); retrain-identical
checkpoints verified by `test_train_loop_reproducible`.

## 2. OBSERVED FACTS

T1. All b2 soft-CE = ln 5 exactly (uniform). Cause: all 282 b2 rows flat
within $500 (max spread $45) — the $500 admissible set covers all 5
classes, targets are uniform, optimum is uniform. B2 is vacuous (see §4).
T2. M4_hard (b2) VAL 0.3851 "learns" the arbitrary hard argmax of flat
rows — memorized noise, reported as a control for why hard-CE was
rejected as primary (preregistered TARGET A soft formulation vindicated).
T3. b1 VAL-CE spans 1.377–1.437 across real/shuffled/stack variants —
within noise on 30 VAL rows. Shuffled (1.3841) sits INSIDE the real-model
range: VAL-CE is non-discriminative. Selection deferred to TEST economics
(preregistered success = economic regret, not CE/accuracy).
T4. Stack width has no VAL effect (none 1.4142 / short 1.3973 / longer
1.4181–1.3774 across seeds): seed noise exceeds stack effect.
T5. Opp-holdout run reproduces the same nullscape (b1 VAL 1.33–1.55,
b2 = ln 5).

## 3. INTERPRETATION

Training behaved exactly as a no-signal problem should: heavy
regularization + early stopping collapse every b1 model toward the
marginal (all four M3 variants pick identically on TEST), and b2 models
toward uniform. VAL-CE cannot select among null models; the TEST economic
evaluation (`V32_R1_EVALUATION.md`) is the decision record.

## 4. B2 vacuity proof (structural, not a training failure)

`V31R2WashAdapter` defaults `split_cap=None` and A7 sets `dispatch=False`,
so E2_A7/E6_W72/E7_W2015 are behaviorally identical to E0_V3 from step 1
onward (all step-0 logic keys off `obs['step']`); only E3_V25P3 differs
post-0 (P3 dispatch, crumbs). A step-24 handoff therefore cannot change
play: measured max spread $45 over 282 b2 rows. The router decision IS the
step-0 wash decision. B2-LOCKED legs skipped per prereg Addendum A1.
