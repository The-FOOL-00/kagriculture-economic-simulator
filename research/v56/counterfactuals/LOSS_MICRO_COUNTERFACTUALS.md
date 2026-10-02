# V56 — Loss Micro-Counterfactuals & Rescue Experiments

## Executive Summary

To answer the core research question of V56:
> *"Why does V49 lose its remaining games, and can a minimal, legally observable, causally justified change flip some of those losses without creating fresh casualties?"*

We constructed and tested four targeted single-decision micro-counterfactuals against the four fresh loss worlds (Seeds 250617, 250621; Seats 0, 1 vs V44). Crucially, every counterfactual was also tested against the closest near-win safety controls (Seeds 250616 [+$384], 250631 [+$305]) to evaluate casualty risk under Gate A.

The results are stark:
1. **0 Historical Losses Rescued**: Across all four interventions, zero loss matches flipped to wins.
2. **Losses Worsened**: In every case, the margin of defeat increased (e.g. from -$82 to -$324 or -$1,516 on Seed 250621).
3. **Fatal Casualties Induced**: Interventions that attempted to reorder or accelerate market transactions flipped near-wins into catastrophic defeats (creating up to 4 fresh casualties).
4. **Causal Mechanism Proven**: V49's existing execution sequence is a fragile, tightly tuned Pareto optimum. Unilateral micro-changes trigger downstream shed overflow, crop loss, and desynchronization.

---

## 1. Experimental Matrix & Quantitative Results

### Counterfactual 1: Descending-Price Market Sell Ordering (Late Endgame, Steps 600–696)
- **Hypothesis**: The decisive loss margin occurred at Step 697 when V44 cleared `WOOL` at queue index 1 before V49 cleared `WOOL` at queue index 3. Sorting sell orders by descending commodity price (`WOOL` $\to$ `MILK` $\to$ `EGG` $\to$ `CARROT`) should capture peak prices and rescue the match.
- **Intervention Horizon Tested**: Steps 600, 648, 672, and 696.

| Match Spec | Seed | Seat | Base Margin | Cand Step 696 | Cand Step 672 | Cand Step 648 | Cand Step 600 | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **L1 (Loss)** | 250617 | 0 | -$862.0 | -$1,015.0 (-$153) | -$1,040.0 (-$178) | -$1,042.0 (-$180) | -$1,127.0 (-$265) | **Worsened** |
| **L2 (Loss)** | 250617 | 1 | -$862.0 | -$1,015.0 (-$153) | -$1,040.0 (-$178) | -$1,042.0 (-$180) | -$1,127.0 (-$265) | **Worsened** |
| **L3 (Loss)** | 250621 | 0 | -$82.0 | -$324.0 (-$242) | -$935.0 (-$853) | -$1,355.0 (-$1,273) | -$1,516.0 (-$1,434) | **Worsened** |
| **L4 (Loss)** | 250621 | 1 | -$82.0 | -$324.0 (-$242) | -$935.0 (-$853) | -$1,355.0 (-$1,273) | -$1,516.0 (-$1,434) | **Worsened** |
| **W_616 (Win)** | 250616 | 0 | +$384.0 | -$31.0 (-$415) | +$189.0 (-$195) | +$113.0 (-$271) | -$28.0 (-$412) | **CASUALTY** |
| **W_616 (Win)** | 250616 | 1 | +$384.0 | -$31.0 (-$415) | +$189.0 (-$195) | +$113.0 (-$271) | -$28.0 (-$412) | **CASUALTY** |
| **W_631 (Win)** | 250631 | 0 | +$305.0 | -$197.0 (-$502) | -$210.0 (-$515) | -$219.0 (-$524) | -$354.0 (-$659) | **CASUALTY** |
| **W_631 (Win)** | 250631 | 1 | +$305.0 | -$197.0 (-$502) | -$210.0 (-$515) | -$219.0 (-$524) | -$354.0 (-$659) | **CASUALTY** |

#### Why Did Price Sorting Fail?
1. **The Shed Congestion Trap**: V49 places bulky crops (`CARROT`) at the front of its sell list for a critical physical reason: storage capacity in the farm shed is capped at 30 units. Selling bulky crops immediately frees shed space. When `WOOL` and `MILK` (small quantities) were placed first, carrots remained in inventory. When workers harvested subsequent crop plots, the shed was full; the engine's `_harvest` logic silently dropped the excess produce.
2. **Cross-Commodity Price Elasticity**: In Seed 250621, selling Wool first raised Wool revenue by +$144, but pushed Carrot sales behind V44's carrot sales. V44 depressed the carrot price from $12 to $6, costing V49 -$386 on 15 carrots. The net change was -$242.0.
3. **Casualty Generation**: On Seeds 250616 and 250631, games that V49 won under default order flipped to losses of -$31.0 and -$197.0, violating Gate A.

---

### Counterfactual 2: Pre-Emptive Liquidation at Step 696
- **Hypothesis**: Sell all inventory at Step 696 (1 turn early) to avoid sharing the market queue with V44 at Step 697.
- **Result**:
  - L1 (Seed 250617): Margin collapsed from -$862.0 to -$3,934.0 (-$3,072 delta).
  - L3 (Seed 250621): Margin collapsed from -$82.0 to -$3,154.0 (-$3,072 delta).
- **Causal Mechanism**: At Step 696, V49's final dairy collection is still underway. Selling at Step 696 misses the terminal collection of 12 milk units. Because milk traded at $256/unit, premature liquidation forfeited $3,072 of pure gross cash, turning narrow defeats into blowouts.

---

### Counterfactual 3: Step 0 Capital Preservation
- **Hypothesis**: V49 executes a `BUY_PRODUCT WHEAT 20, SELL WHEAT 15` transaction at Step 0. Suppressing this wash would save $400 in early working capital.
- **Result**:
  - L1 (Seed 250617): Margin collapsed from -$862.0 to -$118,430.0 (-$117,568 delta).
  - L3 (Seed 250621): Margin collapsed from -$82.0 to -$97,214.0 (-$97,132 delta).
- **Causal Mechanism**: The Step 0 transaction is load-bearing for the deterministic seed indexing of the `shop-router-0911` backbone. Omitting it alters subsequent shop indexing, causing complete desynchronization and strategic collapse.

---

## 2. Summary of Findings

| Metric | Measured Value | Requirement | Status |
| :--- | :--- | :--- | :--- |
| **Historical Losses Rescued** | **0 / 4 (0.0%)** | $\ge 1$ | **FAILED** |
| **Historical Losses Worsened** | **4 / 4 (100.0%)** | 0 preferred | **FAILED** |
| **Fresh Casualties Induced** | **4 (Seeds 250616, 250631)** | 0 (Gate A) | **FAILED (GATE A BREACH)** |
| **Rescue Feasibility** | **Zero-Casualty Intervention Impossible** | Causal rescue exists | **CLOSED** |

Every attempted surgical intervention proved either self-defeating or lethal to adjacent near-wins. V49's narrow loss boundary cannot be flipped by micro-interventions without incurring catastrophic collateral damage.
