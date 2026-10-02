# V52 — Herd Composition + Early Liquidity + Barn Bottleneck Research: Final Report

**Cycle**: V52  
**Baseline**: `V49_RETAIN` (SHA256: `8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11`)  
**Status**: COMPLETE  
**Governance Outcome**: **`V49_RETAIN`** (Mandatory Retain Decision)

---

## 1. Executive Summary & Core Research Question

### The Core Research Question
> *Does V49's fixed economic composition (8 Cows, 6 Sheep, 3 Geese) and early-game capital allocation structurally leave money or win-rate on the table against the current elite meta, and can targeted patches to early liquidity float or barn entrance bottlenecks rescue remaining losses?*

### The Empirical Findings
1. **The Early Liquidity Hypothesis is Decisively Refuted**:
   - Injecting shadow liquidity float (+$500 to +$1,800) at Step 1 produced an **exact $0.00 delta** across all 11 historical V49 losses against V44, and an out-of-sample fresh ladder delta of -$60.97 (within bootstrap CI).
   - V49 executes deterministic pre-compiled action sequences; it never fails planned purchases due to cash starvation. Extra capital sits idle in the bank without altering production timing.
2. **The Barn Bottleneck Hypothesis is Decisively Refuted**:
   - Turn-by-turn physical telemetry revealed exactly **0 blocked unit-turns** at the barn door under Route 0.
   - Static choreographic paths are collision-free by construction. Local shed reservations and entrance priority tweaks produced an **exact $0.00 delta** across all 11 historical loss matches and all 576 fresh ladder legs.
3. **The True Causal Root of the V44 Loss Cluster**:
   - The major ~$1,400 loss cluster against V44 (losses L07..L10 on seeds 250436 and 250439) is **not** caused by V44's early liquidity or Step-36 Goose Arbitrage.
   - It is caused by **V49's own `COWSWAP` overlay** (lines 5534–5772 in `candidates/v49_meta_fusion/main.py`) triggering at Step 150. On seeds where egg shops open without milk shops, COWSWAP overrides Route 0's planned purchase of `['BUY_ANIMAL', 'COW', 2]` and forces coop construction for low-margin eggs ($50) rather than high-margin milk ($160).
   - While suppressing COWSWAP rescues L07..L10 (+3,854 on 250436, +$2,825 on 250439), globally suppressing it causes **30 casualties** across discovery seeds and **4 fresh casualties** out-of-sample on the 9-opponent ladder (-$158.02 mean delta, -$448.76 elite delta).
4. **Herd Scaling Architectural Constraint**:
   - Transplanting external public herd sizes (e.g. `9C + 4S + 1W + 10H` from Nishchal Jain / Top-30 meta) onto V49's 2945 choreography causes massive performance collapses (-$10,041 to -$48,722 mean delta, 0% WR). The 2945 chassis relies on exact physical synchronization between unit locations and animal positions; altering animal counts desynchronizes worker paths and wastes dozens of unit turns.

---

## 2. Governance Audit & Holdout Integrity

- **Frozen Candidates**: `v44_economic_portfolio`, `v47_elite_transfer`, `v48_challenger`, `v49_meta_fusion`, `v50_dead_action_guard`, `v51_blocked_repair`. None were modified.
- **Quarantined Virgin Holdouts**:
  - `214200–214249` (0 seeds accessed)
  - `340090–340199` (0 seeds accessed)
  - `249695–249734` (0 seeds accessed)
- **Kaggle Submissions**: Exactly 0.

---

## 3. External Mechanism & Public Meta Teardown

All external claims were independently audited and reproduced against our exact local simulation engine:

1. **Nishchal Jain Herd Findings**:
   - *Public Claim*: Livestock mix matters far more than total headcount due to CARE multiplier mechanics.
   - *Engine Reproduction*: Verified. A 1.25x CARE multiplier rewards diverse animal species, but only when workers can service them synchronously. On a pre-compiled static tape (V49), workers cannot dynamically switch to unscheduled animals.
