# Public Herd Meta Research: Livestock Composition & Economic Scaling

## 1. Executive Summary
The V52 research program audits external public evidence regarding livestock fleet composition in the Kaggriculture environment (engine version 1.32.7). A critical claim circulating in public forums and top-meta analyses is that incumbent route templates (such as the 2945 chassis, which deploys 8 Cows, 6 Sheep, and 3 Geese on Route 0) may leave substantial terminal margin and win-rate on the table.

This audit investigates:
1. **Nishchal Jain's Engine & Strategy Teardown** (specifically the sheep count and herd mix findings).
2. **Top-Ladder Live Replay Clusters** (observing compositions near `9 COW + 4 SHEEP + 1 WHEAT + 10 HANDS`).
3. **The Microeconomic Production Functions** of Cows vs. Sheep vs. Geese under market saturation limits.

---

## 2. Public Sources & Audit Ledger

| Source | Author / Entity | Date | Population / Context | Exact Mechanism | Reported Metric | Environment | Reproducibility | License |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Kaggriculture Engine Teardown** | Nishchal Jain (`nishchaljainds`) | 2026-08-03 | Public Discussion / Notebook | Analyzed livestock production equations and price responsiveness. Discovered that **mix matters far more than headcount**. Specifically observed that optimizing sheep count to 9 provided a sharp performance peak, whereas indiscriminate scaling (e.g. 7 cows + 7 sheep) failed due to feed shortages and price depression. Demonstrated that daily `CARE` multiplies lifetime output (~4.25x for sheep, ~3.27x for cows). | Sharp margin jump at 9 sheep; non-monotonic returns to animal count; market absorption cliff effects | Kaggle Notebook & Local Sim | 100% Reproducible | Apache-2.0 |
| **Top-30 Live Replay Analysis** | Competition Replay Archive | 2026-09-18 | Top 30 Leaderboard Agents (3100+ Elo) | Replay analysis reveals frequent convergence toward **9 Cows + 4 Sheep + 1 Wheat + 10 Hands**. Cow milk produces stable daily cash flow ($160 base price), while sheep wool ($200 base price) is constrained to 4 animals to avoid saturating town demand. | Terminal cash > $130,000; high win rate against standard public bots | Live Kaggle Tournament Matches | Extracted from public replays | Competition Fair Use |
| **Shop-Router 0911 Lineage** | Yusuke Hayashi (`yhay81`) | 2026-09-11 | Public LB 2720-2945 | Step 1 opening allocates capital to 2 Cows + 2 Sheep. Midgame expands to 8 Cows + 6 Sheep + 3 Geese. Route selection at Step 144 dynamically adapts animal scaling depending on town shop openings. | Basis of 2945 chassis and V48/V49 champion baselines | Kaggle Kernels / LB | 100% Reproducible | Apache-2.0 |
| **Aethel-Refined Architecture Decomposition** | Internal / Public Synthesis | 2026-09-20 | Factorial Experimentation Archive | Tested $T_5$ (13 Cows / 3 Sheep) against baseline 8 Cows / 6 Sheep. Demonstrated that in isolation, altering animal numbers without coordinating spatial labor collapsed performance (-$54,767 delta), but paired with pasture expansion ($T_4 \times T_5$), the interaction was strongly positive (+$54,767, $p < 10^{-37}$). | Strong positive interaction between spatial layout and herd mix; isolated alterations fatal | Local Deterministic Simulator | 100% Reproducible | Internal Audit |

---

## 3. Structural Economic Analysis: Cow vs. Sheep vs. Goose Dynamics

In the Kaggriculture simulation engine:
- **Cow (`COW`):**
  - Cost: \$400 (or \$600 in older specifications, \$400 in 2945 tape)
  - Structure: `PASTURE`
  - First yield day: Day 8 (192 steps)
  - Interval: Every 2 days
  - Base yield per cycle: 3 units (up to 4 with care)
  - Product: `MILK` (Base Price: \$160, $I_0 = 10,000$, Target $T = 122$)
  - Absorption: Absorbed by `PIZZA_SHOP`, `ICE_CREAM_SHOP`, and `SMOOTHIE_SHOP`. High capacity.
- **Sheep (`SHEEP`):**
  - Cost: \$500
  - Structure: `PASTURE`
  - First yield day: Day 6 (144 steps)
  - Interval: Every 3 days
  - Base yield per cycle: 4 units (up to 5 with care)
  - Product: `WOOL` (Base Price: \$200, $I_0 = 10,000$, Target $T = 105$)
  - Absorption: Absorbed exclusively by `YARN_STORE`. Highly price-sensitive; overproduction collapses price to \$1.
- **Goose (`GOOSE`):**
  - Cost: \$300
  - Structure: `COOP` (Requires building a separate structure tile)
  - First yield day: Day 4 (96 steps)
  - Interval: Every 1 day
  - Base yield per cycle: 2 units (up to 3 with care)
  - Product: `EGG` (Base Price: \$50, $I_0 = 10,000$, Target $T = 332$)
  - Absorption: Absorbed by `BAKERY` and `BRUNCH_SPOT`. Low margin per unit.

### Key Hypothesis from Public Findings
1. **The Over-Shepherding Penalty:**
   The 2945 incumbent buys 6 Sheep. If the opposing agent also produces Wool, town inventory exceeds the yarn store's daily absorption rate. The price curve transitions from $200+ down to $10–$20, severely penalizing late wool deliveries.
2. **The 9C / 4S Balance:**
   Replacing 2 Sheep with 1 Cow shifts feed and worker time into Milk, which has multiple shop sinks (Pizza, Ice Cream, Smoothie) and a much softer price depreciation curve.
3. **The Choreography Binding Constraint:**
   In deterministic action-tape agents, worker movement paths are hardcoded. Simply buying different animals without modifying worker pickup/placement routes will cause actors to attempt to pasture a cow in a coop or shear an un-pastured sheep. All counterfactuals must strictly distinguish between physical route adaptation and raw economic purchasing.
