# V32 P7 — PHASE ABLATION (H2 GATE: REJECTED WITHOUT TRAINING)

## 1. ABLATION STATUS

- **A (P6 baseline)**: measured — §CLOSED_LOOP Arm 0.
- **B (prefix only)**: measured — §CLOSED_LOOP Arm 1.
- **C (prefix + phase conditioning)**: NOT TRAINED — H2 rejected at the gate
  (prereg §8; `V32_P7_PHASE_DEFINITION.md` §5 criterion b). This document records
  the rejection evidence. No phase-embedding checkpoint exists; no architecture
  change was made.

## 2. DISCRIMINATIVE CHECK (PASSES — NECESSARY BUT NOT SUFFICIENT)

The state-derived detector (`v32/p7/phase.py`, no step/teacher/seed/future
inputs) DOES separate nominal from failed trajectories in closed loop:

- Teacher 0–24: OPENING×2 → LIVESTOCK×2 → PRODUCTION → ECONOMIC (step 5+),
  identical 240/240 recorded seats.
- Arm 0 policy: stalls in LIVESTOCK_SETUP through step 6, PRODUCTION_SETUP
  after (never stocks on time).
- Arm 1 policy: LIVESTOCK_SETUP through step 6, PRODUCTION_SETUP, ECONOMIC
  only at step 16+ (too late).

So phase context "knows" the policy is off-macro. H2's hope was that FEEDING
that knowledge back would stabilize decisions.

## 3. REJECTION PROOF: SAME-PHASE CONFUSION (SUFFICIENT TO REJECT)

The binding step-3 error is PROVABLY unfixable by phase conditioning:

- Train step-3 state (arg head → SHEEP, correct): phase = LIVESTOCK_SETUP.
- Closed-loop step-3 state (arg head → COW, wrong): phase = LIVESTOCK_SETUP
  (Arm 0 and Arm 1 traces, all legs: 5 hands + shed livestock + no
  hand-built structures yet at step-3 pre-action).
- A phase embedding contributes IDENTICAL input in both states (same phase →
  same embedding). It therefore CANNOT change the arg decision between them;
  the flip is driven by other features (cash, shed counts, action history)
  that phase coarsens AWAY.

More generally: phase is a deterministic function of EXISTING features
(hands/shed/inv/thist) — it adds zero information the MLP cannot already
extract, and the diagnosed failures (closed-loop arg flip under shift,
trunk-coupled op ranking, wash order) are supervision failures (missing
closed-loop labels), not feature failures. No input transformation creates
labels that do not exist in the demonstration set.

## 4. WHY TRAINING C WAS NOT RUN ANYWAY

"Just try it" would cost a training run + 120-leg screen to test a hypothesis
with a proof of incapability against the binding error and no mechanism for
the others. The preregistered gate exists precisely to prevent
compute-without-hypothesis. The honest ablation conclusion is B > A on
continuous fidelity, B = A on macro stability, and C incapable by construction
of addressing the residual.

## 5. WHAT WOULD REOPEN H2

A future phase variable that is NOT a function of current observable features
(e.g. a learned execution-context belief carried across steps) is no longer
"H2 phase conditioning" — it is sequence memory (the P7-D direction). That
renaming matters: it concedes that instantaneous state is insufficient.
