# V32 P2 EVALUATION (BC replay; no PPO to evaluate)

## 1. Mixture-BC vs 6-opponent panel (SCREEN 249650–249672, both seats)

276 legs (`results/v32_p2_eval_bc.jsonl`). Seat-0 paired vs R1 b1 rows
(n=138): BC−A7 mean −$101,315, median −$96,734; W-L-T 0-138-0; uniform
across opponents (worst −$102,685 vs V25P3, best −$98,935 vs DMITRII).
Mean policy entropy 14.2 (confident, wrong).

## 2. A7-BC replay screen (4 seeds × 4 opponents, seat 0)

16 legs (`results/v32_p2_eval_bc_a7.jsonl`): $0–39 every leg, mean
−$109,161 vs A7. Mechanism identical (wash missed → drift → qty-0).

## 3. PPO eval: NOT APPLICABLE (no PPO run; Tier-1/2 screens, oracle-regret
tracking, and V22R1 confirmation protocol preserved in `V32_P2_PPO_SPEC.md`
for the follow-up phase).
