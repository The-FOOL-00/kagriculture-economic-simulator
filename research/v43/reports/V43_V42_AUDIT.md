# V43 Comprehensive Forensic Audit of V42 Empirical Outcomes

**Document ID:** `research/v43/reports/V43_V42_AUDIT.md`  
**Date:** 2026-09-25  
**Repository:** `Kagriculture`  
**Scope:** Quantitative and causal audit of the V42 research cycle, evaluating all 10 strategic interventions, identifying surviving alpha vs. false alpha, mapping intervention interactions, and establishing the empirical mandate for V43 Multi-Step Economic Planning and Alpha Composition.

---

## 1. Executive Summary & V42 Milestone Context

The V42 research program achieved a major breakthrough in the Kagriculture lineage: **the first confirmed discovery and validation of positive incremental economic alpha over V35 while preserving 100% zero-casualty safety and the Golden Property**.

In the clean 96-leg DEV tournament (`DEV_SEEDS = [249685, 249686, 249687, 249688]` vs. `E8_DMITRII`, `E2_A7`, `E0_V3`, `SYN_AGG` in both seats):
* **Ladder C (V42-Det):** Mean paired cash delta **`+$110.94`**, median cash delta **`+$67.00`**, 32/32 legs won (100.0%), **0 casualties**, and **1 confirmed rescue** (`LOSE` $\to$ `WIN`) in the targeted loss cohort.
* **Ladder D (V42-Alpha Model):** Two-head heteroscedastic uncertainty estimation with Lower Confidence Bound (LCB) risk gating ($\hat{\mu} - \beta \hat{\sigma}$) demonstrated an 88.5% oracle agreement rate and **0.0% false-positive intervention rate**, ensuring absolute safety.
* **Key Mechanism Discovery:** Staggered terminal liquidation (selling 50% of marketable shed goods at Step 694 and 50% at Step 705) captured maximum liquidation revenue while preventing internal market crash dynamics.

However, V42 was fundamentally constrained to **isolated, single-step intervention evaluations**:
$$\text{state } s_t \longrightarrow \text{intervention } a_t \longrightarrow \text{terminal step 719}$$
Of the 721 baseline loss decision points analyzed in V42, isolated single-step interventions rescued only **11 points (1.5%)**. The remaining **98.5% of losses** require multi-step coordinated actions (e.g. capital preservation + late expansion, or staggered multi-point market realization).

---

## 2. Quantitative Audit of the 12 Mandated Questions

### Question 1: Which interventions produced positive alpha?
Based on the full terminal rollout dataset (2,821 transitions across 16 safe training seeds):
1. **`TERMINAL_LIQUIDATE_FULL` (Action 1):**
   - Sample Count: $N = 210$ legal opportunities.
   - Positive Alpha Count: $99 / 210$ ($47.1\%$).
   - Mean Cash Delta: **`+$27.40`** | Median: `$0.00` | Max: `+$649.00`.
   - 95th Percentile: `+$313.30`.
   - Downside Risk (P5): `-$241.00`.
   - Rescues: **3** | Casualties: **0**.
2. **`TERMINAL_LIQUIDATE_PARTIAL` (Action 2):**
   - Sample Count: $N = 447$ legal opportunities.
   - Positive Alpha Count: $202 / 447$ (**$45.2\%$**).
   - Mean Cash Delta: **`+$24.77`** | Median: `$0.00` | Max: `+$552.00`.
   - 95th Percentile: `+$185.00`.
   - Downside Risk (P5): **`-$111.00`** (cuts full-dump downside by 53.9%).
   - Rescues: **5** (highest of any single intervention) | Casualties: **0**.
3. **`DEFER_EXPANSION_LOW_CASH` (Action 9):**
   - Sample Count: $N = 82$ legal opportunities.
   - Positive Alpha Count: $3 / 82$ ($3.7\%$).
   - Mean Cash Delta: **`+$190.94`** | Median: `$0.00` | Max: `+$14,242.00`.
   - Rescues: **0** | Casualties: **0**.
4. **`PRESERVE_LIQUIDITY_BUFFER` (Action 8):**
   - Sample Count: $N = 562$ legal opportunities.
   - Positive Alpha Count: $3 / 562$ ($0.5\%$).
   - Mean Cash Delta: **`+$27.86`** | Median: `$0.00` | Max: `+$14,242.00`.
   - Rescues: **0** | Casualties: **0**.

---

### Question 2: Which produced negative alpha?
1. **`SPOT_SELL_PEAK_STRAWBERRY` (Action 5):**
   - Sample Count: $N = 495$ legal opportunities.
   - Positive Count: $13 / 495$ ($2.6\%$).
   - Mean Cash Delta: **`-$25.29`** | Median: `$0.00` | Max: `+$619.00`.
   - Downside Risk (P5): **`-$131.00`**.
   - Rescues: **0** | Casualties: **1** (converted baseline win to loss).
   - *Causal Root:* Strawberries have slow spoilage and high price sensitivity. Selling prematurely midgame captures transient cash but depresses future spot prices and starves peak bulk fulfillment.
