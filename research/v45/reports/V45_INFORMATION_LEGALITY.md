# V45 Information-Legality Contract & Runtime Feature Specification

**Document ID:** `research/v45/reports/V45_INFORMATION_LEGALITY.md`  
**Date:** 2026-09-25  
**Repository:** `The-FOOL-00/kagriculture-economic-simulator`  
**Compliance Standard:** Strict Kaggle Environment Public State Legal Contract  

---

## 1. Core Principle & Legal Separation

In competitive Kagriculture, each agent receives a state dictionary $S_t$ at step $t$. $S_t$ contains both public information (accessible to all observers) and private information (restricted to player $i$).

To maintain complete competitive legality and prevent lookahead or information leakage:
1. **Zero Future Knowledge:** No feature may reference $t' > t$ (no future prices, no future steps, no future labels, no terminal game outcome).
2. **Zero Hidden Opponent Knowledge:** The runtime model must never inspect opponent private fields (e.g. `obs.private` for opponent, opponent hidden seeds, or opponent internal decision variables).
3. **Zero Meta-Information:** The runtime model must never observe the random simulation seed, the opponent identifier string (`opp_id`), the match replay ID, or offline benchmark metadata.
4. **Current-State and Past Observable History Only:** All runtime features are strictly derived from the current public observation and causal historical trajectories up to current step $t$.

---

## 2. Complete Runtime Feature Catalog

The V45 runtime feature extraction pipeline extracts a fixed-dimensional vector $x_t \in \mathbb{R}^{D}$ from legally observable inputs at step $t$:

### A. Temporal & Game Clock Features (4 features)
1. `step_norm`: Current step normalized $t / 720.0 \in [0.0, 1.0]$.
2. `steps_remaining`: $720 - t$.
3. `is_town_shop_tick`: Binary indicator $(t \pmod 4 == 0)$.
4. `is_town_center_tick`: Binary indicator $(t \pmod{24} == 0)$.

### B. Current Market Price & Inventory State (18 features)
For each of the 9 commodities (`CARROT`, `EGG`, `FERTILIZER`, `MELON`, `MILK`, `STRAWBERRY`, `TOMATO`, `WHEAT`, `WOOL`):
1. `price_norm[item]`: Current spot price normalized by canonical base price: $P_t(item) / P_{\text{base}}(item)$.
2. `market_inventory_delta[item]`: Normalized deviation of market inventory from equilibrium $I_0$: $(I_t(item) - I_0(item)) / I_0(item)$.

### C. Recent Price Velocity & Acceleration (18 features)
Computed over trailing observation window $\tau \in \{1, 4\}$ steps:
1. Trailing 1-step price velocity: $\Delta_1 P_t(item) = P_t(item) - P_{t-1}(item)$.
2. Trailing 4-step price velocity: $\Delta_4 P_t(item) = P_t(item) - P_{t-4}(item)$.

### D. Observable Market Volume Imbalances (9 features)
Observed change in market inventory from $t-1$ to $t$:
$$\Delta I_t(item) = I_t(item) - I_{t-1}(item)$$
Accounting for town shop drainage (which is deterministic given unlocked shops), any net addition to $I_t(item)$ represents market selling activity:
$$\text{ObservedMarketDump}_t(item) = \max(0, \Delta I_t(item) + \text{TownDrain}_t(item) - \text{OurSales}_{t-1}(item))$$

### E. Player Financial & Asset State (8 features)
1. `our_cash_norm`: Our liquid money $M_t^{\text{our}} / 10000.0$.
2. `our_shed_qty[item]`: Shed inventory for marketable goods (`STRAWBERRY`, `MILK`, `WOOL`, `MELON`).
3. `our_total_shed_value`: Liquidation value of our shed stock at current spot prices.
4. `our_farm_hands`: Number of active hired workers.
5. `our_quadrants`: Number of unlocked farm quadrants.

### F. Observable Public Opponent State (7 features)
1. `opp_cash_norm`: Opponent public cash from `obs.farms[1-player].money / 10000.0`.
2. `relative_cash_margin`: $(M_t^{\text{our}} - M_t^{\text{opp}}) / 1000.0$.
3. `opp_farm_hands`: Number of active hired workers on opponent's farm (`len(obs.farms[1-player].hands)`).
4. `opp_cash_velocity_4`: Trailing 4-step change in opponent public cash ($M_t^{\text{opp}} - M_{t-4}^{\text{opp}}$).
5. `opp_unlocked_quadrants`: Number of quadrants unlocked by opponent.
6. `opp_visible_crops`: Count of mature/growing crops visible on opponent's farm grid.
7. `opp_visible_animals`: Count of cows, sheep, and geese visible on opponent's farm grid.

---

## 3. Explicit Proscription Matrix

| Category | Status | Runtime Assertion |
| :--- | :---: | :--- |
| `seed` | **FORBIDDEN** | Never passed to agent `act()` or state encoder. |
| `opponent_id` | **FORBIDDEN** | Agent is strictly opponent-agnostic. |
| `replay_id` | **FORBIDDEN** | No match metadata accessed. |
| `future_prices` | **FORBIDDEN** | Strictly causal trailing history. |
| `future_actions` | **FORBIDDEN** | Causal state estimation only. |
| `opponent_shed` | **FORBIDDEN** | `obs.private` for opponent is never inspected. |
| `opponent_seeds` | **FORBIDDEN** | Hidden private seeds never inspected. |
| `terminal_result` | **FORBIDDEN** | Offline evaluation only; 0 exposure at inference. |

---

## 4. Legality Verification Protocol

An automated script `research/v45/audit_feature_leakage.py` performs static and dynamic inspection of the feature pipeline to ensure 100% adherence to this contract prior to any candidate promotion.
