# V44 League Tournament Benchmark Report

**Document ID:** `research/v44/reports/V44_LEAGUE_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `The-FOOL-00/kagriculture-economic-simulator`  
**Scope:** Full-lineage A/B tournament benchmark across 5 developmental ladders against 4 league opponents in both seat positions over unseen DEV seeds (`249685..249688`).

---

## 1. Executive Summary

In compliance with Sections 40, 41, and 51 of the V44 specification, we executed a comprehensive **160-leg A/B League Tournament** evaluating the full developmental lineage of Kagriculture controllers:
* **Ladder A:** V35 Baseline (Production Incumbent, deterministic choreography)
* **Ladder B:** V39 Targeted (Single-step terminal flush at Step 694)
* **Ladder C:** V42 Deterministic (Two-point 50/50 staggered liquidation at Steps 694 & 705)
* **Ladder D:** V43 Sequence Deterministic (Multi-point 40/60/Flush schedule at Steps 694, 705, 716)
* **Ladder E:** V44 Economic Strategy Portfolio (Defensive Payback Cutoff + Refined Staggered Liquidation)

### Key Benchmark Discoveries:
1. **Zero Casualties Maintained:** Across all validated candidate variants (V39, V42, V43, and V44 Refined), exactly **0 casualties** occurred across 160 competitive legs.
2. **Empirical Peak of Incremental Cash Alpha:**
   * Ladder C (V42-Det): **+$106.19** mean paired cash delta
   * Ladder D (V43-Seq Det): **+$98.25** mean paired cash delta
   * Ladder B (V39 Targeted): **+$82.31** mean paired cash delta
   * Ladder A (V35 Baseline): **$0.00**
3. **The Active Midgame Selling Trap:** Testing continuous midgame spot liquidation (Town Shop Arbitrage on Step % 4 == 0) caused a severe drop of **-$369.81**, proving that selling inventory before Step 690 violates the **Zero Carry Cost Invariant** of the Kagriculture engine.
4. **Defensive Cutoff Generalization:** Restricting candidate modifications to the **Step 520 Pre-Terminal Payback Cutoff** and **Staggered Order Book Pre-emption** preserves maximum value without inducing execution risk or capacity starvation.

---

## 2. Tournament Protocol & Governance

The tournament followed rigid competitive conditions:
* **Opponent Suite:**
  * `E8_DMITRII`: Aggressive terminal liquidator (dumps all inventory at Step 695).
  * `E2_A7`: Production mirror baseline executing pure A7 choreographies.
  * `E0_V3`: Conservative legacy agent with steady, risk-averse play.
  * `SYN_AGG`: Synthetic adversary with rapid early workforce and land expansion.
* **Paired Mirror Matches:** Every matchup was played as a paired 2-leg contest where the candidate and opponent swapped seats (Seat 0 as Player 1, Seat 1 as Player 2) on identical engine seeds.
* **Strict Holdout Protection:** The quarantined holdout seed ranges (`214200–214249`, `340090–340199`, `249695–249734`) were 100% untouched. All matches ran on clean DEV seeds (`249685..249688`).
* **Full-Terminal Accounting:** All games executed through the terminal step (Step 718/719). No proxy approximations or truncated horizons were permitted.

---

## 3. Full Tournament Results Matrix

The table below compiles the verified performance metrics stored in `research/v44/artifacts/ladder_tournament_results.json`:

| Ladder | Controller Description | Matchups | Total Legs | Win Rate (%) | Mean Cash Delta | Median Cash Delta | Casualties | Rescues |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Ladder A** | V35 Baseline (Incumbent) | 16 | 32 | 100.0% | $0.00 | $0.00 | 0 | 0 |
| **Ladder B** | V39 Targeted (Single Flush @ 694) | 16 | 32 | 100.0% | +$82.31 | +$64.50 | **0** | 0 |
| **Ladder C** | V42-Det (50/50 Staggered Flush) | 16 | 32 | 100.0% | **+$106.19** | +$63.00 | **0** | 0 |
| **Ladder D** | V43-Seq Det (40/60/Flush) | 16 | 32 | 100.0% | +$98.25 | +$62.00 | **0** | 0 |
| **Ladder E (Active)** | V44 Active (Midgame Arbitrage) | 16 | 32 | 100.0% | -$369.81 | -$260.50 | **0** | 0 |
| **Ladder E (Refined)**| V44 Refined (Cutoff + Staggered) | 16 | 32 | 100.0% | **+$98.31** | +$58.50 | **0** | 0 |

*Note: In all DEV seed matchups, V35 achieved a 100% win rate against the evaluation pool, meaning no baseline losses were available on this specific seed subset to trigger match rescues. Rescues were previously validated on the baseline-loss forensic cohort (Seed `249657` vs `E2_A7`, Seed `249659` vs `E8_DMITRII`).*

---

## 4. Head-to-Head Opponent Analysis

### 1. Versus `E8_DMITRII` (Terminal Dumper)
* **Mechanics:** `E8_DMITRII` hordes all farm yield and dumps its entire shed at Step 695.
* **Ladder Comparison:**
  * V35: Holds inventory into terminal window without selling; cash delta is baseline ($0).
  * V39: Sells at Step 694, pre-empting DMITRII's dump by 1 turn: **+$112.40** cash delta.
  * V42/V43/V44 Refined: Sells 40–50% at Step 694, absorbs DMITRII's crash, and sells remaining goods at Step 705 and 716: **+$148.50** cash delta.
* **Finding:** Staggered liquidation consistently dominates single-step dumping against market crash opponents by capturing residual liquidity after initial market recovery.

### 2. Versus `E2_A7` (Mirror Choreography)
* **Mechanics:** Plays the exact same deterministic opening and farm management as V35.
* **Ladder Comparison:**
  * Both agents generate identical farm production through Step 690.
  * At Step 694, candidate pre-emption sells shed inventory at clean, unperturbed market prices ($150–$210).
  * Realized Delta: **+$72.00 to +$94.00** across all seeds.
* **Finding:** In mirror games, any agent that realizes terminal shed inventory cleanly before Step 718 secures an insurmountable cash margin.

### 3. Versus `SYN_AGG` (Synthetic Aggressor)
* **Mechanics:** Rapidly purchases Land 2 and hires maximum farm hands early.
* **Ladder Comparison:**
  * `SYN_AGG` often over-expends working capital, entering cash crises during midgame maintenance.
  * V35 maintains high liquidity and steady production.
  * Candidates add **+$88.00 to +$115.00** by monetizing high-value wool and melon stocks late in the game.
* **Finding:** Conservative liquidity management strictly outperforms aggressive over-expansion.

### 4. Versus `E0_V3` (Conservative Legacy)
* **Mechanics:** Low-throughput legacy play, small animal holdings, minimal market participation.
* **Ladder Comparison:**
  * Candidates achieve **+$60.00 to +$78.00** delta purely from harvesting efficiency and late-stage liquidation.

---

## 5. Ablation Forensics: Why Midgame Interventions Degrade

A critical objective of V44 was to investigate why candidate economic strategies outside the terminal window failed to provide additive alpha.

### 1. The Zero Carry Cost Invariant
In Kagriculture, shed storage is unconstrained:
* No storage fee per item per turn.
* No inventory spoilage, deterioration, or theft.
* Zero capital tax on physical goods.

Consequently, holding physical inventory (Strawberries, Melons, Wool, Milk) in the shed has an economic carry cost of **exactly $0.00**.

### 2. The Price Depression Mechanism
When the candidate executes midgame spot selling (e.g. at Step 300, 400, or 500):
1. **Thin Order Book:** Midgame town demand absorbs only 1–2 units per cycle. Selling 3–5 units drives prices down from $200+ to < $100.
2. **Idle Cash Inefficiency:** The realized cash sits in the bank generating zero interest, while the farm has already reached its planned capital allocation.
3. **Compound Value Destruction:** By monetizing inventory midgame, the farm cannot capitalize on the large market price spikes that occur near the end of the episode when town demand accumulates.

### 3. Quantitative Ablation on DEV Cohort:
* **Terminal Staggered Flush Alone:** **+$98.25** mean delta
* **Flush + Spot Selling (Price > $200):** **+$90.31** (-$7.94 drop)
* **Flush + Late Scarcity Selling (650–680):** **+$71.69** (-$26.56 drop)
* **Flush + Continuous Midgame Selling:** **-$369.81** (-$468.06 net destruction)

---

## 6. Seat Position Asymmetry

Across all 160 tournament legs:
* **Seat 0 (Player 1):** Mean cash: **$11,842.10** | Win Rate: **100.0%**
* **Seat 1 (Player 2):** Mean cash: **$11,624.50** | Win Rate: **100.0%**
* **First-Mover Advantage:** Seat 0 enjoys a slight edge (+$217.60 mean cash) due to order of execution priority during simultaneous market transactions and tile interactions.
* **Candidate Invariance:** The cash delta delivered by the candidate over V35 was nearly identical in both seats:
  * Seat 0 Delta: **+$99.12**
  * Seat 1 Delta: **+$97.50**
  * This confirms that the portfolio's edge is mechanically robust to seat assignment.

---

## 7. Tournament Conclusion & Recommendation

1. **Hierarchy of Strength:**
   $$\text{V42-Det} \approx \text{V44 Refined} \approx \text{V43-Seq Det} > \text{V39 Targeted} \gg \text{V35 Baseline} \gg \text{V44 Active}$$
2. **Production Candidate Specification:**
   The production-ready candidate (`candidates/v44_economic_portfolio/main.py`) must strictly omit midgame spot selling and combine:
   * **Step 520 Pre-Terminal Payback Cutoff:** Safe capital shield preventing late un-amortized capital outlays.
   * **Staggered Order Book Pre-emption:** 40–50% at Step 694, 60–100% of remainder at Step 705, and 100% flush at Step 716.
3. **Governance Compliance:** Zero casualties, 100% win rate maintained, Golden Property verified across turns 0..692.
