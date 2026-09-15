# EXP-DEV-001 POSTMORTEM FINAL CORRECTIONS LEDGER

**Experiment Identifier**: `EXP-DEV-001`  
**Governing Standard**: Epistemic Audit & Retraction Standard  
**Date**: 2026-09-11  
**Auditor**: Antigravity Autonomous Pair Programmer  

---

## 1. Formal Corrections Table

The following claims from the original experiment report and preliminary postmortem notes have been audited, scoped, and officially corrected:

| Claim ID | Previous Claim | Corrected Claim | Reason for Correction | Evidence Base |
| :--- | :--- | :--- | :--- | :--- |
| **CORR-01** | *"Seed 50018 failed due to Day 3 Pet Cafe and Day 6 Yarn Store causing carrot diversion, animal starvation, and feed buffer collapse."* | **Seed 50018 failed because Day 11 Tomato substitution underperformed after 5 Strawberry shops unlocked late in the game.** | The previous narrative confused Seed 50000 with Seed 50018. Zero carrots were planted; animals never starved; feed buffers remained intact. | Replay trace and action log in [`experiments/EXP-DEV-001/SEED_50018_FORENSIC.md`](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-DEV-001/SEED_50018_FORENSIC.md). |
| **CORR-02** | *"The -$2,388 loss on Seed 50018 was 100% caused by single-farm crop replacement in isolation."* | **The -$2,388 paired loss is a general equilibrium market price effect: candidate lost $1,231 in net crop sales while V2 captured an uncontested monopoly on high-price strawberry demand.** | The loss is a paired margin in a shared market, not an isolated single-farm accounting line. Cand cash was higher than self-play ($105.9k vs $101.9k), but V2 cash was boosted even more ($107.1k). | Counterfactual simulation and economic decomposition in [`scratch/audit_seed_50018_accounting.py`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/audit_seed_50018_accounting.py). |
| **CORR-03** | *"Treatment fallback to V2 on 42/50 seeds covered 62.5% of the shop draw space."* | **62.5% (5/8) is the single-draw marginal probability of Yarn/Strawberry types. The probability of falling back to V2 across the 2-shop sequence is 85.94% (55/64), matching the 84.0% empirical tie rate.** | Conflating single-slot marginal probability with 2-step joint sequence probability was mathematically imprecise and misleading. | Combinatorial proof and empirical audit in [`experiments/EXP-DEV-001/EXP-DEV-001_SHOP_TRAJECTORY_AUDIT.csv`](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-DEV-001/EXP-DEV-001_SHOP_TRAJECTORY_AUDIT.csv). |
| **CORR-04** | *"Dynamic adaptation degrades agent Elo in a Swiss tournament format, mathematically lowering Top-10 probability."* | **EXP-DEV-001 provides a negative development signal for early unhedged specialty crop replacement by demonstrating unacceptable downside tail risk ($-\$2,388 < -\$800$). Competition format details remain unmodeled.** | Unverified assertions regarding tournament formats exceeded the empirical scope of the local experiment. | Scoped language in [`experiments/EXP-DEV-001/EXP-DEV-001_FINAL_INTERPRETATION.md`](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-DEV-001/EXP-DEV-001_FINAL_INTERPRETATION.md). |