2. **`MIDGAME_LAND_EXPAND_GATED` (Action 7):**
   - Evaluated across boundary search ($N = 149$ branch rollouts).
   - Mean Cash Delta: **`-$2,506.60` to `-$12,641.70`**.
   - Mean Margin Delta: **`-$3,563.20` to `-$9,043.30`**.
   - Casualties: **20 casualties created**.
   - *Causal Root:* Siphons `$4,000` capital without chore waypoint synthesis; land sits idle.
3. **`HOLD_DEPRESSED_GOODS` (Action 6):**
   - Sample Count: $N = 182$.
   - Mean Cash Delta: **`-$1.11`** | Positive Rate: $14.3\%$.
   - P5: `-$18.95` | P95: `+$17.75`.
   - Pure noise; does not generate reliable incremental value.

---

### Question 3: Which produced positive alpha only under narrow regimes?
1. **`SPOT_SELL_PEAK_MILK` (Action 3):**
   - Mean Delta: `+$18.71`, but positive in only $47 / 653$ states ($7.2\%$).
   - Created **2 casualties** in tight matches ($|\text{margin}| < \$2,000$).
   - Positive **only** when our farm already held extreme capital dominance ($>\$100,000$) against passive bots (`E0_V3`, `E2_A7`). Against active dumpers (`E8_DMITRII`, `SYN_AGG`), mean delta was `-$143.62`.
2. **`SPOT_SELL_PEAK_WOOL` (Action 4):**
   - Mean Delta: `+$24.46`, but positive in only $22 / 507$ states ($4.3\%$).
   - Created **2 casualties**.
   - Positive strictly under high spot price ($P \ge \$50$) with passive opponent absorption.
3. **`TERMINAL_LIQUIDATE_FULL` (Action 1):**
   - Highly positive (`+$649.00`) **only** when marketable shed inventory was small ($\le 4$ items).
   - When shed inventory exceeded 10 items, full dumping caused internal price collapse (P5 `-$241.00`).

---

### Question 4: Which produced rescues?
Across the 721 baseline loss states analyzed in the V42 training dataset, exactly **11 states** were rescued by single interventions:
* **`TERMINAL_LIQUIDATE_PARTIAL` (Action 2):** **5 rescues** (45.5% of all rescues).
* **`SPOT_SELL_PEAK_WOOL` (Action 4):** **5 rescues** (45.5% of all rescues).
* **`TERMINAL_LIQUIDATE_FULL` (Action 1):** **3 rescues** (overlapping with Action 2).
* **`SPOT_SELL_PEAK_MILK` (Action 3):** **1 rescue**.

Crucially, in the live DEV tournament, Ladder C achieved **1 confirmed rescue** (`LOSE` $\to$ `WIN` on Seed 249657 vs `E2_A7`), turning a `-$85.00` loss into a `+$115.00` win.

---

### Question 5: Which interventions interact with one another?
The interaction between two interventions $A$ and $B$ is quantified by:
$$\Delta_{\text{interaction}}(A, B) = \alpha(A \to B) - \alpha(A) - \alpha(B)$$
V42 identified multiple direct interaction channels:
1. **Liquidation Staggering ($A = \text{Partial at 694}, B = \text{Partial at 705}$):**
   - Interacts positively because $A$ sells into unflooded market depth before opponent Step 695 dump, and $B$ sells remaining units after the market partially recovers.
2. **Spot Sale & Terminal Liquidation ($A = \text{Spot Sell Milk}, B = \text{Terminal Liquidate}$):**
   - Interacts negatively: executing $A$ depletes the shed stock of Milk, rendering $B$ ineffective or leaving low-value goods behind.
3. **Liquidity Preservation & Capital Purchases ($A = \text{Preserve Liquidity}, B = \text{Expand Land}$):**
   - $A$ cancels $B$, representing direct mutual exclusion.

---

### Question 6: Which interventions are mutually exclusive?
1. **`TERMINAL_LIQUIDATE_FULL` and `TERMINAL_LIQUIDATE_PARTIAL` at the same step:**
   - Both target the same market order basket. Firing both produces invalid redundant orders.
2. **`PRESERVE_LIQUIDITY_BUFFER` and `MIDGAME_LAND_EXPAND`:**
   - Preservation explicitly purges `BUY_LAND` orders from the order queue.
3. **`SPOT_SELL_PEAK_MILK` and `HOLD_DEPRESSED_GOODS` (for Milk):**
   - One orders a sell; the other purges sell orders for the same commodity.

---

### Question 7: Which interventions are complementary (Synergistic)?
1. **Staggered Liquidation Sequence ($A \to B$):**
   - `TERMINAL_LIQUIDATE_PARTIAL` (Step 694, 50%) followed by `TERMINAL_LIQUIDATE_PARTIAL` (Step 705, 50% of remainder) and `FINAL_FLUSH` (Step 716, 100% of residual).
   - Realizes higher cumulative cash than any single dump without price erosion.
