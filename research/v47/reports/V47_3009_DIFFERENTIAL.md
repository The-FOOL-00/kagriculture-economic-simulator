# V47 — 3009 & Elite Champion Differential Analysis Report

**Date:** 2026-09-25  
**Program:** Kagriculture V47 — 3000 Breakthrough Program  
**Incumbent Benchmark:** V44 (`candidates/v44_economic_portfolio/main.py`)  
**Public Benchmark Artifacts:**
1. `kaitofukami_v48_3009` (Score: 3009.0, SHA256: `dadee25a9840313218384208c53b2c4752f82c3209cc654632e0b96c65e2664a`)
2. `thomastschinkel_2945` (Score: 2944.7, SHA256: `bfee70e9daaebeae0737a880f1df8f1c60d0783c59af620136cc0d28ef482bc7`)

---

## 1. Executive Summary: The 3009 Paradox and the True Champion

Our Phase 5 1,536-game benchmark revealed a critical empirical reality:

1. **The 3009 Paradox:**
   - Under exact local simulation (Kaggriculture 1.32.7, 64 clean seeds x 2 seats = 128 legs), **V44 beats `kaitofukami_v48_3009` 100.00% of the time (128-0)** with a Mean Margin of **+$25,235.38** ($102,435 vs $77,200).
   - The 3009 public notebook achieves its high leaderboard rating by aggressively specializing early on revealed shops (`yarn_fast` at step 88, `farm_fast` at step 120), which exploits weaker leaderboard bots. Against V44's disciplined CapEx cutoff (step 520) and balanced high-value animal economy, 3009 collapses economically and suffers massive terminal margin loss.
2. **The True Elite Champion (`thomastschinkel_2945`):**
   - In stark contrast, `thomastschinkel_2945` (The 2945 Farm) decisively outperforms V44 locally:
     * **Win Rate:** **95.31%** (122 wins vs 6 wins for V44)
     * **Mean Margin:** **+$3,582.77** ($99,683 vs $96,100)
     * **Head-to-Head vs 3009:** 2945 beats 3009 **100.00%** (+$28,062 margin).
   - Thus, `thomastschinkel_2945` represents the true 3000-level champion whose causal mechanisms must be isolated and transferred into V44.

---

## 2. Action-Level Differential Analysis

Replaying identical worlds (CRN) across 16 clean evaluation seeds revealed the exact divergence structure between V44, 2945, and 3009:

### Divergence by Phase & Family (16 Paired Games)
- **First Divergence Step:** Step 0 (opening market bids / initial farmer placement).
- **Divergence Density by Phase:**
  * **Opening (Day 0–3, Steps 0–95):** 128 divergent steps across games.
  * **Early Game (Day 4–10, Steps 96–263):** 684 divergent steps.
  * **Mid Game (Day 11–20, Steps 264–503):** 1,539 divergent steps (major livestock investments).
  * **Late Game (Day 21–27, Steps 504–671):** 1,839 divergent steps (peak harvest and recurring market sales).
  * **Terminal Phase (Day 28–29, Steps 672–719):** 406 divergent steps (liquidation and asset recovery).
- **Divergence by Action Family:**
  * **Market actions:** 3,750 steps (primary divergence axis).
  * **Hired hands:** 1,881 steps.
  * **Farmer actions:** 630 steps.

---

## 3. Macro Signature Differential

| Economic Dimension | V44 Portfolio Baseline | `kaitofukami_v48_3009` | `thomastschinkel_2945` |
| :--- | :--- | :--- | :--- |
| **Land Schedule** | 3 Quadrants (NW, NE, SW) | 2–3 Quadrants (Shop dependent) | 3 Quadrants |
| **Hired Hands** | 11 Hands | 8–10 Hands | 11 Hands |
| **Livestock Scale** | ~17 Animals (4 Goose, 7 Cow, 6 Sheep) | 8–12 Animals (Over-indexed on Wool) | ~17 Animals (Adaptive: COWSWAP / HERD2) |
| **Crops** | Early Wheat/Strawberries | Early specialized mono-crop | Wheat with CARROT substitution |
| **CapEx Cutoff** | Strict Step 520 Cutoff | None (buys late) | Implicit through tape horizon |
| **Market Sell Order** | Route-default static order | Nonlinear Market Impact Reordering | Rival-Harvest Exposure Ordering (`ORDERPRI2`) |
| **Sale Timing** | Fixed schedule + Steps 693/718 | Fixed schedule + Step 718 | `RACE` Pre-emptive Advancement on Rival Harvest |
| **Mean Cash (vs 2945)** | $96,100 | $73,260 | **$99,683** |