2. **Rayk Kretzschmar Early Liquidity (Wheat Wash)**:
   - *Public Claim*: Step 0 wheat wash (50/50 -> 25/25 -> 20/15) provides critical early liquidity float.
   - *Engine Reproduction*: In dynamic routing architectures, early liquidity unlocks earlier farm-hand purchases. In V49, farm-hand purchases are hardcoded at fixed steps; excess cash remains idle.
3. **Barn Entrance Spatial Congestion**:
   - *Public Claim*: Shed-adjacent bottleneck `(4,4)`-`(5,5)` chokes delivery throughput.
   - *Engine Reproduction*: In dynamic A* routers, door collisions cause 12-18 lost turns. In V49, pre-compiled unit paths stagger arrivals, resulting in 0 door collisions.

---

## 4. V49 Baseline Economic Telemetry

Across discovery seeds `[250400..250409]` $\times$ 2 seats (20 matches):
- **Mean Terminal Capital**: **$93,312.75** (Std: $15,860.10)
- **Midday Capital Milestones**:
  - Step 72: $1,280.00
  - Step 144: $2,840.00
  - Step 216: $7,120.00
  - Step 288: $14,960.00
  - Step 360: $27,450.00
  - Step 432: $44,820.00
  - Step 504: $64,110.00
  - Step 576: $78,940.00
  - Step 648: $89,150.00
  - Step 719: $93,312.75
- **Herd Acquisition Milestones**:
  - Cows: 2 at Step 150, 2 at Step 180, 2 at Step 210, 2 at Step 240 (Total: 8)
  - Sheep: 2 at Step 270, 2 at Step 300, 2 at Step 330 (Total: 6)
  - Geese: 1 at Step 360, 2 at Step 390 (Total: 3)

---

## 5. Liquidity Forensics & Historical Loss Rescues (Section 13)

We analyzed all 11 historical V49 losses against V44 under 8 intervention regimes:

| Loss ID | Seed:Seat | Category | V49 Baseline | Herd Patch | Liq Patch (+$1.4k) | Barn Patch | Full Candidate | Result |
|---|---|---|---|---|---|---|---|
| **L01** | `250416:0` | Barn/Macro | -$716.00 | -$1,850.00 | -$716.00 | -$716.00 | -$1,850.00 | Worsened (-$1,134.00) |
| **L02** | `250416:1` | Barn/Macro | -$716.00 | -$1,850.00 | -$716.00 | -$716.00 | -$1,850.00 | Worsened (-$1,134.00) |
| **L03** | `250428:0` | Late Crop/Timing | -$31.00 | -$31.00 | -$31.00 | -$31.00 | -$31.00 | Inert ($0.00) |
| **L04** | `250428:1` | Late Crop/Timing | -$160.00 | -$160.00 | -$160.00 | -$160.00 | -$160.00 | Inert ($0.00) |
| **L05** | `250433:0` | Route Branch | -$470.00 | -$470.00 | -$470.00 | -$470.00 | -$470.00 | Inert ($0.00) |
| **L06** | `250433:1` | Route Branch | -$470.00 | -$470.00 | -$470.00 | -$470.00 | -$470.00 | Inert ($0.00) |
| **L07** | `250436:0` | COWSWAP/Herd | -$1,405.00 | **+$2,449.00** | -$1,405.00 | -$1,405.00 | **+$2,449.00** | **RESCUED (+3,854.00)** |
| **L08** | `250436:1` | COWSWAP/Herd | -$1,405.00 | **+$2,449.00** | -$1,405.00 | -$1,405.00 | **+$2,449.00** | **RESCUED (+3,854.00)** |
| **L09** | `250439:0` | COWSWAP/Herd | -$1,407.00 | **+$1,418.00** | -$1,407.00 | -$1,407.00 | **+$1,418.00** | **RESCUED (+2,825.00)** |
| **L10** | `250439:1` | COWSWAP/Herd | -$1,407.00 | **+$1,418.00** | -$1,407.00 | -$1,407.00 | **+$1,418.00** | **RESCUED (+2,825.00)** |
| **L11** | `250497:1` | Route Branch | -$901.00 | -$901.00 | -$901.00 | -$901.00 | -$901.00 | Inert ($0.00) |

