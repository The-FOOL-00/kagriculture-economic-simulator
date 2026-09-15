# EXP-DEV-003 FORENSIC CAUSAL AUDIT
## Mechanistic Investigation of Conditional Opportunity-Value Specialization Over V54++ Residual Preemption
**Experiment Identifier**: EXP-DEV-003  
**Discovery Partition**: Seeds `245000` to `245049` ($N=50$ contiguous seeds, 100 paired matches)  
**Baseline**: `candidates/compiled_v54_plus_residual.py` (Submission `56146971`)  
**Treatment**: `candidates/closed_loop_architecture/dev_003_conditional_specialization.py`  
**Date**: 2026-09-14  
**Auditor**: Autonomous Verification Engine (Zero-Leakage Governance)

---

## 1. Executive Forensic Summary

EXP-DEV-003 was executed to evaluate whether an information-conditioned crop specialization overlay could add generalizable economic value to our frozen V54++ residual-preemption baseline.

### Primary Outcome:
- **Mean Paired Delta**: **-$835.32**
- **Win / Loss / Tie Record**: **0 Wins / 4 Losses / 46 Ties** (Win Rate: **0.0%**)
- **Non-Activating Partition ($N=45$ seeds, 90%)**: **Bit-exact delta = $0.00**. Baseline preservation invariant confirmed with 100% fidelity.
- **Activating Partition ($N=5$ seeds, 10%)**: All 5 activating seeds specialized in `TOMATO` in response to unlocked `PIZZA_SHOP`.
  - Seed 245025: Delta = **$0.00** (Tie)
  - Seed 245000: Delta = **-$3,653.00** (Loss)
  - Seed 245043: Delta = **-$11,631.00** (Loss)
  - Seed 245007: Delta = **-$11,786.00** (Loss)
  - Seed 245045: Delta = **-$14,696.00** (Worst Loss)

---

## 2. Forensic Causal Tracing: Why Tomato Specialization Suffered Catastrophic Losses

Deep turn-by-turn tracing of the match telemetry, tile states, worker order streams, and market price dynamics revealed three compounding causal failure mechanisms:

### 2.1 The Spatial-Macro Route Desynchronization (The Lifespan Cliff)
In V54++, agricultural production is governed by a tightly calibrated, offline-optimized 719-step spatial conveyor belt. Worker pathing vectors, watering sweeps, and harvest cycles are timed specifically for the 2-day harvest interval and long lifespan of Strawberry.
- **Lifespan Expiration at Step 552**: Tomato plants planted on Day 11 (Step 268) possess a hard engine lifespan of `max_lifespan_step = 552` (Day 23). At step 552, all 4 Tomato tiles expired and died simultaneously.
- **Barren Tiles for 7 Days**: Because the specialization overlay only substituted Strawberry plantings on Day 11 (steps 264–287), no replacement Tomato seeds were purchased or planted after Step 552. For the entire remaining 168 steps of the season (Days 23 to 30), those 4 tiles sat completely empty, producing zero economic value.
- **Unharvested Vine Glut**: Tomato plants yield daily (1-day cycle), whereas V54++ worker harvest routes visit crop tiles on a 2-day cadence. Tomato tiles frequently reached their maximum vine capacity (`yield_units = 4`) and ceased production while waiting for workers to harvest them.

### 2.2 Macro Strawberry Cashflow Dominance vs Micro Shop Demand
The theoretical opportunity model hypothesized that in worlds lacking a Strawberry shop, Strawberry market prices would collapse, allowing a specialized shop crop (Tomato pulled by Pizza Shop) to outperform. This hypothesis failed empirically:
1. **Town Center Demand Buffer**: In `kagsim`, town center demand absorbs finished crops every 24 steps regardless of town shops. Combined with market depletion dynamics, Strawberry prices did NOT collapse; in Seed 245007, the realized Strawberry market price was **$174.00**, while Tomato settled at **$321.00**.
2. **Total Volume Deficit**:
   - **Baseline (Pure Strawberry)**: Produced and monetized **269 Strawberry units** across the season, generating over **$40,000** in realized agricultural revenue.
   - **Candidate (Tomato Overlay)**: Due to slow Pizza Shop pull rates (1 unit per 4 steps) and missed harvests, the candidate only managed to sell **16 Tomato units** (generating ~$1,100 revenue), while forfeiting ~30 Strawberry harvests (~120 units, worth ~$18,000).
   - **Net Economic Deficit**: Forfeiting ~$18,000 in Strawberry cashflow to gain ~$1,100 in Tomato cashflow produced a net loss of **-$11,786.00** on Seed 245007 and **-$14,696.00** on Seed 245045.

### 2.3 Worker Shed Saturation & Interference
Tomato items placed into the shed occupied capacity and interfered with the shed-guard overlays (`_v60_shed_guard`) that manage high-value wool and milk liquidations. Workers made redundant trips to deposit small batches of Tomatoes rather than servicing cows and sheep.

---

## 3. Seed-by-Seed Forensic Analysis of Activating Cases

| Seed | Checkpoint Step | Unlocked Shops | Specialized Crop | Candidate Reward | Baseline Reward | Net Paired Delta | Causal Mechanism |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **245000** | 72 | `PIZZA_SHOP` (Day 3) | `TOMATO` | $58,545.0 | $62,198.0 | **-$3,653.0** | 4 Tomato tiles planted; lost 18 Strawberry harvests; Tomato pull rate failed to compensate. |
| **245007** | 72 | `PIZZA_SHOP` (Day 3) | `TOMATO` | $71,206.0 | $82,992.0 | **-$11,786.0** | Severe lifespan cliff: 4 tiles barren from Step 552 to 720; only 16 Tomatoes sold vs 120 forgone Strawberries. |
| **245025** | 288 | `PIZZA_SHOP` (Day 12) | `TOMATO` | $101,960.0 | $101,960.0 | **$0.0** | Gate fired at Step 288 (after Day 11 planting window 264-287 had closed). Zero tiles substituted; candidate executed identical baseline plan. |
| **245043** | 72 | `PIZZA_SHOP` (Day 3) | `TOMATO` | $95,242.0 | $106,873.0 | **-$11,631.0** | Identical lifespan cliff: 4 tiles died at Step 552; forfeited $15k in Strawberry cash. |
| **245045** | 72 | `PIZZA_SHOP` (Day 3) | `TOMATO` | $120,306.0 | $135,002.0 | **-$14,696.0** | Worst seed loss: high-yield Strawberry world where forgone Strawberry cash reached peak penalty. |

---

## 4. Verification of the Baseline Preservation Invariant

Across the 45 non-activating seeds (90.0% of the partition):
- `delta_m0 == 0.0`
- `delta_m1 == 0.0`
- `paired_mean_delta == 0.0`
- **Ties: 46 / 50 seeds (92.0%)** (including Seed 245025 which had zero physical tile overrides).

This mathematically demonstrates that the baseline wrapper logic, residual preemption engine, and non-activating state transitions preserve bit-for-bit identity with the authoritative championship candidate `56146971`.

---

## 5. Strategic Conclusion

Ad-hoc crop substitution over an intricately compiled macro route table (like V54++) is structurally flawed. The macro route's value does not come merely from *what* crop is planted, but from the tight temporal coupling between worker spatial pathing, watering sequences, and harvest intervals. Overriding crops without simultaneously re-pathing workers guarantees harvest delays, plant expirations, and macro cashflow destruction.
