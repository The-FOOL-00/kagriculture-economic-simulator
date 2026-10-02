# V53 Current Engine Version & Parity Specification

## 1. Installed Environment & Engine Metadata

In accordance with Section 1 of the V53 Research Specification, the installed competition environment has been fully audited:

- **Installed `kaggle-environments` Version**: `1.32.7`
  - *Compliance*: Fulfills the official organizer mandate requiring `kaggle-environments >= 1.32.6`.
  - *Package Location*: `C:\Users\Sundareswaran\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\kaggle_environments`
- **Active Kaggriculture Module**: `kaggle_environments.envs.kaggriculture`
  - Engine Source File: `kaggriculture.py` (40,356 bytes)
  - Engine SHA256: `bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e`
  - Schema File: `kaggriculture.json` (6,002 bytes)
  - Schema SHA256: `a82c89c1a2315b93f39775d8e025471a01b738647c9772658368ee6b1b6f4867`

---

## 2. FastSim Engine Implementation & Architecture

- **FastSim Source File**: `research/v40/env/fast_sim.py`
  - SHA256: `ecb0c3d1da3795f01ea14c19fa3ae4a5ce8a2fe4019cc9a707d14fb8504ea7c8`
- **Architecture**:
  - `FastKagricultureSim` is **not** a bespoke re-implementation or loose approximation of the game mechanics.
  - It directly imports the official installed package (`import kaggle_environments.envs.kaggriculture.kaggriculture as kg`).
  - During `reset()`, it invokes `kg._initialize(self.state, self)`.
  - During `step()`, it passes actions and invokes `kg.interpreter(self.state, self)`.
  - The performance acceleration (12–14x speedup, ~500 SPS) is achieved solely by bypassing redundant JSON schema validation, dictionary deepcopies, and stdout redirection on every step, while executing the identical underlying Python functions of the official engine.

---

## 3. Mid-Competition Balance Change Verification

We directly audited the source code of the active engine (`kaggriculture.py`) against all documented mid-competition balance changes:

1. **Town Center Demand Interval**:
   - `kaggriculture.py` line 734:
     ```python
     center_interval = max(1, int(get(cfg, "townCenterSellInterval", 24)))
     ```
   - *Status*: Verified. Town Center demand consumes exactly once per day (every 24 steps), consuming 1 unit of each product (`TOWN_CENTER_PRODUCTS`).
2. **Shop Sampling With Replacement**:
   - `kaggriculture.py` lines 886–891:
     ```python
     if next_day > 0 and next_day % shop_interval == 0:
         # Drawn with replacement: the same shop can unlock repeatedly, and each
         # copy consumes independently. Variety is not guaranteed; only the total
         # instance count is capped.
         if len(town["unlocked_shops"]) < MAX_SHOP_INSTANCES:
             town["unlocked_shops"].append(rng.choice(sorted(SHOPS)))
     ```
   - *Status*: Verified. Shops are drawn with replacement up to `MAX_SHOP_INSTANCES = 8`.
3. **Shop Demand Multipliers**:
   - `kaggriculture.py` lines 739–744:
     ```python
     for shop_name in town.get("unlocked_shops", []):
         products = SHOPS[shop_name]
         multiplier = 2 if len(products) == 1 else 1
         for item in products:
             market["inventory"][item] -= multiplier
     ```
   - *Status*: Verified. Unlocked shops consume every 4 steps (`townShopSellInterval = 4`), with duplicate shops consuming independently.

All mid-competition balance updates are fully and natively active in our execution environment.