---

## 6. Fresh Out-of-Sample Ladder Benchmark (Section 15)

Evaluated across 32 strictly disjoint fresh seeds `[250600..250631]` $\times$ 2 seats $\times$ 9 opponents (**576 paired legs per candidate**, 2,304 total 719-step matches):

| Candidate Key | Description | Total Legs | Mean Delta vs V49 | 95% Bootstrap CI | Overall WR | Rescues | Casualties | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **V49_Meta_Fusion** | Champion Baseline | 576 | +$0.00 | [+$0.00, +$0.00] | **99.31%** (572/576) | 0 | 0 | **RETAINED** |
| **V52_COWSWAP_Suppression** | Suppress COWSWAP | 576 | -$158.02 | [-$294.69, -$28.07] | 98.61% (568/576) | 0 | **4** | **REJECTED** |
| **V52_Liquidity_Float** | +$1,400 Shadow Float | 576 | -$60.97 | [-$204.56, +$55.23] | 99.31% (572/576) | 0 | 0 | **REJECTED** |
| **V52_Barn_Priority** | Barn Entrance Priority | 576 | +$0.00 | [+$0.00, +$0.00] | 99.31% (572/576) | 0 | 0 | **REJECTED** |

### Per-Suite Performance:
- **Elite Suite (384 legs)**:
  - `V49_Meta_Fusion`: Mean Delta $0.00, WR **98.96%** (380/384)
  - `V52_COWSWAP_Suppression`: Mean Delta **-$448.76**, WR **97.92%** (376/384, 4 casualties against V44)
  - `V52_Liquidity_Float`: Mean Delta -$91.45, WR 98.96%
  - `V52_Barn_Priority`: Mean Delta $0.00, WR 98.96%
- **Adversarial Suite (192 legs)**:
  - `V49_Meta_Fusion`: WR **100.00%** (192/192)
  - `V52_COWSWAP_Suppression`: WR **100.00%** (192/192)
  - `V52_Liquidity_Float`: WR **100.00%** (192/192)
  - `V52_Barn_Priority`: WR **100.00%** (192/192)

---

## 7. Promotion Gate Audit (Section 16)

| # | Criterion | Required Threshold | Observed Value | Pass / Fail |
|---|---|---|---|---|
| 1 | Disjoint Fresh Seeds | 32 seeds `[250600..250631]` | Verified disjoint | **PASS** |
| 2 | Holdout Integrity | Zero holdout seeds accessed | 0 holdouts accessed | **PASS** |
| 3 | Opponent Suite | 9 opponents (6 elite + 3 adv) | 9 opponents evaluated | **PASS** |
| 4 | Paired Mean Delta vs V49 | Strict positive delta (> +$0.00) | -$158.02 (Herd), -$60.97 (Liq), $0.00 (Barn) | **FAIL** |
| 5 | Bootstrap 95% CI | Strictly excludes zero on positive side | CI includes negative territory | **FAIL** |
| 6 | Overall Win Rate | $\ge$ V49 Win Rate (99.31%) | 98.61% (Herd), 99.31% (Liq, Barn) | **FAIL** |
| 7 | Zero Casualties | Exactly 0 casualties vs baseline | **4 casualties** on Herd patch | **FAIL** |
| 8 | Elite Suite Delta & WR | Elite $\Delta \ge 0$, WR $\ge$ 98.96% | -$448.76, WR 97.92% | **FAIL** |
| 9 | Adversarial Suite WR | 100.00% across 192 legs | 100.00% | **PASS** |
| 10 | Clean Causal Mechanism | Mechanistic proof without ad-hoc overfit | Hypotheses decisively falsified | **PASS** |

**Promotion Verdict**: All candidate modifications FAIL promotion criteria 4, 5, 6, 7, and 8.  
**Mandatory Decision**: **`V49_RETAIN`**.

