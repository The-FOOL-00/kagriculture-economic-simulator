# Kagriculture Scientific Research History (V22 – V60)

This document provides a comprehensive, chronological record of the hypotheses, experiments, empirical benchmarks, failure modes, and architectural breakthroughs across the Kagriculture project lifecycle.

---

## Evolution Timeline Summary

```
V22R1 (Baseline Release)
  ├── V23: Backbone Challenge
  ├── V24: Live Meta & Challengers (C1 idle zeroing, C2 livestock scale, C3 carrot compound) [Preserved in culture/v24]
  ├── V25: Coherent Planner Campaign (P1 macro, P2 options, P3 unified) [Preserved in culture/v25]
  ├── V26: Backbone-Aware AEC
  ├── V27: Robustness & Noise Audit (Outcome D)
  ├── V28: A7 Confirmation Protocol
  ├── V29: A7 Promotion Holdout
  ├── V30: A7 Standalone Packaging & Gauntlet
  ├── V31R2: Real-Price Forensics & Live Scorecards
  ├── V32: RL-X2 Macro-Actions & Behavioral Cloning
  ├── V33: Public Meta-Strategy Replication & Route Selection
  ├── V34: Tactical Exact Search & Liquidity Safety
  ├── V35: A7 Opening Wash Controller [Submitted Milestone]
  ├── V36: Independent Validation & Casualty Audit
  ├── V37: Production Packaging & Determinism Staging
  ├── V38: Heuristic-Guided PPO & Counterfactual Engine
  ├── V39: Live-Loss Forensics & Terminal Liquidation
  ├── V40: FastKagricultureSim High-Throughput Engine & Recurrent RL
  ├── V41: Safe Residual RL & Counterfactual Value Gating
  ├── V42: Staggered Terminal Asset Liquidation
  ├── V43: Multi-Step Compositional Alpha Discovery
  ├── V44: Systematic CapEx Cutoff (Step >= 520 Guard)
  ├── V45: Opponent Market Pressure Modeling (AUROC 0.94)
  ├── V46: Macro-Route Diversity & Strategy Selector Analysis
  ├── V47: Public 2945 Chassis Deconstruction & Elite Transfer
  ├── V48: Surgical Shop-Route 105 Overrides (+0.74 Alpha)
  ├── V49: Live Top-Meta Memory & E402 Late Seed-Cap Overlay [FINAL INCUMBENT: 99.31% WR]
  ├── V50: Late Capital Leakage & Fertilizer Buyback Suppression [Rejected: Starved Crops]
  ├── V51: Weed Blocked-Action Repair Replay Buffer [Rejected: 0 Firings / Inert]
  ├── V52: Herd Composition Swapping & CowSwap [Rejected: Shed Saturation]
  ├── V53: Bit-Exact Engine Parity Revalidation (kaggle-environments 1.32.7)
  ├── V54: Public-Opponent State Reconstruction & Divergence Boundary
  ├── V55: Post-Reveal Shop Route Adaptation [Rejected: Midgame Desync]
  ├── V56: Microscopic Forensic Autopsy of V49's 4 Loss Worlds
  ├── V57: Market Queue Microstructure & Slot Alignment Optimization [Pareto-Optimal Lock]
  ├── V58: August 3100+ Elite Replay Reconstruction [100% Win Rate Against August Meta]
  ├── V59: September Elite Meta Reconstruction & Replay Corpus Design
  └── V60: September Replay Acquisition, A100 Staging & Recovery Build
```

---

## Detailed Version Dossiers (V40 – V60)

### V40: Unrestricted Recurrent Macro RL & FastKagricultureSim
- **Objective**: Train a macro-level PPO/GRU reinforcement learning policy operating over 16 abstract economic actions.
- **Methodology**: Developed `FastKagricultureSim`, a high-throughput Python simulator matching Kaggle engine semantics at 500+ steps/second.
- **Empirical Result**: Parity verified, but end-to-end RL training collapsed against rule-based baselines due to credit assignment latency across 700 steps.
- **Surviving Component**: `FastKagricultureSim` high-throughput headless benchmark harness.

### V41: Safe Residual RL & Counterfactual Action Gating
- **Objective**: Superimpose a residual RL correction network over the deterministic baseline, gated by counterfactual Q-values ($\Delta Q > 0$).
- **Methodology**: Offline RL trained on expert tournament trajectories.
- **Empirical Result**: Zero positive alpha discovered; residual noise disrupted delicate multi-turn choreography.
- **Surviving Component**: Counterfactual evaluation engine and deterministic rollout diff tools.

### V42: Staggered Terminal Asset Liquidation
- **Objective**: Harvest maximum terminal liquidity by liquidating non-productive animals and inventory before match conclusion.
- **Methodology**: Turn-by-turn counterfactual scan across steps 650–700.
- **Empirical Result**: Confirmed positive cash gain when liquidation timing respects final market delivery deadlines.
- **Surviving Component**: Staggered terminal liquidation bounds integrated into production controllers.

### V43: Multi-Step Compositional Alpha Discovery
- **Objective**: Systematically combine discrete micro-alphas discovered in V41–V42 without destructive cross-phase interference.
- **Methodology**: Orthogonal decomposition testing across production, expansion, and terminal regimes.
- **Empirical Result**: Validated robust cumulative margin improvement.
- **Surviving Component**: Formal compositional alpha verification protocol.

### V44: Full-Game Economic Portfolio & Systematic CapEx Cutoff
- **Objective**: Optimize capital allocation by cutting off non-amortizing capital expenditures in the endgame.
- **Methodology**: Sweep of capital cutoffs across livestock and land acquisition steps.
- **Empirical Result**: **Major Breakthrough**. Discovered the **Step >= 520 CapEx Cutoff Rule**: forbidding `BUY_ANIMAL` and `BUY_LAND` after turn 520 saves thousands in stranded capital.
- **Surviving Component**: Hard constraint `step >= 520` CapEx cutoff, adopted in all subsequent agents.

