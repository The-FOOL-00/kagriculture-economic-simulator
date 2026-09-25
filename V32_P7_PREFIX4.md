# V32 P7 — ARM 1 PREFIX-4 (UNIFORM TRAJECTORY-PREFIX SUPERVISION)

## 1. OBJECTIVE (PREREG §6 + DOCUMENTED ADDITIVE CHOICE)

```text
L = L_unit + L_mkt + 50·L_crit_s0 + 10·L_early_1_10 + 50·L_s2_farmer + 10·L_prefix(4)
```

`L_prefix(4)` = ROW-uniform mean action loss over steps 0–4 (`v32/p7/loss.py`:
every qualifying timestep contributes exactly 1/N_window; verified in
`tests/test_v32_p7.py::test_04`). No per-step spikes, no λ_s3/λ_s4, no schedule.

Additive-design note (deviation from the §10 sketch, preregistered in
`V32_P7_PREREG.md` §6 and here): the P6 base terms are RETAINED and the run
warm-starts from P6 Arm 2, so the H1 test is the MARGINAL effect of the uniform
prefix term without a forgetting confound. A pure (dropped-base) variant would
unlearn the spike-dependent opening and answer nothing about prefix supervision.

Hyperparameters: 10 epochs, Adam lr 3e-4, batch 128, grad-clip 1.0, seed 42.
Selection: opening gates (hard) + teacher-forced prefix-exact + S3/S4 accuracy +
Mode-B consistency on fixed TRAIN seeds 249635/249636 (never dev, never
holdouts). Checkpoint: `results/v32_p7_prefix4.npz` (best epoch 4).

## 2. TRAINING RESULT (TEACHER-FORCED)

| Epoch | val_full | S0 wash | S1 N/hire | S2 S | pem4 | S3 | S4 | ModeB t/d |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1–10 | 0.062–0.069 | 0/240 | 240/240 | 240/240 | 0/192 | 0.00 | 0→1 | 3 / 0.08–0.10 |

- Opening preserved (no forgetting). Wash order unmoved (0/240).
- Step 4 learned (PICKUP WHEAT 1.00); step 3 NEVER learned (0.00 all epochs);
  prefix-exact 0/192; Mode-B divergence stuck at step 3.
- Mechanism (`V32_P7_PREFIX_DIAGNOSTICS.md`): at step 3 the prefix gradient
  raised PICKUP (+0.61) but NORTH rode along (+0.65) — ranking gap −0.53 →
  −0.57, unchanged. Step 4 flipped only because its margin was −0.05.

## 3. CLOSED-LOOP RESULT (120-LEG SCREEN, `results/v32_p7_eval_arm1.jsonl`)

| Metric | Arm 0 (P6) | Arm 1 (Prefix-4) |
|:---|:---:|:---:|
| Step-0 wash shape / order | 100% / 0% | 100% / 0% |
| Step-0 wash qty (closed loop) | SELL-30/BUY-30 | **SELL-7/BUY-2 (W72-style)** |
| Step-1 cash vs teacher | $2,040 (−$1,014) | **$2,936 (−$118)** |
| Step-0 PASS / S1 NORTH / hires / S2 SOUTH | 100% / 100% / 5.00 / 100% | same |
| Step-3 farmer op | SOUTH 120/120 | **PICKUP COW 120/120** (right op, wrong arg) |
| Step-3 PICKUP SHEEP | 0% | 0% |
| Prefix-exact P4/P8 (farmer) | 0% / 0% | 0% / 0% |
| Opening-macro survival | 0/120 | 0/120 (all fail `pickup_sheep@3`) |
| t_act / t_state / t_pos / t_econ (median) | 3 / 1 / 4 / 1 | 3 / 1 / **5** / 1 |
| State distance @ step 8 (mean) | 0.242 | **0.211** (lower at every step 0–8) |
| Terminal cash mean / median | $0.07 / $0.00 | $1.14 / $0.00 |
| Wins | 0/120 | 0/120 |

## 4. INTERPRETATION

Prefix-4 supervision produced MEASURABLE but NON-COMPOUNDING gains:

1. Wash bleed −89% (qty compromise toward the smallest-qty teacher; order still
   flipped — the uniform window rebalances quantities but cannot fix rank order).
2. Step-3 op corrected (SOUTH → PICKUP), but the ARG is wrong (COW ≠ SHEEP):
   the arg head says SHEEP on train states (192/192) and COW in closed loop —
   a closed-loop/train mismatch no teacher-forced window can supervise.
3. t_pos +1 (PICKUP doesn't move, so positions stay synced one step longer),
   state trajectory uniformly closer, policy reaches ECONOMIC_CONTINUATION and
   builds/places (wrong tile, no-op PLACEs).
4. The macro still breaks at step 3 (pem 0%, t_act 3, macro 0/120) and economics
   stay in the flat-zero regime ($1.14 mean, $0.00 median, 0 wins).

## 5. EXPANSION DECISION: NO PREFIX-8/12/24 (PREREG §9 + §42 STOP RULE)

Prefix-8 is NOT run. Justification (all three must hold to expand; none does):

1. **No material prefix-stability gain**: pem4 0→0, t_act 3→3, macro 0→0. The
   t_pos 4→5 shift is the horizon-shift signature in miniature, not stability.
2. **No mechanism by which a longer window helps**: the residual failures are
   (a) closed-loop arg flip under state shift (same-phase, §6), (b)
   trunk-coupled op ranking at step 3, (c) wash ORDER. A 0–8 uniform window
   gives step 3 LESS per-step signal (λ/9 vs λ/5) and adds unreachable-step
   labels (5–8 are never visited on-manifold). Longer supervision cannot create
   the missing (closed-loop-state → correct-action) labels.
3. **Chasing would repeat the banned pattern**: training Prefix-8 after this
   result would BE §27's forbidden "repeat the same failure mechanism with more
   weight."

Per §42, the correct horizon finding is: NO uniform teacher-forced horizon
stabilizes the macro — the binding constraint is supervision type (closed-loop
labels), not horizon length. PREFIX8/12/24 artifacts are therefore not created.
