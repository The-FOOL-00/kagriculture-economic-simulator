# AEC V1.1 Preregistration: Foundation Mechanism Activation and Evaluation Protocol

**Preregistration Protocol:** PREREG-AEC-V1.1-20260917
**Date:** 2026-09-17
**Status:** PREREGISTERED & FROZEN
**Target Milestone:** AEC V1.1 Mechanism Activation (Development Phase)
**Parent Study:** EXP-AEC-001 (Audit Verdict: Valid Non-Inferiority, Dormant Treatment)

---

## 1. Scientific Governance & Anti-Tuning Declaration

Under strict scientific governance, this development cycle adheres to the following immutable constraints:
1. **No Prospective Cohort Tuning:** Prospective cohort seeds `340000`–`340049` were **not** used to tune thresholds, horizons, or parameters.
2. **Holdout Non-Consumption:** Seeds `340050`–`340199` remain strictly locked, unexecuted, and uninspected.
3. **Frozen Backbone Immutability:** `submission_Vj_kc_v3.tar.gz` (SHA256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`) remains untouched and frozen.
4. **No Rewriting into Route-Replay:** AEC remains an economic IR and coupled patch compiler over the V3 backbone.
5. **No Outcome-Driven Parameter Search:** Parameters, horizons, and valuation weights are derived strictly from verified game economics before outcome evaluation.

---

## 2. Formal Hypotheses

### H1 (Market Order Frontload Semantic Alignment)
Enforcing that `FRONTLOAD_ORDERS` triggers only when an actual `SELL` order exists and succeeds non-sell orders will eliminate 100% of false-positive opportunities on capital-only order sets while preserving genuine frontload opportunities.

### H2 (Downstream Weed Removal Asset Valuation)
Evaluating `LOCAL_WEED_DIG` via explicit downstream execution benefit (unblocking planned `PLANT` or `BUILD` tasks) minus grounded labor opportunity cost ($C_{\text{labor}} = \text{fib\_hire\_cost}(\text{hires\_today}) / 24.0$) enables the counterfactual evaluator to certify weed digging when economically justified, while abstaining when digging has no downstream utility, without artificially lowering cash or margin thresholds.

### H3 (State-Driven Adaptive Horizon Selection)
Mechanism-specific adaptive horizons derived from downstream dependency step offsets and opponent market pressure provide sufficient lookahead to capture true economic deltas while keeping compute within per-turn latency bounds ($< 100$ ms).

### H4 (Defense-in-Depth Characterization)
`TERMINAL_LIQUIDATION` and `PHASE_SHUTDOWN` are redundant with V3's primary line during standard gameplay, but will reliably activate, pass safety, and commit in synthetic reachability states where baseline actions contain unliquidated inventory or obsolete seed purchases.

---

## 3. Fixed Economic Formulas and Constants

All economic terms are derived from verified engine mechanics (`sim.hpp` / `config.py`):

### 3.1 Labor Opportunity Cost
$$\text{Cost}_{\text{labor}} = \frac{\text{fib\_hire\_cost}(\text{hires\_today})}{\text{TURNS\_PER\_DAY}} = \frac{\text{fib}(\text{hires\_today})}{24.0} \text{ per worker-step}$$
- Idle worker turn (`PASS`): measured replacement floor ($\approx \$0.0417$ at baseline).
- Displaced transit (`MOVE`): route delay replacement cost.
- Displaced productive task (`PLANT`, `WATER`, `HARVEST`): task value ($\ge \$25.00$).

### 3.2 Downstream Weed Removal Asset Value
$$\text{WEED\_VALUE} = B_{\text{downstream}} - C_{\text{labor}}$$
where:
$$B_{\text{downstream}} = \begin{cases}
\max\left(0, \text{Yield}(c) \times P_{\text{market}}(c) - \text{SeedPrice}(c)\right) & \text{if future } \text{PLANT}(c) \text{ on tile is unblocked and feasible} \\
\$50.0 & \text{if future structure BUILD on tile is unblocked} \\
\Delta \text{RouteSteps} \times C_{\text{labor}} & \text{if movement detour is eliminated} \\
0.0 & \text{if no downstream dependency exists}
\end{cases}$$

Exact Biological, Operational, and Terminal Feasibility Conditions:
$$s_{\text{plant}} = s_{\text{current}} + \text{offset}_{\text{dep}}$$
$$s_{\text{mature}} = s_{\text{plant}} + \text{GrowthDays}(c) \times 24 \le 718$$
$$\text{Operational Feasibility}: \text{farm.seeds}[c] > 0 \lor \text{farm.cash} \ge \text{SeedPrice}(c)$$
If $s_{\text{mature}} > 718$ or operational check fails, $B_{\text{downstream}} = 0.0 \implies \text{WEED\_VALUE} < 0$.

### 3.3 Route-Tape Spatial Consistency Guard (§7, §8)
Candidate rollout verifies candidate worker coordinates against baseline rollout history at every offset $\ge 1$. If coordinates diverge on spatial commands (`MOVE` or tile operations), continuation commands are truncated to `PASS`, marking `spatial_consistency_ok = False` and failing closed.

### 3.4 Official Market Pricing (§10)
Simulator market order resolution executes unit-by-unit in lockstep using official engine function `compute_market_price(item, inventory)`. Toy price formulas are forbidden.

### 3.5 WinModel Heuristic Score
$$P_{\text{win\_heuristic}} = \frac{1}{1 + \exp\left(-\frac{\text{CurrentGap} + \Delta \text{TerminalMargin}}{1000.0}\right)}$$
*Preregistered Note:* This is an uncalibrated ranking score for candidate tie-breaking, not an empirical probability.


---

## 4. Fixed Mechanism Horizon Policy Rules

| Mechanism Family | Trigger / State Feature | Assigned Horizon $H$ | Deterministic Rationale |
|---|---|---|---|
| `LOCAL_WEED_DIG` | Downstream dependency at offset $s_{\text{dep}}$ | $\min(\text{rem}, \max(6, s_{\text{dep}} + 3))$ | Captures dependent action and verification |
| `LOCAL_WEED_DIG` | No downstream dependency | $\min(\text{rem}, 6)$ | Fast rejection of non-beneficial dig |
| `FRONTLOAD_ORDERS` | Opponent market activity present | $\min(\text{rem}, 18)$ | Normal horizon captures lockstep market pricing |
| `FRONTLOAD_ORDERS` | No opponent market activity | $\min(\text{rem}, 6)$ | Short horizon for local reordering |
| `TERMINAL_LIQUIDATION` | Any | $\min(\text{rem}, 2)$ | Terminal-local liquidation executes immediately |
| `PHASE_SHUTDOWN` | Any | $\min(\text{rem}, 6)$ | Phase-local verification of seed purchase avoidance |
| Any Mechanism | Remaining game steps $\le 1$ | $1$ | Terminal game boundary |

---

## 5. Preregistered Test Fixtures and Success Criteria

### 5.1 Verification Categories (A through J)
1. **Category A:** Market Analyzer Correctness (Cases 1–6 passing).
2. **Category B:** Weed Valuation Correctness (Benefit unblocking passing; cost $>$ benefit rejected).
3. **Category C:** Mechanism Horizon Policy (Deterministic state-driven horizons).
4. **Category D:** Patch Generation (Correct mutations for all 4 families).
5. **Category E:** Simulation Deltas (Exact money and margin calculations).
6. **Category F:** Safety Rejections (Legality, negative cash, overflow rejected).
7. **Category G:** Commit-Gate Correctness (Certified superior candidate committed).
8. **Category H:** Abstention Correctness (Inferior/equal candidate falls back to baseline).
9. **Category I:** Determinism Replay (Exact identical bitwise output on state replay).
10. **Category J:** Action-Divergence Invariant (Exact baseline identity across all 7 conditions).

### 5.2 Mandatory Success Criteria
1. FRONTLOAD_ORDERS false-positive bug is fixed and tested.
2. FRONTLOAD_ORDERS produces genuine causal commit under rival dump using official market pricing.
3. LOCAL_WEED_DIG has explicit downstream valuation with grounded replacement labor costs and terminal cutoffs.
4. Route-tape spatial consistency guard prevents stale continuation execution.
5. Positive synthetic fixtures commit for all 4 mechanisms.
6. Negative synthetic fixtures abstain for all 4 mechanisms.
7. 100% pass rate on all existing AEC unit tests (84/84).
8. 100% pass rate on new V1.1 activation suite (29/29).
9. 100% pass rate on development fixes test suite (18/18, total 102 passing tests).
10. Frozen V3 tarball hash remains identical (`845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`).
11. Zero holdout seeds touched or executed.
12. Telemetry records full per-candidate diagnostic trace (`CandidateTelemetry`), separating realized from projected values.

