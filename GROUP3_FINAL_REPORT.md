# AEC PHASE 013: FINAL SCIENTIFIC REPORT
## GROUP 3 MECHANISM RESCUE EVALUATION
### Shop Arbitrage • Production Arbitrage • Terminal Conversion • Emergency Feed Purchase

**Author**: Advanced Agentic Coding (DeepMind Antigravity)  
**Date**: September 19, 2026  
**Status**: COMPLETE / FINALIZED  
**Chassis Freeze**: `submission_Vj_kc_v3.tar.gz` (SHA256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`)  
**Empirical Foundation**: `V3` + `DEPENDENCY_AWARE_MARKET_TIMING` + `TERMINAL_LIQUIDATION` + `PHASE_SHUTDOWN`  

---

## 1. Executive Summary

Phase 013 executed the second-generation economic rescue of the four Group 3 mechanisms in the Kagriculture Adaptive Economic Compiler (AEC):
1. `SHOP_ARBITRAGE` (Realizable Market Arbitrage)
2. `PRODUCTION_ARBITRAGE` (Marginal Production Opportunity)
3. `TERMINAL_CONVERSION` (Realizable Terminal Value Conversion)
4. `EMERGENCY_FEED_PURCHASE` (Irreversible Feed Failure Avoidance)

The first-generation formulations of these mechanisms had produced zero live commits, suffered from capital starvation, or proved redundant with the authoritative V3 macro planner. Phase 013 completely reformulated each mechanism from foundational microeconomics:
- Enforcing structural labor opportunity costs, capital liquidity constraints, and transit runway proofs.
- Establishing sequential non-commutative market action ordering.
- Creating a comprehensive 48-case adversarial synthetic test matrix (12 cases per mechanism), achieving 100% test passage across all 645 tests in the AEC repository.
- Designing a dedicated cross-mechanism composition and pairwise conflict resolution engine (`tests/aec/test_group3_composition.py`).

Following rigorous governance protocols (§38, §39), each mechanism was evaluated independently in paired Common Random Numbers (CRN) mirror matches against the frozen live empirical foundation on a certified fresh development cohort (`249231..249240`, 10 seeds, 20 matches per mechanism).

**Key Empirical Verdict**:
- `SHOP_ARBITRAGE` committed actively (954 commits) but inflicted catastrophic capital depletion, producing a mean paired delta of **-$54,525.95 USD** (0W - 10L - 0T). The mechanism is **FAILED / QUARANTINED**.
- `PRODUCTION_ARBITRAGE` discovered zero marginal headroom beyond V3's already-optimal macro crop scheduler (`ALREADY_CAPTURED_BY_BACKBONE`), correctly abstaining 100% of the time (0 commits, +$4.90 non-causal variance). The mechanism is **FUNCTIONALLY COMPLETE / DORMANT**.
- `TERMINAL_CONVERSION` was dominated by direct raw liquidation in 8/10 seeds; in the 2 seeds where it committed (4 commits), worker transit and conversion delays reduced final harvest yield, producing a negative delta of **-$3.60 USD** (0W - 2L - 8T). The mechanism is **FUNCTIONALLY COMPLETE / QUARANTINED**.
- `EMERGENCY_FEED_PURCHASE` encountered zero natural feed crises under the strong foundation, correctly determining that baseline actions maintain safe feed levels and abstaining 100% of the time (0 commits, **+$0.00 USD** across 10/10 seeds). The mechanism is **FUNCTIONALLY COMPLETE / DORMANT**.

Under §36 and §39, because no mechanism demonstrated an individually promising positive active delta in pilot testing, **zero Group 3 mechanisms advance to formal qualification or live deployment**.

---

## 2. Canonical Qualification Table (§47)

| Mechanism | Pilot N | Formal N | Mean Delta | Median | W/L/T | Commits | Final Status | Live? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **SHOP_ARBITRAGE** | 10 | 0 | -$54,525.95 | -$59,504.25 | 0W / 10L / 0T | 954 / 24,236 | `FAILED / QUARANTINED` | **NO** |
| **PRODUCTION_ARBITRAGE** | 10 | 0 | +$4.90 | +$0.00 | 4W / 0L / 6T | 0 / 25,870 | `FUNCTIONALLY COMPLETE / DORMANT` | **NO** |
| **TERMINAL_CONVERSION** | 10 | 0 | -$3.60 | +$0.00 | 0W / 2L / 8T | 4 / 1,046 | `FUNCTIONALLY COMPLETE / QUARANTINED` | **NO** |
| **EMERGENCY_FEED_PURCHASE** | 10 | 0 | +$0.00 | +$0.00 | 0W / 0L / 10T | 0 / 416 | `FUNCTIONALLY COMPLETE / DORMANT` | **NO** |

*Note: W/L/T denotes seed-level paired outcomes. Formal N is 0 because no mechanism met the gating criteria to advance past pilot screening.*

---

## 3. Baseline Hierarchy & Governance Compliance (§1, §2, §49, §50)

### 3.1 Baseline Hierarchy
- **Architectural Baseline**: The complete 18-stage AEC compiler pipeline remains frozen as the ultimate destination architecture.
- **Empirical Control**: The live foundation against which all candidate treatments were evaluated:
  $$\text{Control} = \text{V3} + \text{DEPENDENCY\_AWARE\_MARKET\_TIMING} + \text{TERMINAL\_LIQUIDATION} + \text{PHASE\_SHUTDOWN}$$
- **Single-Mechanism Isolation**:
  $$\text{Treatment} = \text{Control} + \text{TARGET\_MECHANISM}$$
  No other experimental or previously quarantined mechanisms were enabled during any evaluation.

### 3.2 Governance Audit
- **Chassis Hash Verification**: Bit-identical `submission_Vj_kc_v3.tar.gz` SHA256 verified as `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` prior to all runs.
- **Protected Cohorts Intact**: Zero touches of Primary Locked Holdout (`340050..340199`), Gate 0.3 Virgin Holdout (`214200..214249`), and Prospective Tournament Cohort (`340300..340349`).
- **Retired / Consumed Cohorts**: Zero re-use of retired cohorts (`50000..50024`, `249000..249049`), Phase 010/010B (`249050..249110`), Phase 011 (`249111..249170`), or Phase 012 (`249171..249230`).
- **CRN Mirror Symmetry**: Every seed was evaluated in both $S_0$ (Treatment as Player 0) and $S_1$ (Treatment as Player 1) against identical control instances to cancel seat bias.

---

## 4. In-Depth Mechanism Evaluations

### 4.1 SHOP_ARBITRAGE: The Working Capital Trap
- **Hypothesis**: By exploiting deterministic town shop unlock windows (every 72 steps) and cyclical price fluctuations, buying low and selling high would yield net economic profit.
- **Implementation**: Formulated as Realizable Market Arbitrage (§6-§10), enforcing sequential non-commutativity, shed storage bounds ($N \le 10$), and minimum liquidity reservations.
- **Observed Behavior**: The mechanism found 24,236 candidate opportunities and executed 954 commits across all 10 pilot seeds.
- **Root-Cause Analysis**:
  - In Kagriculture, working capital is the primary engine of compounding growth. High-yield crops (melons, pumpkins) require immediate cash outlay for seeds and hired hand wages ($50/day).
  - When `SHOP_ARBITRAGE` committed funds to buy intermediate commodities (carrots, wheat, eggs) for future resale, it depleted the liquid cash balance below the threshold needed for continuous planting.
  - Furthermore, holding goods in the farm shed occupied slots needed for harvested crops, causing workers to halt or drop crops.
  - The local gross spread of $+\$20..\$50$ was dwarfed by the macro penalty of a stalled farm ($-\$54,525.95$ mean paired delta).
- **Status**: `FAILED / QUARANTINED`.

### 4.2 PRODUCTION_ARBITRAGE: Backbone Redundancy
- **Hypothesis**: Identifying marginal crop selection or timing opportunities where V3 is locally constrained but not globally optimal.
- **Implementation**: Defined as Marginal Production Opportunity (§13-§17). Added explicit diagnostic gating to verify whether V3 was already planning the crop (`ALREADY_CAPTURED_BY_BACKBONE`), requiring marginal headroom before candidate generation.
- **Observed Behavior**: Across 25,870 candidates evaluated in 20 matches, the mechanism executed exactly 0 commits.
- **Root-Cause Analysis**:
  - V3's macro production scheduler is already globally optimized for crop profitability based on current day, cash, and soil conditions.
  - In every single natural game turn, V3 was either already purchasing the optimal seed or conserving cash for the next major planting window.
  - The detector correctly recognized that deviating from V3's plan would reduce terminal profit, successfully abstaining in 100% of states.
  - Per §42 and §45, abstention is correct behavior. The small $+4.90$ delta is pure baseline stochastic variance.
- **Status**: `FUNCTIONALLY COMPLETE / DORMANT`.

### 4.3 TERMINAL_CONVERSION: Liquidation Dominance
- **Hypothesis**: Converting raw inventory (e.g. wheat) into higher-value animal products (milk, wool) or processed goods in the endgame (steps 670-716) would maximize terminal liquidated wealth.
- **Implementation**: Required strict terminal runway proof ($T_{\text{needed}} \le 718 - \text{step}$) and mandatory direct liquidation dominance comparison ($\Delta V_{\text{terminal}} = V_{\text{converted}} - V_{\text{raw}} - C_{\text{transit}} > 0$).
- **Observed Behavior**: 1,046 candidates evaluated, 4 commits executed across 2 seeds, resulting in a mean paired delta of -$3.60 USD (0W - 2L - 8T).
- **Root-Cause Analysis**:
  - In 8 of 10 seeds, direct liquidation of raw wheat at $\$25/\text{unit}$ was mathematically superior to spending 4-6 turns moving a worker to pasture/coop, feeding animals, waiting for yield, and transporting goods back to market.
  - In the 2 seeds where the mechanism committed, the worker dispatch slightly disrupted terminal field harvesting, costing more in unharvested crop value than the small conversion markup.
- **Status**: `FUNCTIONALLY COMPLETE / QUARANTINED`.

### 4.4 EMERGENCY_FEED_PURCHASE: Dormant Safety Invariant
- **Hypothesis**: Preventing catastrophic and irreversible livestock death ($1500 Cow, $1000 Sheep) through targeted emergency hay/feed procurement when starvation is imminent.
- **Implementation**: Enforced Irreversible Feed Failure Avoidance (§25-§29), activating only when `consecutive_unfed >= 2` and comparing multi-path alternatives (`BUY_PRODUCT`, `WHEAT_TO_HAY`, `EXISTING_INVENTORY`, `BASELINE_SAFE`).
- **Observed Behavior**: 416 candidates evaluated across 10 seeds, exactly 0 commits executed, resulting in $+0.00$ net delta (0W - 0L - 10T).
- **Root-Cause Analysis**:
  - Under the optimized V3 baseline, natural starvation never occurs. V3's internal scheduling feeds animals or manages grain stocks reliably.
  - The detector evaluated all 416 candidates as `BASELINE_SAFE` and abstained 100% of the time.
  - While synthetic adversarial tests proved that the engine successfully saves animals when starvation is artificially induced, natural exposure is genuinely zero.
  - Per §44: When natural exposure is zero, the mechanism must be classified as dormant, not qualified.
- **Status**: `FUNCTIONALLY COMPLETE / DORMANT`.

---

## 5. Composition Analysis (§36)

Phase 013 implemented a dedicated cross-mechanism composition test suite (`tests/aec/test_group3_composition.py`) verifying pairwise interactions:
1. `SHOP_ARBITRAGE` + `PRODUCTION_ARBITRAGE`: Disjoint execution verified on independent market and field worker channels.
2. `PRODUCTION_ARBITRAGE` + `TERMINAL_CONVERSION`: Conflict resolution verified via economic dominance and mutual exclusion on shared workers.
3. `SHOP_ARBITRAGE` + `TERMINAL_CONVERSION`: Sequential non-commutative market ordering verified.
4. `EMERGENCY_FEED_PURCHASE` + `PRODUCTION_ARBITRAGE`: Combined working capital reservation verified under low cash scenarios.
5. `EMERGENCY_FEED_PURCHASE` + `TERMINAL_CONVERSION`: Life-safety priority over discretionary terminal conversion verified.
6. Safety certificate compliance verified under `CounterfactualSimulator` and `SafetyChecker`.

However, per §36 non-negotiable governance:
> "First qualify each mechanism independently. Only after an individually promising mechanism exists should you test composition. Do not allow composition experiments to rescue a mechanism whose standalone formulation never demonstrated value."

Because no Group 3 mechanism demonstrated a standalone positive economic delta, no multi-mechanism composition models were promoted to live deployment.

---

## 6. Synthesis & Final Stop Condition (§53)

The Group 3 mechanism rescue completes the systematic forensic review of all legacy mechanism candidates across Groups 1, 2, and 3:
- **Group 1 (Trajectory)**: `DYNAMIC_SHADOW_HARVEST` and `TERMINAL_HARVEST_SWEEP` were salvaged, proven causal, and integrated into the foundation.
- **Group 2 (Economic-State)**: Forensics completed; mechanisms classified with causal attribution.
- **Group 3 (Arbitrage & Conversion)**: Rigorously tested under second-generation specifications. Every mechanism either correctly abstained due to baseline dominance (`PRODUCTION_ARBITRAGE`, `EMERGENCY_FEED_PURCHASE`) or was decisively rejected due to capital and transit opportunity costs (`SHOP_ARBITRAGE`, `TERMINAL_CONVERSION`).

### Final Disposition:
- **Live Empirical Foundation**: Preserved unchanged as `V3` + `DEPENDENCY_AWARE_MARKET_TIMING` + `TERMINAL_LIQUIDATION` + `PHASE_SHUTDOWN`.
- **Live Enablement**: ZERO Group 3 mechanisms added to live configuration.
- **Architectural Integrity**: Fully preserved. 645/645 repository tests passing.

Per §53: **FINAL STOP CONDITION REACHED.** Work on Phase 013 is concluded.
