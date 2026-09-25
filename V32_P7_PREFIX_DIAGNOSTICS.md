# V32 P7 — PREFIX DIAGNOSTICS (MODE A LOGIT & CONFUSION ANALYSIS)

## 1. METHOD

Teacher-forced evaluation of the P6 Arm 2 checkpoint vs the P7 Prefix-4
checkpoint (epoch 4, λ4 = 10.0) on all 192 training step-3 and step-4 samples
(non-val legs). Raw model (no mask; at step-3/4 states PICKUP/NORTH/SOUTH are
all mask-legal, so masking cannot change the ranking discussed here).

## 2. STEP-3 RESULT: PREFERENCE ORDER UNMOVED (192/192 NORTH, BOTH CHECKPOINTS)

| Checkpoint | Predicted op (192) | Mean logit NORTH | Mean logit PICKUP | Gap |
|:---|:---:|:---:|:---:|:---:|
| P6 Arm 2 | NORTH 192/192 | +7.02 | +6.49 | −0.53 |
| P7 Prefix-4 | NORTH 192/192 | +7.67 | +7.10 | −0.57 |

The prefix gradient DID reach step 3 (PICKUP logit +0.61), but NORTH rose by
+0.65 through the shared trunk, so the ranking gap is unchanged (−0.53 →
−0.57). Uniform reweighting scales local confidence, not the learned preference
order. The arg head already predicts SHEEP 192/192 — the head knows WHAT to
pick up; the op head refuses to select PICKUP.

Note: teacher-forced prediction at step 3 is NORTH, while free-running closed
loop emits SOUTH (Arm 0, 120/120). The closed-loop step-3 state (wash-bleed
cash $468 vs train ~$1,106, stranded wheat) flips NORTH → SOUTH — further
evidence that the step-3 decision boundary is balanced on out-of-manifold
nuisance features rather than the macro context.

## 3. STEP-4 RESULT: RAZOR-THIN MARGIN FLIPPED (192/192 PICKUP)

| Checkpoint | Predicted op (192) | Mean logit PICKUP | Mean logit PLACE | Gap |
|:---|:---:|:---:|:---:|:---:|
| P6 Arm 2 | PLACE 192/192 | +5.92 | +5.97 | −0.05 |
| P7 Prefix-4 | PICKUP 192/192 | +6.45 | +6.38 | +0.07 |

Step 4 (target PICKUP WHEAT) flipped because the P6 margin was −0.05: the small
uniform prefix push (+0.53 PICKUP vs +0.41 PLACE) sufficed. Step 4 is
distinguishable by an observable feature (farmer carrying SHEEP), while step 3
requires acting on macro context (empty-handed at a full shed = load livestock).

## 4. MECHANISTIC INTERPRETATION

Mode-A prefix supervision acts as a **margin-dependent nudge**, not as sequence
coordination:

- Where the teacher-forced preference gap is tiny (step 4: −0.05), the uniform
  window flips the decision.
- Where the gap is structural and trunk-coupled (step 3: −0.53, NORTH riding
  with PICKUP), the same weight leaves the ranking untouched — the exact
  behavior the preregistered factorization argument predicts: under teacher
  forcing, the prefix gradient carries no cross-step dependency information, so
  it cannot teach the model WHY step 3 must be PICKUP (to enable steps 4–8).

This is the P4–P6 spike-scale story from the other side: P6 needed λ = 50 to
flip a single step; a uniform λ = 10 window flips only near-tied steps. No
uniform λ can both preserve steps 0–2 and flip step 3 without becoming the
forbidden per-step spike it was designed to replace.

## 5. CLOSED-LOOP CONSEQUENCE (PREDICTION → VERIFIED IN V32_P7_PREFIX4.md)

Because step 3 is unmoved, the free-running policy still diverges at step 3 and
never visits the step-4 teacher state — so the step-4 teacher-forced repair is
causally inert in closed loop. Prefix-4 exact-match stays 0% and economics stay
flat. The screen in `results/v32_p7_eval_arm1.jsonl` confirms this prediction.
