# EXP-DEV-005_KILLTEST FORENSIC CAUSAL AUDIT
## Mechanistic Investigation of Route Reversal, Sunk Capital, and Market Absorption Failures

**Experiment Identifier**: `EXP-DEV-005_KILLTEST`  
**Evaluation Scope**: The 16 Original DEV-004 Loss Seeds + 4 Positive Control Winning Seeds  
**Baseline**: `candidates/compiled_v54_plus_residual.py` (Submission `56146971`)  
**Intervention Tested**: `HYSTERESIS_COMMITMENT_GUARD` over `dev_004_joint_macro_scheduler.py`  
**Date**: 2026-09-14  
**Auditor**: Autonomous Verification Engine (Zero-Leakage Governance)

---

## 1. Operational Definition of Harmful Hysteresis

A route reversal event is classified as **Harmful Hysteresis** if and only if it satisfies all four operational criteria:
1. **Post-Commitment Timing**: It occurs *after* material, irreversible operational or capital commitments have been initiated for a specialized route.
2. **Asset Abandonment**: It abandons plan-specific physical assets (specialized animals, dedicated planting cadences, or tailored shed inventory).
3. **Identifiable Mismatch Cost**: It forces an incompatible policy (e.g., `BASELINE_BACKBONE`) to operate on an altered physical state (e.g., shearing paths executed on non-existent cows, or unharvested sheep).
4. **Avoidable Net Loss**: The resulting physical desynchronization directly causes a measurable, avoidable loss relative to counterfactual continuation.

### Negative Constraints
- A route reversal is **NOT** automatically harmful.
- A seed loss is **NOT** automatically hysteresis.
- A route change without prior sunk commitment is **NOT** hysteresis.
- A reversal followed by a superior or protective outcome is an **Adaptive Defensive Reversal**, not harmful hysteresis.

---

## 2. Taxonomy of the 16 Original DEV-004 Loss Seeds

Cross-referencing the raw event telemetry (`PLAN_EVENTS.csv`) and simulator trajectories classifies the 16 losses into three distinct causal categories:

```
Total 16 Loss Seeds
├── Category A: Non-Reversal Losses (3 seeds: 246008, 246010, 246016)
│   └── Never reversed; stayed specialized from Step 72 to 719. Losses driven by spot price softening.
├── Category B: Reversal Flip-Flop Loss (1 seed: 246024)
│   └── Quad-phase oscillation: YARN (72) -> BASELINE (144) -> BASELINE (216) -> YARN (288). 
└── Category C: Single Mid-Flight Reversals (12 seeds)
    ├── Sub-Group C1: True Harmful Reversals where Specialization was Viable (5 seeds: 246003, 246005, 246028, 246035, 246049)
    │   └── Market prices were high enough that staying committed was profitable; reversal caused avoidable loss.
    └── Sub-Group C2: Adaptive Reversals where Specialization was Structurally Unviable (7 seeds: 246007, 246022, 246030, 246032, 246036, 246039, 246042)
        └── No Yarn Store unlocked; staying committed led to massive dead wool inventory and feed drain. Reversal to baseline, while noisy, was actually protective.
```

---

## 3. Forensic Causal Tracing of the Hysteresis Seeds

### 3.1 Trace of Seed 246024 (The Quad-Phase Oscillation Catastrophe: -$10,369.00)
- **Pre-Commitment (Step 0–71)**: Identical to baseline. Money = $142.00.
- **Commitment Event (Step 72)**: Candidate selects `YARN_SPECIALIZED` ($\Delta = +3,595.0$). 
- **Assets Purchased (Steps 72–143)**: Purchases strawberry seeds, sells wheat at specialized cadence, alters tile hydration.
- **Information Update & Reversal 1 (Step 144)**: Shop 2 unlocks as `BAKERY` (no Yarn Store). Projected delta drops to 0.0. Planner abruptly switches to `BASELINE_BACKBONE`.
- **Mismatch Created (Steps 144–287)**: Planner executes backbone worker paths, desynchronizing strawberry harvesting.
- **Information Update & Reversal 2 (Step 288)**: Shop 4 unlocks as `PIZZA_SHOP`. Projected margin flips back to `YARN_SPECIALIZED`. Planner re-specializes at Step 288!
- **Downstream Consequence**: Extreme worker confusion, missed late-game melon harvesting, completely stranded inventory. Terminal loss: **-$10,369.00**.
- **Kill-Test Impact**: When `HYSTERESIS_COMMITMENT_GUARD` prevented the flip-flop, the candidate remained stably committed to Yarn, finishing at **-$1,011.00** (**+$9,358.00 recovery**).

### 3.2 Trace of Seed 246028 (Avoidable Hysteresis Loss: -$2,113.00)
- **Commitment (Step 72)**: Specializes in Yarn.
- **Sunk Capital**: Strawberry plantings and specialized feed schedules.
- **Reversal (Step 144)**: Shop 2 reveals `ICE_CREAM_SHOP`. Projected margin drops; planner reverts to `BASELINE_BACKBONE`.
- **Mismatch Created**: Backbone fails to shear sheep efficiently; wheat feed is misallocated.
- **Downstream Consequence**: Finished at -$2,113.00.
- **Kill-Test Impact**: Staying committed allowed full wool production. Because wool prices were high ($320/unit), candidate achieved **+$8,775.00** (**+$10,888.00 recovery**).

