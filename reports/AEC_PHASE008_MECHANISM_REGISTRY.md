# AEC PHASE 008: AUTHORITATIVE MECHANISM REGISTRY
**Scientific Portfolio Governance, Activation Status, and Operational Boundaries**  
**Date:** 2026-09-18  
**Governance Standard:** Phase 008 Scientific Covenant  
**Authoritative Chassis SHA-256:** `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`

---

## 1. Governance Principles & Epistemic Taxonomy

A critical scientific distinction enforced throughout the Adaptive Economic Compiler project is:

$$\text{ARCHITECTURE COMPLETE} \neq \text{MECHANISM VALIDATED} \neq \text{LIVE ELIGIBLE}$$

A mechanism is **NOT** promoted to live competition simply because its Python classes exist, its tests pass, or it is integrated into `AECExecutor`. A mechanism achieves live eligibility **only** after surviving a pre-registered, prospective Common Random Numbers (CRN) trial with statistically significant value accretion ($p < 0.01$) or by originating directly from verified frozen baseline logic.

---

## 2. Mechanism Portfolio Classification

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             AEC MECHANISM PORTFOLIO                              │
├─────────────────────────┬──────────────────────────┬─────────────────────────────┤
│  ACTIVE / LIVE-ELIGIBLE │ PENDING / OFFLINE VALID  │   DIAGNOSTIC / QUARANTINED  │
│  - DEP_MARKET_TIMING    │ - DYNAMIC_SHADOW_HARVEST │   - ROUTE_COMPRESSION       │
│  - TERMINAL_LIQUIDATION │ - TERMINAL_HARVEST_SWEEP │   - CARGO_FERRY             │
│  - PHASE_SHUTDOWN       │                          │   - SHOP_ARBITRAGE          │
│  - MARKET_COLLISION     │                          │   - PRODUCTION_ARBITRAGE    │
│  - FROZEN_V3_BACKBONE   │                          │   - TERMINAL_CONVERSION     │
│  - EXACT_SIMULATOR      │                          │   - EMERGENCY_RECOVERY      │
│  - SAFETY_CERTIFICATE   │                          │   - OPPONENT_PREEMPT_SELL   │
│  - ROBUST_FALLBACK      │                          │   - TOWN_CYCLE (SIGNAL)     │
│                         │                          │   - LABOR_SHADOW (SCREEN)   │
├─────────────────────────┴──────────────────────────┴─────────────────────────────┤
│  STRICTLY QUARANTINED (BLOCKED):                   RETIRED / FALSIFIED:          │
│  - RESOURCE_CONVERSION                             - FRONTLOAD_ORDERS            │
│  - LOCAL_WEED_DIG                                  - WHOLE_ROUTE_SWITCHING       │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Comprehensive Mechanism Governance Registry