### V45: Opponent Market Pressure Modeling
- **Objective**: Predict opponent commodity deliveries and front-run price degradation using machine learning.
- **Methodology**: Trained gradient boosted classifiers (AUROC 0.94) on 100k turns of opponent market history.
- **Empirical Result**: Accurate classification, but transit delay prevented actionable front-running; market prices reset dynamically.
- **Surviving Component**: Rigorous observability audit rules (enforcing strict separation of public vs private state).

### V46: Macro Route Diversity & Strategy Selector Analysis
- **Objective**: Train an early-turn meta-classifier to select optimal macro routes based on opponent style.
- **Methodology**: Evaluated multi-route portfolio against diverse opponent clusters.
- **Empirical Result**: Theoretical +1500 cash oracle ceiling, but realized selector had 8% false positives which caused catastrophic route divergence.
- **Surviving Component**: Mathematical framework separating oracle potential from realizable policy margin.

### V47: Public 2945 Elite Chassis Transfer
- **Objective**: Deconstruct and absorb the ultra-elite public 2945 benchmark chassis (Hayashi/Tschinkel lineage).
- **Methodology**: Systematic port of worker pathfinding, ORDERPRI2 priority, cow->goose substitution, and shed-room guards.
- **Empirical Result**: Baseline performance jumped into the 98%+ win rate tier when merged with V44 CapEx guards.
- **Surviving Component**: 2945 core movement engine, task dispatch, and shop routing infrastructure.

### V48: Surgical Shop-Route 105 Overrides
- **Objective**: Resolve specific shop pair weaknesses on the 2945 chassis.
- **Methodology**: Audited historical failure logs and mapped alternative shop routes for underperforming combinations.
- **Empirical Result**: Discovered that substituting **Route 105** for three specific shop pairs (Brunch/Farmers, Bakery/Brunch, PetCafe/Farmers) yielded **+0.74 alpha**, 4 historical rescues, and 0 casualties.
- **Surviving Component**: `_V48_OVERRIDES` dictionary active in production incumbent.

### V49: Live Top-Meta Memory & E402 Late Seed-Cap Overlay (FINAL INCUMBENT)
- **Objective**: Eliminate endgame seed overpurchasing and lock down tournament-grade stability.
- **Methodology**: Injected the **E402 Seed Cap**: after step 624, strictly clamp `BUY_SEED` for wheat and carrot to the exact remaining unplanted tile count.
- **Empirical Result**: **99.31% Win Rate (572W / 4L / 0T / 0 casualties across 576 fresh validation matches)**. Zero losses against historical public replays (400/400).
- **Surviving Component**: **The Final Submitted Incumbent Agent** (`candidates/v49_meta_fusion/main.py`).

### V50: Late Capital Leakage & Fertilizer Buyback Suppression
- **Objective**: Suppress late-game fertilizer purchases to preserve raw cash.
- **Empirical Result**: **FALSIFIED / REJECTED**. Negative alpha; starving late crops killed high-value town delivery payouts.

### V51: Weed Blocked-Action Repair Replay Buffer
- **Objective**: Buffer actions blocked by dynamic weed spawns and replay them on subsequent turns.
- **Empirical Result**: **FALSIFIED / REJECTED**. 0 blocked actions observed across 92,032 steps. The 2945 base route already pre-empts weed spawns via deterministic `DIG` actions.

### V52 & V53: Herd Composition Swapping & Engine Parity Revalidation
- **Objective**: Test dynamic animal ratio adjustments based on town order reveals.
- **Empirical Result**: Dynamic herd swapping caused severe shed bottlenecks and delayed deliveries. Bit-exact engine parity with `kaggle-environments 1.32.7` re-confirmed.

### V54: Public-Opponent State Reconstruction & Divergence Boundary
- **Objective**: Map the mathematical boundary of opponent predictability from public observations.
- **Empirical Result**: Proved that matches with identical observable early state diverge irrevocably post-step 144 due to unobserved stochastic draws.

### V55: Post-Reveal Shop Route Adaptation
- **Objective**: Dynamically swap routes mid-match after town reveals at days 6, 12, and 18.
- **Empirical Result**: **HARMFUL / REJECTED**. Win rate dropped to 78.65% due to inventory desynchronization and crop abandonment.

### V56: Forensic Autopsy of V49's 4 Loss Worlds
- **Objective**: Isolate the exact physical root cause of V49's 4 losses (seeds 250617 and 250621 vs V44).
- **Empirical Result**: V49 was ahead in cash at step 690; loss occurred at step 697 due to a simultaneous transaction queue collision where opponent had prior tie-breaking precedence in the market interpreter.

### V57: Market Queue Microstructure & Slot Alignment
- **Objective**: Intervene in transaction ordering to overcome the step 697 collision.
- **Empirical Result**: 24 queue intervention variants tested; 0 rescued the collision without degrading win rate on control seeds. V49 baseline confirmed Pareto-optimal.

### V58: August 3100+ Elite Replay Reconstruction
- **Objective**: Benchmark V49 against executable plans extracted from top August replays.
- **Empirical Result**: V49 achieved **400 wins out of 400 legs (100% WR)**, demonstrating that early carrot-0 strategies were completely obsolete against V49's wash/carrot economy.

### V59 & V60: September Elite Meta Acquisition & Recovery Staging
- **Objective**: Acquire late-competition match replays and build portable recovery bundles.
- **Empirical Result**: Established automated retrieval pipeline via Kaggle API and built the fully verified A100 recovery staging bundle.