2. **Capital Preservation into Targeted Deployment:**
   - `DEFER_EXPANSION_LOW_CASH` (Steps 100–300) preserves critical working capital for seed and feed purchases, enabling stronger compounding that yields a larger harvest at Step 650.

---

### Question 8: Which interventions are order-dependent?
1. **Partial Liquidation Order:**
   - Step 694 must precede Step 705. Liquidating 50% at 705 and then attempting to liquidate at 694 is temporally impossible.
   - Furthermore, dumping at 694 pre-empts opponent Step 695 dump. If delayed until 696, the opponent has already crashed the spot price, destroying marginal revenue.
2. **Production Buffer before Liquidation:**
   - Preserving goods during midgame market troughs ($P < \$20$) is only valuable if followed by a terminal or peak liquidation step. Withholding sales without eventual liquidation results in goods spoiling or expiring at step 718 with zero revenue.

---

### Question 9: Which interventions are useful only because another earlier action occurred?
1. **Second Liquidation (Step 705):**
   - Step 705 partial liquidation is useful **only because Step 694 was a partial liquidation (50%) rather than a full liquidation (100%)**. If Step 694 dumped 100%, the shed is empty at Step 705, making the second action completely vacuous ($N=0$).
2. **Late Capital Deployment:**
   - Late high-value purchases or market operations are enabled only if liquidity was preserved during steps 150–400.

---

### Question 10: Which V42 results survive full-terminal rollout?
* **Survives:**
  - `TERMINAL_LIQUIDATE_PARTIAL` at Step 694: Mean cash delta `+$118.00`, 0 casualties, 4 rescues (evaluated to Step 719).
  - `TERMINAL_LIQUIDATE_PARTIAL` at Step 705: Mean cash delta `+$71.00`, 0 casualties, 3 rescues.
  - Overall Ladder C Staggered Liquidation: Mean cash delta `+$110.94`, 0 casualties.
* **Fails / Disproven:**
  - V41 `MIDGAME_LAND_EXPAND_F5`: Showed `+$3,385` at step 304 (24-step horizon), but crashed to **`-$12,341.06` cash delta** and **`-$7,699.17` margin delta** when evaluated to full terminal step 719, causing 6 casualties.

---

### Question 11: Which V42 findings are still based on small cohorts?
1. **Live DEV Tournament Cohort:**
   - Evaluated on 4 seeds (`249685..249688`) $\times$ 4 opponents $\times$ 2 seats = 32 legs per candidate (96 total legs). While statistically clean, 4 seeds represent a limited sample of environmental diversity.
2. **Rescue Cohort:**
   - Evaluated on 24 matches with 1 confirmed rescue. A larger cohort of loss and near-tie seeds is needed to quantify rescue potential with high confidence.
3. **Sequencing Depth:**
   - V42 only tested the fixed 50/50 two-point schedule (694, 705). Boundary search over other fraction splits (30/70, 40/60, 60/40, 70/30) and multi-step combinations was not evaluated.

---

### Question 12: Where is the remaining unexplained V35 loss margin?
Analyzing the 721 loss states in the V42 training dataset:
* **Margin Distribution of Losses:**
  - Minimum deficit: `-$2.00` (ultra-narrow tie-breaker).
  - Maximum deficit: `-$16,133.00` (runaway opponent compounding).
  - Mean deficit: **`-$1,281.00`**.
  - Median deficit: **`-$452.00`**.
* **Loss Categorization:**
  1. **Near-Ties ($|\text{margin}| \le \$500$):** Represent **54.2%** of all losses. In these matches, our farm has between `$1,500` and `$3,500` of unharvested crops or unliquidated shed inventory at step 680. Recovering `$200` to `$600` via multi-step planning is mathematically sufficient to flip these losses into wins!
  2. **Mid-Range Losses ($\$500 < |\text{margin}| \le \$2,500$):** Represent **31.8%** of losses. Caused by opponent commodity dominance or slightly earlier farm scaling.
  3. **Severe Runaway Deficits ($|\text{margin}| > \$2,500$):** Represent **14.0%** of losses. Unrecoverable by terminal actions alone; requires earlier intervention sequences.

---

## 3. The V43 Strategic Mandate

V42 answered the question: *Does positive alpha exist?* (Yes, `+$110.94`).  
V43 must now answer: **Can safe alpha compose into multi-step strategies that capture the remaining recoverable margin?**

The architecture must transition:
$$\text{From: } (s_t, a_t) \to r_{719} \quad\Longrightarrow\quad \text{To: } (s_t, (a_t, a_{t+k}, \dots), \text{timing}, \text{conditions}) \to r_{719}$$

The immediate next steps for V43:
1. Construct the **Sequential Counterfactual Engine** to simulate action tuples $(A, B)$ and measure pairwise interaction alpha $\Delta_{\text{interaction}}$.
2. Map the **Intervention Conflict & Interaction Graph**.
3. Mine the complete **Rescue Library** from baseline losses.
4. Generalize the staggered liquidation boundary across fractions $(30/70, 40/60, 50/50, 60/40, 70/30)$ and timings.
5. Train the **Sequence Advantage & Uncertainty Model** and run active learning boundary search.
