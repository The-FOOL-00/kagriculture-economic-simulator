# Forensic Reconstruction: V54 & V66 Operational Architecture

**Source of Truth:** Executable source code from:
- V54: `external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py`
- V66: `external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py`
- Engine: `kaggle_environments.envs.kaggriculture.kaggriculture`

---

## 1. V54 Exact Policy Reconstruction (Solo Benchmark: $165,492 Mean)

Across 10 deterministic validation seeds (2000–2009), V54 operates a tightly synchronized macroeconomic pipeline:

### A. Labor Scheduling & Workforce Density
* **Day 0 Opening:** Exactly **5 workers** hired on Step 0 (Cost: $1+1+2+3+5 = \$12$).
* **Day 1–5:** Maintains a steady **4–5 workers/day** for early crop maintenance.
* **Day 6 (Land Unlock 1):** Ramps instantly to **8 workers/day** (Cost: \$54).
* **Day 10–14:** Expands to **11 workers/day** (Cost: \$232).
* **Day 15–20:** Reaches peak density of **12 workers/day** (Cost: \$376).
* **Day 21–29:** Sustains **11 workers/day** through endgame liquidation.
* **Total Workforce:** Exactly **290.0 worker-days** per match ($6,218 total hiring expenditure).
* **Workforce Actions:** 333 Cares, 326 Feeds, 338 Fertilizer Collections, 700+ Waters, 450+ Harvests.

### B. Crop Engine & Self-Sufficient Feed Loop
* **Melon:** Exactly 12 seeds purchased on Day 0–1. All 12 planted in Quadrant 1. Yields **72 units sold** for **$17,064 gross revenue**.
* **Wheat (The Core Engine):** Exactly **187 seeds purchased and planted**.
  * **On-Farm Feed Cycling:** Wheat harvests feed all cows and sheep directly on-farm. Zero finished feed is ever purchased from the market, avoiding an \$8k–\$12k capital drain.
  * **Surplus Cash Clearance:** Excess wheat is dumped into the market (mean **386.0 units sold** for **$15,565** pure profit).
* **Strawberry (Recurring Wealth Wave):** Exactly **38 seeds purchased** starting at step 128 (Day 5).
  * All 38 seeds planted immediately in Quadrants 2 and 3.
  * Yields **295.0 recurring units sold** for **$55,128 gross revenue** (33.3% of total final wealth).
* **Carrot:** Exactly 6 seeds purchased on Day 0 for early liquidity ($668 revenue).

### C. Livestock Fleet Execution
* **Fleet Size:** 7 cows purchased, 3 sheep purchased (augmented by shed drops $\to$ **9 cows and 5 sheep placed** on pastures).
* **Pasture Topology:** Built immediately adjacent to the shed (access coordinates $(3,4), (4,3), (4,6), (5,3)$) to minimize worker round-trip travel time.
* **Yield Monetization:**
  * **Milk:** 270.0 units sold $\to$ **$56,681 gross revenue** (34.2% of total wealth).
  * **Wool:** 154.0 units sold $\to$ **$29,967 gross revenue** (18.1% of total wealth).
  * **Fertilizer:** 335.0 units collected and sold $\to$ **$24,363 gross revenue** (14.7% of total wealth).
* **Starvation / Animal Loss:** **Zero** starvation events across all 10 seeds.

### D. Capital Velocity Milestones
* Day 0: $24 | Day 1: $247 | Day 3: $260 | Day 5: $910 | Day 10: $19,056 | Day 15: $39,806 | Day 20: $77,903 | Day 25: $123,884 | Day 29: **$165,492**.
* Land Expansions: Quadrant 2 unlocked at Step 151 ($1,000); Quadrant 3 unlocked at Step 266 ($2,000).

---

## 2. V66 Exact Policy Reconstruction (Solo Benchmark: $167,562 Mean)

V66 inherits the entire V54 macroeconomic base but introduces an adaptive meta-classification overlay:

### Behavioral Diff (V54 $\to$ V66):
1. **Adaptive Wheat Monetization (Class A - Economically Meaningful):**
   * V66 produces **562.2 units of wheat sold** (vs 386.0 in V54), earning **$22,362** (+30.5% wheat revenue gain).
   * It prioritizes late-game wheat harvest cycles over terminal strawberry watering.
2. **Public Observation Opponent Classifier (Class A - Economically Meaningful):**
   * At Steps 72 and 144, V66 computes `_public_signature(obs)` (unlocked shops, own/opp cash, hands, asset counts, market inventory, prices).
   * Matches opponent against 9 historical threat archetypes (`_VICTOR`, `_TWOMOON`, `_YAT`, `_BAKERY`, `_FARMERS`, `_NEIBYR`, `_C0NRAD`, `_JOHNBLAKE`, `_STEPHEN`).
   * Switches route dynamically between 6 specialized sub-policies (`bakery_yarn`, `recovery`, `yarn`, `ice_minimax`, `known_yarn`, `clone`).
3. **Structured Action Sanitizer (Class D - Robustness Enhancement):**
   * Wraps all outputs through `kaggriculture_agent.env.adapter.sanitize_action`, eliminating malformed command tuples and out-of-bounds orders.

---

## 3. Normalized Milestone Ledger (V54 vs V66 vs EXP-A Declarative Backbone)

| Milestone / Metric | V54 Canonical | V66 Adaptive | EXP-A Declarative Backbone |
| :--- | :---: | :---: | :---: |
| **Solo Mean Reward (IDLE)** | **$165,492** | **$167,562** | **$62,387** |
| **Head-to-Head vs V54** | **$80,264** | **$83,324** | **$25,696** |
| **Total Worker-Days** | 290.0 | 288.9 | 230.0 |
| **Opening Day 0 Hires** | 5 workers | 5 workers | 3 workers |
| **Wheat Seeds Bought / Planted** | 187 / 187 | 187 / 187 | **0 / 0** |
| **Wheat Sold (Units / Rev)** | 386.0 / $15.6k | 562.2 / $22.4k | **0 / $0** |
| **Feed Sourced From** | 100% On-Farm | 100% On-Farm | Market Purchases ($8.1k drain) |
| **Strawberry Seeds Bought / Planted**| 38 / 38 | 37.4 / 37.4 | 38 / **1 (37 stranded)** |
| **Strawberry Sold (Units / Rev)** | 295.0 / $55.1k | 266.2 / $50.2k | **0 / $0** |
| **Milk Sold (Units / Rev)** | 270.0 / $56.7k | 262.1 / $55.8k | 200.6 / $42.8k |
| **Fertilizer Sold (Units / Rev)**| 335.0 / $24.4k | 335.1 / $24.1k | 251.0 / $20.1k |
| **Wool Sold (Units / Rev)** | 154.0 / $30.0k | 152.4 / $30.2k | 94.7 / $18.4k |
| **Melon Sold (Units / Rev)** | 72.0 / $17.1k | 72.0 / $17.1k | 14.0 / $3.6k |
| **Carrot Sold (Units / Rev)** | 12.0 / $0.7k | 12.6 / $0.7k | 107.8 / $4.2k |
| **Quadrant 2 Unlock Timing** | Step 151 (Day 6) | Step 151 (Day 6) | Step 169 (Day 7) |
| **Quadrant 3 Unlock Timing** | Step 266 (Day 11) | Step 266 (Day 11) | Step 265 (Day 11) |
