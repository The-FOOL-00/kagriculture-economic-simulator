# V32 P3 BC TRAINING REPORT (mixture + A7 follow-up)

Runner: `scripts/v32_p3_bc_train.py` (Adam 3e-4, batch 1024, ≤30 epochs,
early-stop patience 5 on val full-exact — never triggered; both runs used all
30). Loss = sum of 6 masked-CE head means. Params: 277,092 (vs P2 a1 545,705).

## 1. Mixture BC (4 teachers, 138,048 train / 34,512 val steps)

Checkpoint: `results/v32_p3_bc.npz`. Report: `results/v32_p3_bc_report.json`.
Wall: 672 s CPU (vs P2 mixture 3,184 s — 4.7× faster; no candidate encoder).

| Split | full-exact | full-sem | farmer | u_op | u_arg | u_qty | m_op | m_item | m_qty | m_op-nn |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 0.047 | 0.047 | 0.478 | 0.476 | 0.940 | 0.833 | 0.974 | 0.772 | 0.803 | 0.824 |
| val | 0.046 | 0.046 | 0.468 | 0.470 | 0.925 | 0.804 | 0.969 | 0.744 | 0.759 | 0.801 |

No overfit (train≈val on every head). All curves still rising at ep29.

### vs P2 mixture-BC (val)

| Metric | P2 pointer | P3 native | Δ |
| :--- | ---: | ---: | :--- |
| full-exact | 0.022 | 0.046 | 2.1× |
| farmer | 0.438 | 0.468 | +0.03 |
| market | 0.897 | 0.969 | +0.07 |
| **mkt-nonnoop** | **0.300** | **0.801** | **+0.50** |

The market-side repair dominates: non-NOOP market-op accuracy 0.30→0.80.
Unit side modestly better (+0.03 farmer). The joint full-exact doubles but
stays low in absolute terms (joint over ~25 slots is harsh; cf. G2
recalibration — P2 never measured full-joint).

## 2. Step-0 wash under mixture BC (G3 ckpt-eval — FAILS on order)

Argmax on all 240 step-0 samples: wash-shape 0/240. The model emits a
REVERSED wash `[SELL,WHEAT,30],[BUY_PRODUCT,WHEAT,30]` (A7's qty, swapped
slots) on all 240 identical inputs. With an empty step-0 shed the M0 SELL is
void; the M1 BUY fills the shed at post-opponent-buy inflated prices — no
wash economics (see `V32_P3_STEP0_WASH_REPORT.md` §4 + first-divergence).

Diagnosis: M0 is globally SELL so the shared head predicts the global slot
mode; 180 step-0 train samples (0.13%) with 4 conflicting qty-labels cannot
override it in 30 epochs. Representation suffices (dedicated step-0 probe
learns the wash); mixture supervision + rare-sample dynamics are the blocker.

## 3. A7-only BC follow-up (ONE controlled follow-up, P2 precedent) — FAILED worse

Config identical except `--teachers E2_A7` (34,512 train / 8,640 val).
Checkpoint: `results/v32_p3_bc_a7.npz` (early-stopped ~ep10, wall 207 s).

Val: full 0.006, farmer 0.195, u_op 0.236, m_op 0.892, m_op-nn 0.080,
m_item 0.487, m_qty 0.435. Step-0 argmax: all-NOOP 240/240 (complete wash miss).

Single-teacher is WORSE on every head (1/4 the data AND 1/4 the gradient steps
at fixed 30 epochs → underfit). P2's A7-BC showed the same pattern (0.369 vs
0.438 farmer). Conclusion: mixture conflict is NOT the binding constraint;
total optimization is. NO PIVOT (prereg §5 condition "single-teacher passes"
not met). Mixture stays primary.

## 4. P3-AMEND-1: LR 3e-3 mixture BC (documented Repair-C branch)

Justification (evidence-backed, not a sweep): the step-0 probe fits the wash
in 75 epochs at LR 3e-3 vs 475 at 3e-4 (6× rate gap); mixture BC at 3e-4 learns
A7's wash qty but not its slot order in 30 epochs; step-0 supervision (180
samples, unanimous order) is signal-starved at 3e-4. One LR value (P2's own
probe LR), same 30-epoch budget, same data: `results/v32_p3_bc_lr3e3.npz`.
Resampling/reweighting stays forbidden (§5).

Result: better everywhere — val full 0.071, farmer 0.535, u_op 0.499,
m_op 0.983, m_op-nn 0.902, m_item 0.754, m_qty 0.759 (wall 705 s, all 30
epochs, no overfit: train full 0.071). BUT step-0 wash still 0/240 with the
SAME reversed `[SELL30,BUY30]` prediction. Probability probe: slot-0
P(BUY_PRODUCT)=0.187 vs P(SELL)=0.813 (3e-4 ckpt: 0.234/0.763) — higher LR dug
the wrong optimum DEEPER. The 180 step-0 samples (0.13%, unanimous order)
cannot override the global M0≈SELL mode in 30 epochs at either LR: stable
wrong equilibrium, not slow convergence. AMEND-1 improves fidelity but does
NOT fix the wash. Closed-loop for this arm decides between continued training
and STOP F3 (see closed-loop report §3).
