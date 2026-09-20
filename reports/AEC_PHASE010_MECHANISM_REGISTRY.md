# AEC PHASE 010: MECHANISM QUALIFICATION REGISTRY
**Author**: Lead Scientific Experiment Engineer, Adaptive Economic Compiler (AEC)  
**Date Established**: 2026-09-18  
**Architecture Freeze Point**: Phase 009 Finalized 44-Item Platform  
**V3 Baseline Chassis Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Governance Invariants**: Protected Cohorts Untouched (`340050–340199`, `214200–214249`, `340300–340349`)  

---

## 1. Master Mechanism Registry Matrix

| Mechanism | Priority Group | Implementation Completeness | Synthetic Matrix Verified | Natural Exposure Status | Empirical Economic Delta | Replicated Cohort | Qualification Gate Status | Live Build Eligibility |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DEPENDENCY_AWARE_MARKET_TIMING** | Foundation | Complete (100%) | Passed | High (100% commits) | +$43.44 ± $18.51 (t=2.35, p=0.019) | Verified (Phase 008/009) | **QUALIFIED (FOUNDATION)** | **LIVE-ELIGIBLE** |
| **TERMINAL_LIQUIDATION** | Foundation | Complete (100%) | Passed | High (Terminal) | Verified Baseline | Verified (Phase 008/009) | **QUALIFIED (FOUNDATION)** | **LIVE-ELIGIBLE** |
| **PHASE_SHUTDOWN** | Foundation | Complete (100%) | Passed | High (Late Game) | Verified Baseline | Verified (Phase 008/009) | **QUALIFIED (FOUNDATION)** | **LIVE-ELIGIBLE** |
| **DYNAMIC_SHADOW_HARVEST** | Group A (1) | Complete (100%) | Passed | 1,876 cands, 0 commits | -$4.67 ± $4.67 (baseline dominance) | Seeds 249050..249052 | **DORMANT / ECONOMICALLY DOMINATED** | Quarantined |
| **TERMINAL_HARVEST_SWEEP** | Group A (2) | Complete (100%) | Passed | 826 cands, 0 commits | +$13.67 ± $46.84 (baseline dominates) | Seeds 249053..249055 | **DORMANT / ECONOMICALLY DOMINATED** | Quarantined |
| **LABOR_SHADOW** | Group A (3) | Complete (100%) | Passed (12/12 GT) | Active in Funnel Stage 5 | Exact marginal valuation verified | GT-01..GT-12 Verified | **QUALIFIED (VALUATION INFRASTRUCTURE)** | **LIVE-ELIGIBLE (INFRASTRUCTURE)** |
| **ROUTE_COMPRESSION** | Group B (4) | Complete (100%) | Passed | 266 cands, 0 commits | +$62.00 ± $33.08 (100% foundation) | Seeds 249056..249058 | **DORMANT / ECONOMICALLY DOMINATED** | Quarantined |
| **CARGO_FERRY** | Group B (5) | Complete (100%) | Passed | 744 cands, 0 commits | +$26.00 ± $28.45 (100% foundation) | Seeds 249059..249061 | **DORMANT / ECONOMICALLY DOMINATED** | Quarantined |
| **TOWN_CYCLE** | Group C (6) | Complete (100%) | Passed | 1,337 cands, 247 commits | -$36,655.33 ± $14,386.69 (t=-2.55) | Seeds 249062..249064 | **FAILED QUALIFICATION** | **PERMANENTLY QUARANTINED** |
| **SHOP_ARBITRAGE** | Group C (7) | Complete (100%) | Passed | 2,118 cands, 0 commits | +$11.00 ± $21.08 (100% foundation) | Seeds 249065..249067 | **DORMANT / ECONOMICALLY DOMINATED** | Quarantined |
| **PRODUCTION_ARBITRAGE** | Group C (8) | Complete (100%) | Passed | 2,656 cands, 0 commits | +$126.67 ± $23.15 (100% foundation) | Seeds 249068..249070 | **DORMANT / REDUNDANT WITH BASELINE** | Quarantined |
| **TERMINAL_CONVERSION** | Group C (9) | Complete (100%) | Passed | 138 cands, 0 commits | +$89.33 ± $66.69 (100% foundation) | Seeds 249071..249073 | **DORMANT / ECONOMICALLY DOMINATED** | Quarantined |
| **EMERGENCY_FEED_PURCHASE** | Group D (10) | Complete (100%) | Passed (Adverse 100%) | 0 natural commits | +$28.67 ± $52.84 (100% foundation) | Seeds 249074..249076 | **INSUFFICIENT NATURAL EXPOSURE** | Quarantined |
| **EMERGENCY_RECOVERY** | Group D (11) | Complete (100%) | Passed | 296 cands, 20 commits | -$25,792.00 ± $4,815.05 (t=-5.36) | Seeds 249077..249079 | **FAILED QUALIFICATION** | **PERMANENTLY QUARANTINED** |
| **OPPONENT_PREEMPT_SELL** | Group E (12) | Complete (100%) | Passed | 7,812 cands, 2 commits | -$96.67 ± $96.67 (harmful drop -$290) | Seeds 249080..249082 | **FAILED QUALIFICATION** | **PERMANENTLY QUARANTINED** |
| **META** | Group E (13) | Complete (100%) | Passed | 0 target commits | +$126.00 (100% foundation commits) | Seeds 249083..249085 | **RESEARCH ONLY (LATENCY EXCEEDS BUDGET)** | Quarantined (Research Build Only) |
| **RESOURCE_CONVERSION** | Group F (14) | Complete (100%) | Passed | Prior Negative ITT | Prior Falsification Applies (-$258.96) | Prior Falsified Cohort | **STRICTLY QUARANTINED** | **STRICTLY QUARANTINED** |

---

## 2. Gate Taxonomy & Qualification Rules

1. **QUALIFIED**: All 12 items of the Qualification Contract satisfied; positive paired delta with compatible CI; clean mechanism attribution; replicated on independent development cohort. Promoted to `AEC_ROBUST_QUALIFIED`.
2. **PROMISING / NEEDS REPLICATION**: Natural exposure occurred with positive signal, but pending replication or additional sample size.
3. **INCONCLUSIVE / INSUFFICIENT EXPOSURE**: Mechanism verified synthetically, but natural game exposure is near-zero under empirical play.
4. **DORMANT / FUNCTIONALLY COMPLETE**: Naturally dormant because baseline optimal policy leaves zero unharvested mature crops or unserved obligations; mechanism preserved in research platform without live enablement.
5. **FAILED QUALIFICATION**: Negative paired delta, harmful tail risk, poor counterfactual fidelity, or safety violation.
6. **STRICTLY QUARANTINED**: Prior empirical falsification or unverified economic rationale; barred from live deployment.
