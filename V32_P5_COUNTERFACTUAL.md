# V32 P5 — COUNTERFACTUAL REPLAY ANALYSIS

## 1. EXECUTIVE SUMMARY

In accordance with Section 27 of the V32 P5 Protocol, counterfactual replay experiments were conducted using simulator-valid executions (no synthetic splicing) to establish whether early divergences are harmless, recoverable, locally bad, or catastrophic.

---

## 2. THREE CONTROLLED COUNTERFACTUAL EXPERIMENTS

### Counterfactual A: P4 Arm 1 with Step-0 Farmer Pass Patch
- **Intervention**: At $t=0$, enforce `farmer = ['PASS']` while letting the P4 Arm 1 model naturally predict the market wash and all downstream actions ($t \ge 1$).
- **Observed Behavior**:
  - Step 1: Model naturally commands `farmer: ['NORTH']` (100% match) and executes the complete 5-hire and livestock purchase orders!
  - Step 2: Farm has 5 hands present and $1,253 deployed capital.
- **Attribution**: Proves conclusively that the Step-1 failure in P4 Arm 1 was not a failure of the model to learn hiring or livestock buying, but an unavoidable covariate shift caused entirely by the farmer being at (4, 5) instead of (5, 5).

### Counterfactual B: Arm 2 (Trained Early-Horizon Weighting, Inference Free-Running)
- **Intervention**: Zero inference patching. The Arm 2 model (`results/v32_p5_arm2_early_weighting.npz`) runs fully autonomously in closed loop.
- **Observed Behavior**:
  - Step 0: Model naturally executes `farmer: ['PASS']` AND market wash (`[['BUY_PRODUCT', 'WHEAT', 7], ['SELL', 'WHEAT', 30]]`).
  - Step 1: Model naturally executes `farmer: ['NORTH']` AND hires 5 hands!
  - Step 2: All 5 hands are present on the field.
  - Step 2 Farmer Action: Model commands `['PICKUP', 'COW']` at tile [4, 3].
- **Causal Consequence**:
  - At [4, 3], the farmer is 1 tile north of the shed. The pickup command is rejected by the engine.
  - The farmer holds no cows.
  - At Steps 3–6, the farmer continues walking North to [4, 0] (the board boundary).
  - Animals are never placed in pasture. The 5 hands idle, consuming Day 1 wages without harvesting crops.
  - Terminal cash collapses to $0.00.

### Counterfactual C: Arm 2 with Step-2 Shed Return Patch
- **Intervention**: Enforce `farmer = ['SOUTH']` at $t=2$ so the farmer steps back to the shed [4, 4] where livestock reside.
- **Observed Behavior**:
  - Step 2: Farmer successfully returns to [4, 4].
  - Step 3: Farmer is shed-adjacent and can pick up livestock.
  - Terminal cash reaches **$271.00** (up from $0.00).
  - Downstream drift recurs around steps 6–10 during pasture fence placement and crop planting.

---

## 3. SEVERITY CLASSIFICATION

Under the Section 27 taxonomy:

| Timestep | Action Head Differing | Error Classification | Mechanism | Downstream Impact |
|:---:|:---:|:---:|:---|:---|
| **Step 0** (P4) | Farmer Unit Op (`WEST` vs `PASS`) | **Catastrophic** | Farmer out of position for Step 1 hiring | 0 hands hired; $108 cash |
| **Step 0** (P5 Arm 2) | None (100% Matched) | **REPAIRED** | Step-0 Wash + PASS both executed | 5 hands hired; $1,005 deployed |
| **Step 1** (P5 Arm 2) | None (100% Matched) | **REPAIRED** | Farmer moves North, hires 5 workers | 5 hands on field at Step 2 |
| **Step 2** (P5 Arm 2) | Farmer Unit Op (`PICKUP` vs `SOUTH`) | **Catastrophic** | Premature pickup 1 tile away from shed | Animals never collected; $0 cash |
