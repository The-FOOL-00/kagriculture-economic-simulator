# V32 RL-X2 — ECONOMIC STATE SPECIFICATION & OBSERVABILITY AUDIT
**Phase:** V32 RL-X2  
**Date:** 2026-09-23  
**Status:** SPECIFIED, IMPLEMENTED & VERIFIED  
**Package:** `candidates/v32_rlx2/state.py`  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. Design Principles (§10, §11, §59)

The RL-X2 economic state representation is designed to satisfy three foundational criteria:
1. **Strict Observability & Legality (Zero Leakage):** Only variables legally present in the Kaggle `observation` dict are used. Opponent private shed stock, seeds, and worker inventories are completely omitted.
2. **Economic Salience:** Captures capital velocity, labor runway, crop growth, livestock feeding, land availability, and market dynamics.
3. **Structured Tiered Ablation:** Enables controlled scientific comparison between raw essentials ($S_0$), structured economics ($S_1$), opponent observables ($S_2$), and derived opportunity signals ($S_3$).

---

## 2. Representation Tiers Comparison

| Feature Tier | Focus | Vector Dimension | Normalization | Description |
| :---: | :--- | :---: | :---: | :--- |
| **$S_0$** | Raw Essentials | **19** | $[0, 1]$ | Cash, liquid value, shed total, crop total, worker count, normalized time, 9 spot prices, 4 shop indicators. |
| **$S_1$** | Structured Economics | **63** | $[0, 1]$ | $S_0$ + wage runway days, committed wages, hire cost, chore backlog, idle hands, unwatered crops, arable land, weeds, livestock counts (cows, sheep, geese), unfed/uncared counts, empty pastures, feed runway, wheat in shed, quadrants, next land cost, town phase ($step \pmod 4$), hour ($step \pmod{24}$), individual crop counts (5), individual shed inventory (9), price deltas (9). |
| **$S_2$** | Opponent Observables | **71** | $[-1, 1]$ / $[0, 1]$ | $S_1$ + opponent cash, cash delta ($p\_cash - opp\_cash$), opponent visible workers, opponent visible crops, opponent cows/sheep/geese, opponent quadrants. **(Primary Default)** |
| **$S_3$** | Derived Opportunities | **80** | $[0, 1]$ | $S_2$ + liquidity stress index, preempt sell opportunity signals (Milk, Wool, Melon, Strawberry), market glut warning signals. |

---

## 3. Detailed Variable Dictionary ($S_2$ Tier)

### 3.1 Capital & Labor (10 dims)
- `cash / 100,000.0`: Normalized current balance.
- `liquid_inventory_value / 50,000.0`: Valuation of shed stock at current spot prices.
- `min(1.0, wage_runway_days / 10.0)`: Days of wages remaining before insolvency.
- `committed_wages_today / 500.0`: Outstanding daily wages owed to hired hands today.
- `active_workers / 12.0`: Total current workforce (Farmer + hands).
- `next_hire_cost / 100.0`: Fibonacci cost of next hire today.
- `chore_backlog / 30.0`: Unwatered crops + unfed animals + uncared animals + weeds.
- `idle_hands_count / 12.0`: Surplus workers available above pending chores.

### 3.2 Crops & Arable Land (10 dims)
- `planted_crop_counts[crop] / 20.0`: Wheat, Carrot, Tomato, Strawberry, Melon counts.
- `unwatered_crops_count / 30.0`: Urgent watering chores pending.
- `vacant_arable_count / 50.0`: Arable tiles ready for seeding.
- `weed_count / 20.0`: Obstructing weeds requiring digging.

### 3.3 Livestock & Feed Security (8 dims)
- `cow_count / 10.0`, `sheep_count / 10.0`, `goose_count / 10.0`: Animal inventory.
- `unfed_animals_count / 15.0`: Urgent feeding chores pending.
- `uncared_animals_count / 15.0`: Daily petting/care chores pending.
- `empty_pastures_count / 10.0`: Pre-built pastures awaiting livestock purchase.
- `min(1.0, feed_reserve_days / 10.0)`: Wheat in shed divided by daily feed demand.
- `wheat_in_shed / 50.0`: Raw wheat stockpile for feeding.

### 3.4 Land & Expansion (2 dims)
- `unlocked_quadrants / 4.0`: Quadrants owned (1 to 4).
- `next_land_cost / 4000.0`: Cost of next quadrant (1000, 2000, 4000, or 0).

### 3.5 Market & Town Dynamics (31 dims)
- `spot_prices[product] / 300.0`: Current market spot prices for 9 commodities.
- `price_deltas[product] / 50.0`: 1-step price change indicating recent market momentum.
- `shed_inventory[product] / 50.0`: Quantity held in shed across 9 products.
- `unlocked_shops`: One-hot indicators for Bakery, Dairy, Textile, Pet Cafe.

### 3.6 Time & Opponent Observables (10 dims)
- `step / 720.0`: Normalized game timeline.
- `(step % 4) / 4.0`: Distance to town consumption clearing tick.
- `(step % 24) / 24.0`: Hour of day.
- `is_terminal_window`: Indicator for steps $\ge 712$.
- `opp_cash / 100,000.0`: Opponent visible farm cash.
- `(cash - opp_cash) / 50,000.0`: Relative cash margin.
- `opp_workers / 12.0`: Opponent total active workforce.
- `opp_crops / 50.0`: Opponent planted crop count.
- `opp_cows / 10.0`, `opp_sheep / 10.0`, `opp_geese / 10.0`: Opponent animal counts.
- `opp_quadrants / 4.0`: Opponent unlocked land quadrants.

---

## 4. Observability & Anti-Leakage Audit (§59)

A line-by-line inspection of `candidates/v32_rlx2/state.py` confirms:
1. **Zero Access to Private Opponent State:** Opponent shed, seeds, and worker inventory are never read.
2. **Zero Access to Hidden Simulation Fields:** No access to simulator random generator, future shop unlock order, or future seed weather.
3. **Deterministic & Idempotent:** Feature extraction is a pure mathematical function of the current turn's legal observation.
4. **Runtime Verification:** Tested and passed 100% clean across all development seeds (`test_feature_dimensions` in `test_env.py`).