### 3.3 Trace of Seed 246022 (The "Trap" Seed: Reversal was Actually Protective!)
- **Commitment (Step 72)**: Specializes in Yarn based on early wool spot price ($350/unit).
- **Information Update (Step 144)**: Shop 2 reveals `ICE_CREAM_SHOP` (no Yarn Store). Projected margin drops below $\tau$. Planner reverts to `BASELINE_BACKBONE`.
- **Original DEV-004 Outcome**: Reversal created tile mismatch; candidate lost **-$3,794.50**.
- **Kill-Test Intervention (`HYSTERESIS_COMMITMENT_GUARD`)**: The guard forced candidate to stay in `YARN_SPECIALIZED`.
- **Downstream Consequence of Guard**: With no Yarn Store across all 30 days, town wool pull capacity was capped at 1 unit / 12 turns (60 units total). The candidate produced 180 wool units! 120 units of wool sat completely dead in the shed, while 11 sheep consumed expensive feed every single day.
- **Kill-Test Outcome**: Candidate collapsed to **-$8,188.00** (worsened by **-$4,393.50**)!
- **Forensic Finding**: Reversing to baseline at Step 144 was **NOT** the fundamental disease. Reversing was an adaptive retreat from an unviable market environment. Forcing commitment exacerbated the failure by +115%!

---

## 4. Forensic Investigation of the Positive Controls

In DEV-004, four winning seeds exhibited route reversals:
- `246012`: Won +$8,330.00
- `246026`: Won +$8,816.00
- `246034`: Won +$5,453.00
- `246048`: Won +$14,143.00

### 4.1 The Positive Control Collapse on Seed 246048
- **Original DEV-004 Dynamics**:
  1. Step 72: Selected `YARN_SPECIALIZED`.
  2. Step 144: Shop 2 was `PIZZA_SHOP` (no Yarn Store). Planner reverted to `BASELINE_BACKBONE`. Reversion stopped candidate from purchasing 2 sheep at Step 150 when cash was critically low ($234).
  3. Step 216: Shop 3 unlocked `YARN_STORE`! Planner re-specialized into Yarn with abundant liquidity ($725), fully capitalizing on the late Yarn Store and crushing the baseline by **+$14,143.00**.
- **Kill-Test Dynamics (`HYSTERESIS_COMMITMENT_GUARD`)**:
  1. The commitment guard blocked the Step 144 reversion.
  2. Forced to execute `YARN_SPECIALIZED`, candidate purchased 2 sheep at Step 150 for $500, draining cash down to $124!
  3. Low liquidity delayed worker hiring and fertilization. When the Yarn Store finally unlocked at Step 216, candidate lacked working capital to scale wool production.
  4. Terminal Outcome: **-$11,577.00**!
  5. **Net Shift**: A catastrophic collapse of **-$25,720.00** from a single positive control seed!

---

## 5. Mechanistic Synthesis: Why the DEV-004 Reversal Hypothesis Failed

The hypothesis formulated in EXP-DEV-004 was:
$$\text{Hypothesis: Mid-flight route reversal is the primary causal flaw; adding commitment will eliminate losses.}$$

The empirical kill-test conclusively demonstrates that this hypothesis is **mechanistically false**:

1. **Reversal is a Secondary Symptom, Not the Root Cause**:
   The planner did not reverse because of random noise; it reversed because the external environment (town shops) invalidated the route's market absorption model.
2. **The Root Disease is Premature Speculative Specialization**:
   At Step 72, only 1 of 4 town shops is known. `YARN_SPECIALIZED` requires either an unlocked `YARN_STORE` (pull rate 1/4) or persistent high wool spot prices. In seeds where no Yarn Store ever appeared, specializing at Step 72 was a high-risk gamble.
3. **Commitment Creates Asymmetric Downside in Non-Matching Worlds**:
   If an agent commits to a specialized livestock route without the matching town shop, it accumulates physical assets (sheep) whose products cannot be absorbed. The feed cost of 11 sheep ($11 \times 10 = \$110$/day) rapidly drains working capital, creating late-game liquidity failure.
4. **Adaptive Reversal is Necessary When Market Assumptions Fail**:
   While reversing creates temporary physical desynchronization (-$2k to -$3k), stubbornly persisting in an unviable specialized route creates total market absorption failure (-$5k to -$10k).

---

## 6. Audit Conclusion

The `HYSTERESIS_COMMITMENT_GUARD` recovered **+$9,673.50 (20.56%)** of total 16-seed loss magnitude (22.39% of reversal losses), falling far short of the pre-registered **50.0%** threshold ($21,599.25). 

Furthermore, by blocking necessary defensive retreats, it caused severe new failures:
- It worsened losses on **7 of 13 reversal loss seeds** (accumulating -$16,946.50 in new losses).
- It collapsed Positive Control Seed 246048 from **+$14,143.00** into **-$11,577.00** (-$25,720.00 net damage).

The retrospective kill-test conclusively refutes the hypothesis that commitment hysteresis alone can solve the DEV-004 losses.
