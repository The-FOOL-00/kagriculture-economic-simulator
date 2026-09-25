# V32 P8 — DECISION REPORT: THE POST-P7 PIVOT & MACRO ARCHITECTURE DECISION
**Phase:** V32 P8  
**Date:** 2026-09-23  
**Status:** COMPLETE — DECISIVE RESEARCH DIRECTION LOCKED  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. PRIMARY CONCLUSION

```text
======================================================================
PRIMARY CONCLUSION:
OPTION B SELECTED — STOP MEMORY WORK AND PURSUE MACRO PLANNER

SEQUENCE-MEMORY INVESTIGATION: PERMANENTLY CLOSED (HARD NO-GO)
NEURAL BEHAVIORAL CLONING TRACK: PERMANENTLY CLOSED
HIERARCHICAL MACRO-ECONOMIC HYBRID: OFFICIALLY COMMISSIONED FOR P9
======================================================================
```

Phase V32 P8 was designed to eliminate strategic uncertainty and prevent the program from wasting the remaining 7 days of competition time on further variants of imitation learning.

Through an adversarial forensic audit of all 240 expert demonstration legs, counterfactual state-perturbation experiments, compiler bytecode disassembly, and exact tournament simulator evaluations of active baselines (A7, V22R1, V3, Dmitrii LB 2800, V54/V66), P8 establishes the definitive scientific answers to the program's core dilemmas.

---

## 2. ANSWERS TO THE 8 MANDATORY FINAL DECISION QUESTIONS

### Q1: Is the current closed-loop failure primarily state representation, missing history, teacher-route structure, economic planning, execution robustness, or a combination?
**ANSWER: TEACHER-ROUTE STRUCTURE COMBINED WITH LACK OF MACRO-ECONOMIC PLANNING.**
- **Missing History is Refuted:** Across all 240 recorded demonstration legs, the teacher's action is 100% deterministic given only the integer step index $t$ ($H(A_t \mid t) = 0.0000$ bits). The teacher does not condition on past observation history; it executes an open-loop precomputed 719-step action tape (`RouteTape[step]`).
- **The True Bottleneck:** Asking a continuous neural network to memorize an arbitrary 719-step open-loop choreographic script from instantaneous continuous features is fundamentally flawed. In closed loop, slight numerical shifts (such as wash quantity differences) cause continuous latent representations to drift across softmax boundaries.
- **Economic Planning Absence:** The BC policy possessed zero semantic awareness of capital runways, wage burdens, or crop production loops. When an action broke, it had no macro-planner to replan or recover.

### Q2: Does history actually disambiguate the teacher action?
**ANSWER: NO.**
Empirical analysis of the demonstration corpus proved that conditional action entropy $H(A_t \mid t)$ is exactly zero across all 240 seats. In our counterfactual swap test, holding the physical state constant and varying the step index $t$ changed the teacher's action identically to the script; while holding step $t=3$ fixed and drastically perturbing cash ($50 to $5000) or shed inventory (0 to 4 cows/sheep) produced **zero change** in the teacher's action (`['PICKUP', 'SHEEP']` in 100% of trials). The teacher's action is an open-loop script, not a history-dependent Markov or POMDP policy.

### Q3: Does a small memory model improve closed-loop economics enough to justify continuing?
**ANSWER: NO — HARD NO-GO.**
Because the training data has zero history-conditioned variance, an RNN/GRU/LSTM would receive no informative gradient signal from history. It would merely act as an analog step counter, which is wildly sample-inefficient, brittle under closed-loop distribution shift, and completely incapable of economic reasoning. Training sequence models is formally rejected.

### Q4: What economic decisions explain the largest score gap between current ~1800 behavior and stronger observed strategies?
**ANSWER: FIVE CRITICAL MECHANISMS:**
1. **The Step-0 Wash Sizing (+$1,286 alpha):** A7's 30/30 wash saves ~$108 in round-trip slippage, crossing the Day 0 melon purchase threshold and enabling +1 melon plant (`MELON: 12` vs `MELON: 11`).
2. **Adaptive Labor Scaling:** Top agents hire workers dynamically based on the pending chore queue, avoiding wage-drain starvation when chores are few.
3. **Shop-Conditioned Crop & Livestock Allocation:** Re-routing production on Days 3 and 6 to match revealed town shop demand (e.g. Yarn Store, Bakery, Pet Cafe).
4. **Market Queue Timing & Front-Running:** Selling in batches of 18–24 units before scheduled opponent sell dumps to avoid price slippage.
5. **Terminal Physical Simulation Search (Dmitrii LB 2800):** A 7-step physical Monte Carlo search at turns 712–718 that extracts all remaining shed and field inventory into cash, capturing $3,000–$12,000 left behind by static tapes.