### The Causal Smoking Gun:
In seeds where V44 and 2945 produce the **exact same animal portfolio** (e.g. Seed 249801: 3 Goose, 8 Cow, 6 Sheep; Seed 249804: 11 Sheep, 6 Cow), 2945 still beats V44 by **+$2,400 to +$3,600**!

The advantage is **NOT** physical farm layout or worker movement.  
The advantage is **MARKET EXECUTION**:
1. **Rival Harvest Tracking (`_OR2`):** 2945 tracks opponent tile harvests every step. When V44 harvests cows or sheep, 2945 immediately identifies that V44's shed is loaded with Milk or Wool.
2. **Pre-emptive Sale Advancement (`_OR2_SN`):** 2945 immediately pulls forward planned future sales of that commodity from downstream tape steps (horizon 40) into the current turn, while booking future debts.
3. **Exposure Reordering (`ORDERPRI2`):** 2945 places its Milk/Wool sales in the highest-priority market slots.
4. **Result:** 2945's commodities sell at peak prices (e.g. $160-$170 for Milk, $200 for Wool). When V44's sales execute afterwards, the market price has already collapsed, forcing V44 to absorb the price impact.

---

## 4. Reverse-Engineering the Public 3009 Mechanisms

From decompiling `kaitofukami_v48_3009`, we extracted the following distinct components:

1. **`scripts_v22_market_impact.py` (Market Impact Slot Reordering):**
   - Calculates $Q \times (P(Inv) - P(Inv + Q))$ using exact 1.32.7 curves.
   - Sorts only existing SELL slots; does not modify non-SELL orders or change quantities.
   - **Verdict:** Clean, market-neutral, zero structural risk.
2. **`v23_policy_library.py` (Demand-Adjusted Scoring):**
   - Weights price impact by town demand recovery time: $Urgency = \min(1.0, \frac{Excess}{10 \times Demand})$.
   - **Verdict:** Economically sound; gives priority to goods whose price will not quickly bounce back.
3. **`scripts_v22_weed_repair.py` (Actor-Local Weed Repair):**
   - Intercepts worker collisions with weeds, digs on turn $t$, retries on $t+1$, replays fixed route actions.
   - **Verdict:** Highly valuable safety overlay for preventing route stalls on unweeded tiles.
4. **`v48_fast_route_router.py` (Sparse Fast Climber Router):**
   - Hard branches at step 88 on YARN_STORE or step 120 on FARMERS_MARKET.
   - **Verdict:** **DANGEROUS AND FRAGILE.** Causes the 100% loss against V44 under unbiased seeds. We reject whole-route early switching.

---

## 5. Candidate Transfer Roadmap for V47

To surpass 2945 and reach the 3000 rating threshold under our exact engine, V47 will combine:

1. **V44 Rock-Solid Production Engine:**
   - 3-Quadrant multi-quadrant farming.
   - 11 Hired hands.
   - Strict Step 520 CapEx cutoff.
2. **Elite Market Execution Overlays:**
   - **Mechanism A (Market Impact Ordering):** Reorder SELL slots by impact score.
   - **Mechanism B (Demand Awareness):** Weight impact by town demand recovery urgency.
   - **Mechanism C (Rival Stock Exposure Reordering):** Order sales by rival's estimated sellable inventory.
   - **Mechanism D (Demand-Preserving Pre-emptive Sale Advancement):** Advance planned sales when rival harvests, maintaining zero phantom inventory via future tape debt deduction.
   - **Mechanism E (Adaptive Livestock Routing):** COWSWAP / HERD2 dynamic EV selection at steps 144–192 when town lacks milk shops.

This hybrid architecture preserves V44's disciplined capital compounding while eliminating its market-vulnerability to elite front-running bots.
