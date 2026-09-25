# V32 P7 — CLOSED-LOOP EVALUATION (120-LEG SCREEN, BOTH ARMS)

## 1. PROTOCOL

Identical P6 screen: seeds 249675–249684 × 6 opponents
(E0_V3, E1_V22R1, E2_A7, E3_V25P3, E6_W72, E7_W2015) × 2 seats = 120 legs,
deterministic, semantic mask on. First-divergence reference: live E2_A7 replay
in the learner seat (justified: all teachers share the identical 0–24 farmer
prefix). Results: `results/v32_p7_eval_arm0.jsonl`, `results/v32_p7_eval_arm1.jsonl`.

## 2. HEADLINE TABLE

| Metric | Arm 0 (P6 repro) | Arm 1 (Prefix-4) |
|:---|:---:|:---:|
| Wash shape / order | 100% / 0% | 100% / 0% |
| PASS / NORTH / hires / SOUTH | 100/100/5.00/100 | same |
| Step-3 action | SOUTH 120/120 | PICKUP COW 120/120 |
| Step-3 PICKUP SHEEP | 0% | 0% |
| pem4 / pem8 (farmer) | 0% / 0% | 0% / 0% |
| Macro survival | 0/120 | 0/120 |
| t_act / t_state / t_pos / t_econ | 3/1/4/1 | 3/1/5/1 |
| State-dist @8 | 0.242 | 0.211 |
| Cash mean / median / std / max | $0.07/$0.00/$0.82/$9 | $1.14/$0.00/$5.40/$29 |
| Wins | 0/120 | 0/120 |
| Worst 5% / 1% | $0.00 / $0.00 | $0.00 / $0.00 |

Cash by opponent (Arm 1 mean): E0_V3 ≈ E1_V22R1 ≈ E3_V25P3 ≈ E6_W72 ≈ $0–2;
all opponents 0 wins. No opponent-conditional recovery.

## 3. FIRST-24 TRACES

- Arm 0: `results/v32_p7_trace_arm0.json` (teacher $59,603 / policy $0).
- Arm 1: `results/v32_p7_trace_arm1.json` (teacher $59,603 / policy $29).
- Tables in §31 format printed by `scripts/v32_p7_trace24.py` (step, teacher
  action, policy action, positions, cash, phases, match flags).

## 4. VERDICT

Closed-loop behavior improved on every CONTINUOUS metric (cash bleed, state
distance, t_pos, phase progression) and on NONE of the BINARY macro metrics
(pem, survival, wins, median cash). The capital trap still closes on all 120
legs in both arms: hired hands draw wages from step 2 while no livestock →
pasture → revenue chain ever completes.
