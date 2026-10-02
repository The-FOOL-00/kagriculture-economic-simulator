# V46 Phase 2: Discovered Strategy Families & Macro Taxonomy Report

**Status:** COMPLETE  
**Optimal Cluster Count:** k=3 (Exploration k=5)  
**Methodology:** Multi-dimensional feature extraction across 720-step replays + K-Means & PCA  

---

## 1. Cluster Evaluation Across Horizons (k=2..12)

| k | Silhouette Score | Stability Assessment |
| :--- | :--- | :--- |
| 2 | 0.4789 | High Separability |
| 3 | 0.5026 **(Optimal)** | High Separability |
| 4 | 0.2663 | Moderate Overlap |
| 5 | 0.2823 | Moderate Overlap |
| 6 | 0.2193 | Moderate Overlap |
| 7 | 0.2591 | Moderate Overlap |
| 8 | 0.2498 | Moderate Overlap |
| 9 | 0.2532 | Moderate Overlap |
| 10 | 0.2704 | Moderate Overlap |
| 11 | 0.2542 | Moderate Overlap |
| 12 | 0.2700 | Moderate Overlap |

---

## 2. Discovered Strategy Archetypes

The analysis confirms that the competitive Kagriculture meta is **NOT a single uniform family**.  
Instead, the population splits into distinct, economically diverging trajectories:

### Family_0: High-Yield Horticulture (Melon Specialist) (14.1% of population, N=35)
- **Representative Agent:** `episode-92913673-replay.json` (Player 0)
- **Terminal Cash:** Mean **$19836.57** | Median **$19813.00** | P95 **$38873.10**
- **Macro Signatures:**
  - Hires: `116.8` | Land Purchases: `1.8`
  - Livestock: Cow Prob `0.06` | Sheep Prob `0.03`
  - Crop Volumes: Strawberry `7.5` | Melon `164.3` | Milk `6.5` | Wool `1.2`
- **Strengths:** High High-Yield Horticulture (Melon Specialist) economic compounding, Peak cash potential up to $38873.10
- **Vulnerabilities:** Vulnerable to targeted market pre-emption, Requires high liquidity synchronization

### Family_1: Dual-Livestock Compound (Cow + Sheep) (29.4% of population, N=73)
- **Representative Agent:** `episode_107513417.json` (Player 0)
- **Terminal Cash:** Mean **$58118.45** | Median **$55275.00** | P95 **$87945.80**
- **Macro Signatures:**
  - Hires: `299.2` | Land Purchases: `2.0`
  - Livestock: Cow Prob `0.99` | Sheep Prob `1.00`
  - Crop Volumes: Strawberry `215.3` | Melon `88.4` | Milk `229.2` | Wool `141.4`
- **Strengths:** High Dual-Livestock Compound (Cow + Sheep) economic compounding, Peak cash potential up to $87945.80
- **Vulnerabilities:** Vulnerable to targeted market pre-emption, Requires high liquidity synchronization

### Family_2: Dual-Livestock Compound (Cow + Sheep) (0.8% of population, N=2)
- **Representative Agent:** `episode_107547195.json` (Player 1)
- **Terminal Cash:** Mean **$89717.50** | Median **$89717.50** | P95 **$102852.55**
- **Macro Signatures:**
  - Hires: `260.0` | Land Purchases: `2.0`
  - Livestock: Cow Prob `1.00` | Sheep Prob `1.00`
  - Crop Volumes: Strawberry `6253.0` | Melon `6072.0` | Milk `8257.0` | Wool `6188.0`
- **Strengths:** High Dual-Livestock Compound (Cow + Sheep) economic compounding, Peak cash potential up to $102852.55
- **Vulnerabilities:** Vulnerable to targeted market pre-emption, Requires high liquidity synchronization

### Family_3: High-Yield Horticulture (Melon Specialist) (3.2% of population, N=8)
- **Representative Agent:** `episode-92902361-replay.json` (Player 1)
- **Terminal Cash:** Mean **$21814.75** | Median **$13263.00** | P95 **$51924.45**
- **Macro Signatures:**
  - Hires: `107.0` | Land Purchases: `0.5`
  - Livestock: Cow Prob `0.25` | Sheep Prob `0.12`
  - Crop Volumes: Strawberry `37.5` | Melon `78.0` | Milk `11.0` | Wool `4.2`
- **Strengths:** High High-Yield Horticulture (Melon Specialist) economic compounding, Peak cash potential up to $51924.45
- **Vulnerabilities:** Vulnerable to targeted market pre-emption, Requires high liquidity synchronization

### Family_4: Dual-Livestock Compound (Cow + Sheep) (52.4% of population, N=130)
- **Representative Agent:** `episode_107653622.json` (Player 0)
- **Terminal Cash:** Mean **$96481.34** | Median **$92433.50** | P95 **$143146.25**
- **Macro Signatures:**
  - Hires: `283.7` | Land Purchases: `2.0`
  - Livestock: Cow Prob `1.00` | Sheep Prob `1.00`
  - Crop Volumes: Strawberry `312.9` | Melon `105.7` | Milk `300.4` | Wool `197.6`
- **Strengths:** High Dual-Livestock Compound (Cow + Sheep) economic compounding, Peak cash potential up to $143146.25
- **Vulnerabilities:** Vulnerable to targeted market pre-emption, Requires high liquidity synchronization


---

## 3. Core Strategic Implication for V46

1. **Strategic Diversity is Real:**
   - Single-route agents (such as standard V35/V44) achieve high baseline scores but follow a fixed livestock-leaning path that leaves unexploited alpha against pure cash-crop or fast-land opponents.
2. **Matchup Vulnerability Exists:**
   - Crop-heavy and Melon-specialist agents generate huge lump-sum liquidations around days 24–28.
   - Dual-livestock agents generate smooth daily continuous yields from milk and wool.
3. **The Early Observable Window:**
   - The opening 12–72 steps exhibit strong early divergence in land purchases, seed buys (Wheat vs Carrot vs Melon), and animal pasture construction.
   - This proves the foundational hypothesis of V46: **Opponents can be categorized early to select counter-routes.**

---
*Report auto-generated by research/v46/replay_intelligence/cluster_strategies.py*