| Mechanism Family | Category | Current Status | Default Config State | Governance Layer Enforcement | Scientific Evidence & Provenance | Live Deployment Rationale |
|:---|:---:|:---:|:---:|:---|:---|:---|
| **DEPENDENCY_AWARE_MARKET_TIMING** | MARKET | **ACTIVE / LIVE-ELIGIBLE** | `ENABLED` | `AECConfig.enabled_mechanisms` | Proven in `EXP-AEC-003` ($+\$57.36$, $p = 0.0035$) across 50 prospective seeds. | Reorders same-turn orders to place uncoupled SELL orders before capital purchases while preserving same-asset order coupling. |
| **TERMINAL_LIQUIDATION** | TERMINAL | **ACTIVE / LIVE-ELIGIBLE** | `ENABLED` | `AECConfig.enabled_mechanisms` | Proven in `EXP-AEC-001` and validated across baseline V3 source. | Liquidates shed inventory at step 718 to maximize cash balance before terminal step 719. |
| **PHASE_SHUTDOWN** | TERMINAL | **ACTIVE / LIVE-ELIGIBLE** | `ENABLED` | `AECConfig.enabled_mechanisms` | Proven in `EXP-AEC-001` and validated across baseline V3 source. | Prevents purchasing crop seeds that cannot biologically mature before episode completion. |
| **MARKET_COLLISION_GUARD** | MARKET | **ACTIVE / LIVE-ELIGIBLE** | `ENABLED` | `SafetyChecker.verify()` | Checkpoint Phase & Phase 004 verification. | Prevents catastrophic price slippage when large baskets are executed in illiquid shops. |
| **DYNAMIC_SHADOW_HARVEST** | LABOR | **PENDING / OFFLINE VALIDATED** | `ENABLED` (Dev) / `QUARANTINED` (Live) | `AECConfig.quarantined_mechanisms` | Validated in Phase 006 offline replay. Preserves coupled trajectory via `CoupledPatch`. | Dormant in Phase 007 replay (0 commits). Requires prospective trial before live deployment. |
| **TERMINAL_HARVEST_SWEEP** | TERMINAL | **PENDING / OFFLINE VALIDATED** | `ENABLED` (Dev) / `QUARANTINED` (Live) | `AECConfig.quarantined_mechanisms` | Validated in Phase 006 offline replay. Coupled harvest + deposit + reconnect before step 718. | Dormant in Phase 007 replay (0 commits). Requires prospective trial before live deployment. |
| **ROUTE_COMPRESSION** | ROUTE | **DIAGNOSTIC / QUARANTINED** | `QUARANTINED` | `OpportunityEngine`, `PatchGenerator` | Phase 007 structural integration. | Currently a generator stub emitting dummy harvest. Quarantined until full spatial optimizer is written. |
| **CARGO_FERRY** | LABOR | **DIAGNOSTIC / QUARANTINED** | `QUARANTINED` | `OpportunityEngine`, `PatchGenerator` | Phase 007 structural integration. | Generator stub emitting dummy harvest for Hand 1. Quarantined until multi-turn route splicing is written. |
| **PRODUCTION_ARBITRAGE** | RESOURCE | **DIAGNOSTIC / QUARANTINED** | `QUARANTINED` | `OpportunityEngine`, `PatchGenerator` | Phase 007 structural integration. | Full input->growth->sale cycle model. Quarantined until prospective qualification. |
| **SHOP_ARBITRAGE** | MARKET | **DIAGNOSTIC / QUARANTINED** | `QUARANTINED` | `OpportunityEngine`, `PatchGenerator` | Phase 007 structural integration. | Exploits price elasticity across 72-turn shop reveals. Quarantined until prospective qualification. |
| **TERMINAL_CONVERSION** | TERMINAL | **DIAGNOSTIC / QUARANTINED** | `QUARANTINED` | `OpportunityEngine`, `PatchGenerator` | Phase 007 structural integration. | Endgame inventory conversion. Quarantined until prospective qualification. |
| **EMERGENCY_RECOVERY** | RESOURCE | **DIAGNOSTIC / QUARANTINED** | `QUARANTINED` | `OpportunityEngine`, `PatchGenerator` | Phase 004B and Phase 007. | Causal rescue for starvation/insolvency. Quarantined awaiting prospective preregistration. |
| **OPPONENT_PREEMPT_SELL** | MARKET | **DIAGNOSTIC / QUARANTINED** | `QUARANTINED` | `MetaOrchestrator`, `PatchGenerator` | Phase 007 Arm C empirical test: produced $-\$104.60$ delta (drawdown on 3 seeds). | Front-running opponent sells failed due to miscalibrated rival dump forecast. Diagnostic only. |
| **TOWN_CYCLE_SIGNAL** | TIMING | **SIGNAL_ONLY** | `DIAGNOSTIC` | `OpportunityEngine`, `AECExecutor` | Phase 007 structural integration. | Generates non-mutating copy of baseline orders. Purely observational signal; produces no actions. |
| **LABOR_SHADOW_PRICING** | LABOR | **SCREENING_ONLY** | `SCREENING` | `OpportunityCandidateFunnel` (Stage 5) | Phase 005B 5-tier valuation engine. | Operates in Candidate Funnel Stage 5 to prune dominated proposals. Does not propose standalone actions. |
| **RESOURCE_CONVERSION** | RESOURCE | **STRICTLY QUARANTINED** | `QUARANTINED` | `AECConfig.resource_conversion_enabled = False` | Falsified in Phase 004B: ITT mean delta was $-\$258.96$, causing capital exhaustion. | Hard-quarantined at config, opportunity, patch, and execution gates. Cannot commit under any condition. |
| **LOCAL_WEED_DIG** | ROUTE | **STRICTLY QUARANTINED** | `QUARANTINED` | `AECExecutor` Commit Gate (L565) | Sunk-cost labor valuation and unverified 48-step downstream heuristic. | Fails closed to baseline action. Strictly forbidden in competition. |
| **FRONTLOAD_ORDERS** | MARKET | **RETIRED / FALSIFIED** | `RETIRED` | `MECHANISM_REGISTRY["status"] = FALSIFIED` | Falsified in `EXP-AEC-002` ($-\$200.00$ drawdown). | Naive order-blind reordering destroys intra-basket price appreciation. Permanently retired. |

---

## 4. Configuration Binding & Enforcement Architecture

The mechanism boundaries are enforced through a 4-layer defense in depth:

1. **Layer 1: Configuration (`aec/config.py`)**:
   - `ENABLED_FOUNDATION_MECHANISMS`: Exactly 3 mechanisms (`DEPENDENCY_AWARE_MARKET_TIMING`, `TERMINAL_LIQUIDATION`, `PHASE_SHUTDOWN`).
   - `QUARANTINED_MECHANISMS`: 15 mechanisms explicitly locked.
   - `resource_conversion_enabled`: Evaluates `is_family_live_eligible("RESOURCE_CONVERSION")`, returning `False`.
2. **Layer 2: Opportunity Screening (`aec/opportunities/__init__.py`)**:
   - In frozen mode, any opportunity whose transformation family is not in `enabled_mechanisms` is quarantined and excluded from `actionable` proposals.
3. **Layer 3: Patch Generation Gate (`aec/patches/generator.py`)**:
   - Any opportunity family not in `enabled_mechanisms` is rejected during patch compilation.
4. **Layer 4: Executor Commit Gate (`aec/integration/executor.py`)**:
   - Even if a patch passes exact simulation and safety verification, lines 560–589 explicitly verify:
     ```python
     if is_scientifically_quarantined or mech_fam not in self.config.enabled_mechanisms:
         telemetry.decision = "ABSTAIN"
         telemetry.abstain_reason = "SCIENTIFIC_QUARANTINE"
         final_action = baseline_action
     ```
   - This ensures that under no circumstances can an unauthorized or quarantined mechanism commit an action to the game.
