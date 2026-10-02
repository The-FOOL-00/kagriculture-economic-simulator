# V32 P2 PREREGISTRATION — 1M BC-init PPO slope test (DRAFT → FINAL before launch)

Status: SUPERSEDED -- P2 stopped at the section-29 BC gate; no PPO run was
launched, no PPO outcomes exist, and this prereg was never sealed.
Preserved as the starting draft for the follow-up phase (which must
re-derive section 9's BC reference from a competent init before sealing).

## 1. Primary metric

Δ_cash_PPO−BC(step) = terminal_cash(PPO@step) − terminal_cash(BC),
paired by (seed, opponent, seat) on the Tier-1 screen (P2-SCREEN seeds
249650–249672 + 249675–249683 × 6 panel opponents). Secondary:
Δ_cash_PPO−A7, oracle-regret fraction closed.

## 2. Primary baseline

Architecture-aligned BC checkpoint (init = ckpt 0). A7 is the
competition-relevant reference; BC is the RL-value reference.

## 3. Checkpoint schedule

{0, 100k, 250k, 500k, 750k, 1M} learner steps. Tier-1 every checkpoint;
Tier-2 (V22R1, seeds 249650/249660/249670) at {0, 500k, 1M} only.

## 4. Expected slope (directional, not a promise)

100k: −$1.5k..−$0.3k (critic burn-in, BC disruption possible)
250k: −$1.0k..+$0.3k
500k: −$0.5k..+$0.8k
1M: −$0.3k..+$1.5k vs BC.
Minimum directional evidence: monotone-ish rise over the LAST THREE
checkpoints with final > BC on paired cash (see G2).

## 5. Tail/safety bounds

Tolerated: worst-5% within −$3k of BC's worst-5%; catastrophic count
(< BC same-pair cash − $25k) ≤ 2 per 100 legs; zero invalid actions
(by construction), zero simulator errors, zero quarantine touches.

## 6. Independence

G6 slice: P2-CONFIRM-research seeds 249692–249694 (3 virgin seeds) +
second training seed for the slope shape (only if slope passes on seed 0;
reproducibility before any scale-up talk).

## 7. SLOPE GATE (brief §44 G1–G7, verbatim criteria)

PASS requires ALL: directional trajectory (G1); final > BC paired (G2);
not one-seed/one-opp driven (G3); no catastrophic tail (G4); behavior
change after t≈258 window (G5); survives independent slice (G6); all
fidelity/masking/determinism/boundary checks pass (G7).

## 8. SCALE-UP REVIEW (brief §46 S1–S9, verbatim criteria)

**PASSING THE 1M SLOPE GATE DOES NOT AUTOMATICALLY AUTHORIZE 5–10M.**
Scale-up needs a separate review answering §62's 12 questions. P2 ends at
GATE 1; no promotion (GATE 3) under any P2 outcome.

## 9. BC reference (filled after §29 eval)

- BC-vs-A7 paired cash on SCREEN: TBD
- BC-init rollout entropy (guard band): TBD
- BC action accuracy / NLL: TBD (from `v32_p2_bc_report.json`)