### Q5: What is the smallest viable architecture that can exploit those economic decisions?
**ANSWER: THE HIERARCHICAL MACRO-ECONOMIC HYBRID (HMEH).**
A modular two-tier architecture:
- **Tier 1 (Macro-Planner):** Evaluates economic state and fires event-driven replanning on Days 0, 3, 6, 12, 27 to set labor caps, land milestones, crop targets, and animal purchases.
- **Tier 2 (Chore Executor):** A deterministic 4-pass spatial dispatcher that manages stand-on chores, shed logistics, chore bidding, and obstacle-aware pathfinding.

### Q6: Can the architecture preserve proven A7 mechanisms while becoming adaptive?
**ANSWER: YES, COMPLETELY.**
The HMEH architecture explicitly hardcodes the proven A7 30-wash at Step 0 and the initial 5-worker / pasture livestock setup across Steps 1–8. Only after the bootstrap phase is secured (from Step 9 onward) does the adaptive macro-planner take command. Furthermore, the protected A7 standalone agent acts as the hard fallback if any unexpected condition occurs.

### Q7: What can realistically be implemented and evaluated before 2026-09-30?
**ANSWER: A 3-STAGE SPRINTER PLAN (7 DAYS REMAINING):**
- **Stage 1 (Sep 24):** Complete implementation of HMEH compiler (`candidates/v32_hmeh/`) and verify 100% legality on unit tests.
- **Stage 2 (Sep 25–26):** Execute the 120-leg development screen against core opponents (`E0_V3`, `E1_V22R1`, `E2_A7`, `E8_DMITRII`, `V54`, `SYN_AGG`). Tune the 12 macroeconomic parameters.
- **Stage 3 (Sep 27–28):** Implement the 7-step terminal liquidation closure (adapted from Dmitrii Gluzdov) to capture late-game inventory alpha.
- **Stage 4 (Sep 29–30):** Final release freeze, integrity audit, package bundling, and submission into live competition slots.

### Q8: Which experiments should be permanently closed so the program does not loop?
**ANSWER: PERMANENT STOP LIST (CLOSED FOREVER):**
- $\times$ Another uniform BC loss reweighting experiment ($\lambda$ tweaks).
- $\times$ Another per-step loss spike ($\lambda_{s3}, \lambda_{s4}$, etc.).
- $\times$ Trajectory Prefix-8, Prefix-12, or Prefix-24 BC training.
- $\times$ Phase-conditioned BC embeddings (proven incapable due to same-phase confusion).
- $\times$ Recurrent sequence-memory models (RNN / GRU / LSTM / Transformer).
- $\times$ Unconstrained end-to-end Reinforcement Learning (PPO remains CLOSED).

---

## 3. MASTER EVALUATION & SCREENING AUDIT RECORD

```json
{
  "phase": "V32_P8",
  "decision": "OPTION_B_STOP_MEMORY_PURSUEMACRO_PLANNER",
  "memory_gate": "HARD_NO_GO",
  "ppo_gate": "PERMANENTLY_CLOSED",
  "findings": {
    "demonstration_legs_audited": 240,
    "step_farmer_action_entropy": 0.0,
    "teacher_type": "open_loop_action_tape_with_reactive_patches",
    "a7_wash_margin_vs_v3": 1286.0,
    "a7_mechanism": "+1 Melon plant enabled by $108 Step 0 wash slippage savings",
    "v22r1_margin_vs_v3": 18.4,
    "frontier_leaderboard_reference": "Dmitrii Gluzdov LB 2800 (7-step Monte Carlo terminal search) + V54/V66 Declarative Backbone"
  },
  "recommended_architecture": "Hierarchical Macro-Economic Hybrid (HMEH)",
  "competition_deadline": "2026-09-30T23:59:59Z"
}
```