---

## 8. Checklist of All 18 Required Artifacts (Section 18)

Every required artifact for the V52 cycle has been generated and validated:

1. [public_mechanisms.json](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/external/public_mechanisms.json): Audited public mechanisms across 5 community architectures.
2. [PUBLIC_HERD_META.md](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/external/PUBLIC_HERD_META.md): Deep-dive into Nishchal Jain's herd teardown and care multipliers.
3. [EARLY_LIQUIDITY_META.md](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/external/EARLY_LIQUIDITY_META.md): Analysis of wheat wash and early liquidity float lineages.
4. [BARN_BOTTLENECK_META.md](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/external/BARN_BOTTLENECK_META.md): Spatial physics and door congestion dynamics.
5. [v49_economic_profile.json](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/baseline/v49_economic_profile.json): V49 turn-by-turn economic telemetry data.
6. [v49_economic_profile.md](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/baseline/v49_economic_profile.md): V49 baseline economic analysis report.
7. [V44_STEP36_LIQUIDITY_FORENSICS.md](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/losses/V44_STEP36_LIQUIDITY_FORENSICS.md): Complete forensics on V44-linked losses and shadow float tests.
8. [v52_liquidity_sweep.json](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/counterfactuals/v52_liquidity_sweep.json): Capital sweep and liquidity counterfactual records.
9. [v49_barn_congestion.json](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/barn/v49_barn_congestion.json): Spatial coordinate telemetry at shed entrance.
10. [v49_barn_congestion.md](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/barn/v49_barn_congestion.md): Barn door congestion report showing 0 blocked moves.
11. [v52_barn_sweep.json](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/counterfactuals/v52_barn_sweep.json): B1..B6 barn coordination counterfactual results.
12. [v52_herd_sweep.json](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/counterfactuals/v52_herd_sweep.json): Cow/Sheep composition grid sweep.
13. [v52_interaction_matrix.json](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/counterfactuals/v52_interaction_matrix.json): 28-seed discovery interaction evaluation.
14. [v49_loss_counterfactuals.json](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/losses/v49_loss_counterfactuals.json): 8-regime counterfactual records across L01..L11.
15. [V49_LOSS_COUNTERFACTUALS.md](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/losses/V49_LOSS_COUNTERFACTUALS.md): Detailed loss rescue and regression report.
16. [v52_fresh_ladder.json](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/benchmarks/v52_fresh_ladder.json): 576-leg fresh out-of-sample ladder benchmark dataset.
17. [V52_FINAL_LADDER.md](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/reports/V52_FINAL_LADDER.md): Comprehensive ladder benchmark breakdown and per-opponent tables.
18. [V52_FINAL_REPORT.md](file:///c:/Users/Sundareswaran/Kagriculture/research/v52/reports/V52_FINAL_REPORT.md): This grand synthesis report.

---

## 9. Final Conclusion & Strategic Guidance

The V52 research program has definitively mapped the boundaries of V49's architecture:
1. **The 2945 Choreographic Chassis is an Integrated Whole**:
   Livestock counts, unit pathing, harvest timing, and sale priorities form a tightly coupled, highly synchronized mechanism. Isolating and modifying livestock counts (e.g. attempting to mimic public 9C+4S or Top-30 herds) without re-synthesizing the physical worker paths severely destabilizes the choreography.
2. **Early Liquidity Does Not Constrain V49**:
   V49's action tapes are pre-scripted and capital-sufficient; excess liquidity provides zero leverage.
3. **Barn Entrance Jamming is a Myth in Route 0**:
   Pre-compiled paths eliminate simultaneous door contention.
4. **V49 Remains the Undisputed Sovereign Baseline**:
   Across 576 fresh out-of-sample legs against 6 elite public agents and 3 adversarial stresses, `V49_Meta_Fusion` achieved a **99.31% overall win rate** and **100.0% adversarial win rate**.

`V49_RETAIN` is firmly reaffirmed as the canonical baseline.
