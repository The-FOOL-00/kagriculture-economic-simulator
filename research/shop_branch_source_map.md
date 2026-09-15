# Canonical V66 Lineage: Comprehensive Shop-Dependent Branch Source Map

This document exhaustively catalogs every route decision, mode switch, and conditional branch across the canonical lineage (**V66 $\to$ V65 $\to$ V62 $\to$ V60 $\to$ V59 $\to$ V58 $\to$ V56 $\to$ V54**) that depends directly or indirectly on town shop states (`YARN_STORE`, `BAKERY`, `ICE_CREAM_SHOP`, `FARMERS_MARKET`, `PET_CAFE`, `PIZZA_SHOP`, `SMOOTHIE_SHOP`, `BRUNCH_SPOT`).

---

| Branch ID | Source File | Function | Line(s) | Trigger Step | Shop Dependency | Route Selected | Exact Predicate Expression |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **V66_BRANCH_01_TWOMOON** | `candidate_v66_meta_closed_loop.py` | `_advance(obs, visible)` | 314-315 | Step 72 | **BRUNCH_SPOT (requires exact opponent/market signature)** | `yarn (_BASE._V56_YARN_ROUTE)` | `step == 72 and not curve_active and signature == _TWOMOON_STEP72 (where signature[0] == ('BRUNCH_SPOT',))` |
| **V66_BRANCH_02_YAT** | `candidate_v66_meta_closed_loop.py` | `_advance(obs, visible)` | 316-317 | Step 72 | **FARMERS_MARKET (requires exact opponent/market signature)** | `recovery (_BASE._V58_RECOVERY_ROUTE)` | `step == 72 and not curve_active and signature == _YAT_STEP72 (where signature[0] == ('FARMERS_MARKET',))` |
| **V66_BRANCH_03_VICTOR_ARM** | `candidate_v66_meta_closed_loop.py` | `_advance(obs, visible)` | 318-320 | Step 72 | **FARMERS_MARKET (arms two-stage check)** | `state['victor_armed'] = True` | `step == 72 and not curve_active and signature == _VICTOR_STEP72 (where signature[0] == ('FARMERS_MARKET',))` |
| **V66_BRANCH_03_VICTOR_CONFIRM** | `candidate_v66_meta_closed_loop.py` | `_advance(obs, visible)` | 340-345 | Step 144 | **FARMERS_MARKET + YARN_STORE** | `clone (_BASE._V58_CLONE_ROUTE)` | `step == 144 and state['victor_armed'] and _public_signature(obs) == _VICTOR_STEP144 (where signature[0] == ('FARMERS_MARKET', 'YARN_STORE'))` |
| **V66_BRANCH_04_BAKERY_STAGE1** | `candidate_v66_meta_closed_loop.py` | `_advance(obs, visible)` | 321-322 | Step 72 | **BAKERY** | `bakery_yarn (_BASE._V58_BAKERY_YARN_ROUTE)` | `step == 72 and not curve_active and signature == _BAKERY_STEP72 (where signature[0] == ('BAKERY',))` |
| **V66_BRANCH_04_BAKERY_STAGE2** | `candidate_v66_meta_closed_loop.py` | `_advance(obs, visible)` | 346-348 | Step 144 | **BAKERY + YARN_STORE** | `bakery_yarn (_BASE._V58_BAKERY_YARN_ROUTE) if second == 'YARN_STORE' else recovery (_BASE._V58_RECOVERY_ROUTE)` | `step == 144 and state['branch'] == 'bakery' and (second == 'YARN_STORE' -> 'bakery_yarn' else 'recovery')` |
| **V66_BRANCH_05_FARMERS_STAGE1** | `candidate_v66_meta_closed_loop.py` | `_advance(obs, visible)` | 323-324 | Step 72 | **FARMERS_MARKET** | `recovery (_BASE._V58_RECOVERY_ROUTE)` | `step == 72 and not curve_active and signature == _FARMERS_STEP72 (where signature[0] == ('FARMERS_MARKET',))` |
| **V66_BRANCH_05_FARMERS_STAGE2** | `candidate_v66_meta_closed_loop.py` | `_advance(obs, visible)` | 349-351 | Step 144 | **FARMERS_MARKET + YARN_STORE (Key driver of seeds 204 & 208!)** | `yarn (_BASE._V56_YARN_ROUTE) if second == 'YARN_STORE' else recovery (_BASE._V58_RECOVERY_ROUTE)` | `step == 144 and state['branch'] == 'farmers' and (second == 'YARN_STORE' -> 'yarn' else 'recovery')` |
| **V66_BRANCH_06_NEIBYR** | `candidate_v66_meta_closed_loop.py` | `_advance(obs, visible)` | 325-326 | Step 72 | **PIZZA_SHOP** | `recovery (_BASE._V58_RECOVERY_ROUTE)` | `step == 72 and not curve_active and signature == _NEIBYR_STEP72 (where signature[0] == ('PIZZA_SHOP',))` |
| **V66_BRANCH_07_C0NRAD** | `candidate_v66_meta_closed_loop.py` | `_advance(obs, visible)` | 327-328 | Step 72 | **FARMERS_MARKET** | `ice_minimax (_BASE._V58_ICE_MINIMAX_ROUTE)` | `step == 72 and not curve_active and signature == _C0NRAD_STEP72 (where signature[0] == ('FARMERS_MARKET',))` |
| **V66_BRANCH_08_JOHNBLAKE** | `candidate_v66_meta_closed_loop.py` | `_advance(obs, visible)` | 329-330 | Step 72 | **BRUNCH_SPOT** | `known_yarn (_BASE._V58_KNOWN_YARN_ROUTE)` | `step == 72 and not curve_active and signature == _JOHNBLAKE_STEP72 (where signature[0] == ('BRUNCH_SPOT',))` |
| **V66_BRANCH_09_STEPHEN** | `candidate_v66_meta_closed_loop.py` | `_advance(obs, visible)` | 331-332 | Step 72 | **BRUNCH_SPOT** | `known_yarn (_BASE._V58_KNOWN_YARN_ROUTE)` | `step == 72 and not curve_active and signature == _STEPHEN_STEP72 (where signature[0] == ('BRUNCH_SPOT',))` |
| **V66_BRANCH_10_COKE_ARM** | `candidate_v66_meta_closed_loop.py` | `_advance(obs, visible)` | 333-335 | Step 72 | **ICE_CREAM_SHOP** | `state['coke_armed'] = True` | `step == 72 and not curve_active and signature == _COKE_STEP72 (where signature[0] == ('ICE_CREAM_SHOP',))` |
| **V66_BRANCH_10_COKE_CONFIRM** | `candidate_v66_meta_closed_loop.py` | `_advance(obs, visible)` | 352-357 | Step 144 | **ICE_CREAM_SHOP + BRUNCH_SPOT** | `known_yarn (_BASE._V58_KNOWN_YARN_ROUTE)` | `step == 144 and state['coke_armed'] and _public_signature(obs) == _COKE_STEP144 (where signature[0] == ('ICE_CREAM_SHOP', 'BRUNCH_SPOT'))` |
| **V65_BRANCH_11_CYGN_CLONE** | `candidate_v65_curve_cygn_clone.py` | `kaggle_agent_v65_curve_cygn_clone` | 41-43 | Step 144 | **YARN_STORE + PIZZA_SHOP** | `_CLONE (_BASE._V58_CLONE_ROUTE)` | `curve_active and step >= 144 and tuple(_BASE._v58_shops(obs)[:2]) == ('YARN_STORE', 'PIZZA_SHOP')` |
| **V65_BRANCH_12_KNOWN_YARN_REPAIR** | `candidate_v65_curve_q2_known_yarn_repair.py` | `kaggle_agent_v65_curve_q2_known_yarn_repair` | 110-113 | Step 72 | **FARMERS_MARKET** | `_KNOWN_YARN (_BASE._V58_KNOWN_YARN_ROUTE)` | `step == 72 and curve_active and _public_signature(obs) == _CURVE_Q2_REPAIR_STEP72 (where signature[0] == ('FARMERS_MARKET',))` |
| **V65_BRANCH_13_DANIEL_BACKBONE** | `candidate_v65_curve_q2_daniel_backbone.py` | `kaggle_agent_v65_curve_q2_daniel_backbone` | 53-56 | Step 72 | **SMOOTHIE_SHOP** | `_BACKBONE (_BASE._V56_BACKBONE_ROUTE)` | `step == 72 and curve_active and _Q2._public_signature(obs) == (('SMOOTHIE_SHOP',),) + ...` |
| **V65_BRANCH_14_ATTACK_YARN** | `candidate_v65_local_combined.py` | `_attack_advance` | 96-102 | Step 72 | **BAKERY / BRUNCH_SPOT / FARMERS_MARKET** | `base_yarn (_BASE._V56_YARN_ROUTE)` | `shops[0] in {'BAKERY', 'BRUNCH_SPOT', 'FARMERS_MARKET'} and mine money 149, rival 724, wheat 9975/30` |
| **V62_BRANCH_15_DEFAULT_FIRST_YARN** | `candidate_v62_composite_bakery_yarn.py` | `_v58_base_action / _v59_route` | 3656 / 3902-3903 | Step 72 | **YARN_STORE (Pure public shop rule! No opponent matching required!)** | `_V56_YARN_ROUTE` | `first == 'YARN_STORE'` |
| **V62_BRANCH_16_PET_CAFE_ROUTE** | `candidate_v62_composite_bakery_yarn.py` | `_v58_base_action / _v59_route` | 3658-3662 / 3904-3910 | Step 144 | **PET_CAFE + any legal second shop** | `_V57_PET_ROUTE` | `first == 'PET_CAFE' and step >= 144 and len(shops) >= 2 and shops[1] in {'BAKERY', 'BRUNCH_SPOT', 'FARMERS_MARKET', 'ICE_CREAM_SHOP', 'PET_CAFE', 'PIZZA_SHOP', 'SMOOTHIE_SHOP', 'YARN_STORE'}` |
| **V58_BRANCH_17_FARMERS_SMOOTHIE** | `candidate_v62_composite_bakery_yarn.py` | `_v59_route` | 3880-3883 | Step 144 | **FARMERS_MARKET (step 72) + SMOOTHIE_SHOP (step 144)** | `_V58_SMOOTHIE_ROUTE (else _V58_RECOVERY_ROUTE)` | `mode == 'farmers-recovery' and future_step >= 144 and len(shops) >= 2 and shops[1] == 'SMOOTHIE_SHOP'` |
| **V58_BRANCH_18_BAKERY_YARN** | `candidate_v62_composite_bakery_yarn.py` | `_v59_route` | 3888-3891 | Step 144 | **BAKERY (step 72) + YARN_STORE (step 144)** | `_V58_BAKERY_YARN_ROUTE (else _V56_BACKBONE_ROUTE)` | `mode == 'bakery-second-shop' and future_step >= 144 and len(shops) >= 2 and shops[1] == 'YARN_STORE'` |
| **V58_BRANCH_19_PIZZA_PET** | `candidate_v62_composite_bakery_yarn.py` | `_v59_route` | 3892-3895 | Step 144 | **PIZZA_SHOP (step 72) + PET_CAFE (step 144)** | `_V58_PIZZA_RECOVERY_ROUTE (else _V56_BACKBONE_ROUTE)` | `mode == 'pizza-second-shop' and future_step >= 144 and len(shops) >= 2 and shops[1] == 'PET_CAFE'` |
| **V58_BRANCH_20_KNOWN_YARN** | `candidate_v62_composite_bakery_yarn.py` | `_v59_route / _v58_known_yarn` | 3828-3831 / 3733-3754 | Step 96 | **YARN_STORE** | `_V58_KNOWN_YARN_ROUTE` | `shops[0] == 'YARN_STORE' and (mine, opp, wheat, animals) in {(214, 214, 9982, 4, 2, 7, 12), (215, 125, 9979, 4, 2, 7, 12)}` |
| **V58_BRANCH_21_CLONE** | `candidate_v62_composite_bakery_yarn.py` | `_v59_route` | 3833-3841 | Step 360 | **YARN_STORE + exact opponent public farm clone** | `_V58_CLONE_ROUTE` | `shops[0] == 'YARN_STORE' and step >= 360 and mirror_streak >= 240` |
| **V56_BRANCH_22_BASE_BACKBONE** | `candidate_v62_composite_bakery_yarn.py` | `_v59_route` | 3911 | Step 0 | **None (default macro backbone prior)** | `_V56_BACKBONE_ROUTE` | `True (fallback default)` |
| **V54_BRANCH_23_STATIC_ROUTE** | `main.py` | `kaggle_agent` | 1-120 | Step 0 | **None (Blind to all town shops)** | `r007-1-flow3-h2q4 static route` | `None (Zero shop adaptation; completely blind to unlocked_shops)` |

---

## Detailed Branch Forensics

### V66_BRANCH_01_TWOMOON
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v66_meta_closed_loop.py)
- **Function**: `_advance(obs, visible)` (Lines 314-315)
- **Input State**: `step == 72, not curve_active, signature == _TWOMOON_STEP72`
- **Exact Condition**: `step == 72 and not curve_active and signature == _TWOMOON_STEP72 (where signature[0] == ('BRUNCH_SPOT',))`
- **Route Selected**: `yarn (_BASE._V56_YARN_ROUTE)`
- **Step Range**: Steps 72 to 718
- **Shop Dependency Analysis**: BRUNCH_SPOT (requires exact opponent/market signature)

### V66_BRANCH_02_YAT
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v66_meta_closed_loop.py)
- **Function**: `_advance(obs, visible)` (Lines 316-317)
- **Input State**: `step == 72, not curve_active, signature == _YAT_STEP72`
- **Exact Condition**: `step == 72 and not curve_active and signature == _YAT_STEP72 (where signature[0] == ('FARMERS_MARKET',))`
- **Route Selected**: `recovery (_BASE._V58_RECOVERY_ROUTE)`
- **Step Range**: Steps 72 to 718
- **Shop Dependency Analysis**: FARMERS_MARKET (requires exact opponent/market signature)

### V66_BRANCH_03_VICTOR_ARM
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v66_meta_closed_loop.py)
- **Function**: `_advance(obs, visible)` (Lines 318-320)
- **Input State**: `step == 72, not curve_active, signature == _VICTOR_STEP72`
- **Exact Condition**: `step == 72 and not curve_active and signature == _VICTOR_STEP72 (where signature[0] == ('FARMERS_MARKET',))`
- **Route Selected**: `state['victor_armed'] = True`
- **Step Range**: Steps 72 to 143
- **Shop Dependency Analysis**: FARMERS_MARKET (arms two-stage check)

### V66_BRANCH_03_VICTOR_CONFIRM
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v66_meta_closed_loop.py)
- **Function**: `_advance(obs, visible)` (Lines 340-345)
- **Input State**: `step == 144, state['victor_armed'], signature == _VICTOR_STEP144`
- **Exact Condition**: `step == 144 and state['victor_armed'] and _public_signature(obs) == _VICTOR_STEP144 (where signature[0] == ('FARMERS_MARKET', 'YARN_STORE'))`
- **Route Selected**: `clone (_BASE._V58_CLONE_ROUTE)`
- **Step Range**: Steps 144 to 718
- **Shop Dependency Analysis**: FARMERS_MARKET + YARN_STORE

### V66_BRANCH_04_BAKERY_STAGE1
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v66_meta_closed_loop.py)
- **Function**: `_advance(obs, visible)` (Lines 321-322)
- **Input State**: `step == 72, not curve_active, signature == _BAKERY_STEP72`
- **Exact Condition**: `step == 72 and not curve_active and signature == _BAKERY_STEP72 (where signature[0] == ('BAKERY',))`
- **Route Selected**: `bakery_yarn (_BASE._V58_BAKERY_YARN_ROUTE)`
- **Step Range**: Steps 72 to 143
- **Shop Dependency Analysis**: BAKERY

### V66_BRANCH_04_BAKERY_STAGE2
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v66_meta_closed_loop.py)
- **Function**: `_advance(obs, visible)` (Lines 346-348)
- **Input State**: `step == 144, state['branch'] == 'bakery', second shop observed`
- **Exact Condition**: `step == 144 and state['branch'] == 'bakery' and (second == 'YARN_STORE' -> 'bakery_yarn' else 'recovery')`
- **Route Selected**: `bakery_yarn (_BASE._V58_BAKERY_YARN_ROUTE) if second == 'YARN_STORE' else recovery (_BASE._V58_RECOVERY_ROUTE)`
- **Step Range**: Steps 144 to 718
- **Shop Dependency Analysis**: BAKERY + YARN_STORE

### V66_BRANCH_05_FARMERS_STAGE1
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v66_meta_closed_loop.py)
- **Function**: `_advance(obs, visible)` (Lines 323-324)
- **Input State**: `step == 72, not curve_active, signature == _FARMERS_STEP72`
- **Exact Condition**: `step == 72 and not curve_active and signature == _FARMERS_STEP72 (where signature[0] == ('FARMERS_MARKET',))`
- **Route Selected**: `recovery (_BASE._V58_RECOVERY_ROUTE)`
- **Step Range**: Steps 72 to 143
- **Shop Dependency Analysis**: FARMERS_MARKET

### V66_BRANCH_05_FARMERS_STAGE2
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v66_meta_closed_loop.py)
- **Function**: `_advance(obs, visible)` (Lines 349-351)
- **Input State**: `step == 144, state['branch'] == 'farmers', second shop observed`
- **Exact Condition**: `step == 144 and state['branch'] == 'farmers' and (second == 'YARN_STORE' -> 'yarn' else 'recovery')`
- **Route Selected**: `yarn (_BASE._V56_YARN_ROUTE) if second == 'YARN_STORE' else recovery (_BASE._V58_RECOVERY_ROUTE)`
- **Step Range**: Steps 144 to 718
- **Shop Dependency Analysis**: FARMERS_MARKET + YARN_STORE (Key driver of seeds 204 & 208!)

### V66_BRANCH_06_NEIBYR
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v66_meta_closed_loop.py)
- **Function**: `_advance(obs, visible)` (Lines 325-326)
- **Input State**: `step == 72, not curve_active, signature == _NEIBYR_STEP72`
- **Exact Condition**: `step == 72 and not curve_active and signature == _NEIBYR_STEP72 (where signature[0] == ('PIZZA_SHOP',))`
- **Route Selected**: `recovery (_BASE._V58_RECOVERY_ROUTE)`
- **Step Range**: Steps 72 to 718
- **Shop Dependency Analysis**: PIZZA_SHOP

### V66_BRANCH_07_C0NRAD
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v66_meta_closed_loop.py)
- **Function**: `_advance(obs, visible)` (Lines 327-328)
- **Input State**: `step == 72, not curve_active, signature == _C0NRAD_STEP72`
- **Exact Condition**: `step == 72 and not curve_active and signature == _C0NRAD_STEP72 (where signature[0] == ('FARMERS_MARKET',))`
- **Route Selected**: `ice_minimax (_BASE._V58_ICE_MINIMAX_ROUTE)`
- **Step Range**: Steps 72 to 718
- **Shop Dependency Analysis**: FARMERS_MARKET

### V66_BRANCH_08_JOHNBLAKE
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v66_meta_closed_loop.py)
- **Function**: `_advance(obs, visible)` (Lines 329-330)
- **Input State**: `step == 72, not curve_active, signature == _JOHNBLAKE_STEP72`
- **Exact Condition**: `step == 72 and not curve_active and signature == _JOHNBLAKE_STEP72 (where signature[0] == ('BRUNCH_SPOT',))`
- **Route Selected**: `known_yarn (_BASE._V58_KNOWN_YARN_ROUTE)`
- **Step Range**: Steps 72 to 718
- **Shop Dependency Analysis**: BRUNCH_SPOT

### V66_BRANCH_09_STEPHEN
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v66_meta_closed_loop.py)
- **Function**: `_advance(obs, visible)` (Lines 331-332)
- **Input State**: `step == 72, not curve_active, signature == _STEPHEN_STEP72`
- **Exact Condition**: `step == 72 and not curve_active and signature == _STEPHEN_STEP72 (where signature[0] == ('BRUNCH_SPOT',))`
- **Route Selected**: `known_yarn (_BASE._V58_KNOWN_YARN_ROUTE)`
- **Step Range**: Steps 72 to 718
- **Shop Dependency Analysis**: BRUNCH_SPOT

### V66_BRANCH_10_COKE_ARM
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v66_meta_closed_loop.py)
- **Function**: `_advance(obs, visible)` (Lines 333-335)
- **Input State**: `step == 72, not curve_active, signature == _COKE_STEP72`
- **Exact Condition**: `step == 72 and not curve_active and signature == _COKE_STEP72 (where signature[0] == ('ICE_CREAM_SHOP',))`
- **Route Selected**: `state['coke_armed'] = True`
- **Step Range**: Steps 72 to 143
- **Shop Dependency Analysis**: ICE_CREAM_SHOP

### V66_BRANCH_10_COKE_CONFIRM
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v66_meta_closed_loop.py)
- **Function**: `_advance(obs, visible)` (Lines 352-357)
- **Input State**: `step == 144, state['coke_armed'], signature == _COKE_STEP144`
- **Exact Condition**: `step == 144 and state['coke_armed'] and _public_signature(obs) == _COKE_STEP144 (where signature[0] == ('ICE_CREAM_SHOP', 'BRUNCH_SPOT'))`
- **Route Selected**: `known_yarn (_BASE._V58_KNOWN_YARN_ROUTE)`
- **Step Range**: Steps 144 to 718
- **Shop Dependency Analysis**: ICE_CREAM_SHOP + BRUNCH_SPOT

### V65_BRANCH_11_CYGN_CLONE
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v65_curve_cygn_clone.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v65_curve_cygn_clone.py)
- **Function**: `kaggle_agent_v65_curve_cygn_clone` (Lines 41-43)
- **Input State**: `curve_active, step >= 144, shops == ('YARN_STORE', 'PIZZA_SHOP')`
- **Exact Condition**: `curve_active and step >= 144 and tuple(_BASE._v58_shops(obs)[:2]) == ('YARN_STORE', 'PIZZA_SHOP')`
- **Route Selected**: `_CLONE (_BASE._V58_CLONE_ROUTE)`
- **Step Range**: Steps 144 to 718
- **Shop Dependency Analysis**: YARN_STORE + PIZZA_SHOP

### V65_BRANCH_12_KNOWN_YARN_REPAIR
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v65_curve_q2_known_yarn_repair.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v65_curve_q2_known_yarn_repair.py)
- **Function**: `kaggle_agent_v65_curve_q2_known_yarn_repair` (Lines 110-113)
- **Input State**: `step == 72, curve_active, signature == _CURVE_Q2_REPAIR_STEP72`
- **Exact Condition**: `step == 72 and curve_active and _public_signature(obs) == _CURVE_Q2_REPAIR_STEP72 (where signature[0] == ('FARMERS_MARKET',))`
- **Route Selected**: `_KNOWN_YARN (_BASE._V58_KNOWN_YARN_ROUTE)`
- **Step Range**: Steps 72 to 718
- **Shop Dependency Analysis**: FARMERS_MARKET

### V65_BRANCH_13_DANIEL_BACKBONE
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v65_curve_q2_daniel_backbone.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v65_curve_q2_daniel_backbone.py)
- **Function**: `kaggle_agent_v65_curve_q2_daniel_backbone` (Lines 53-56)
- **Input State**: `step == 72, curve_active, signature == _DANIEL_STEP72`
- **Exact Condition**: `step == 72 and curve_active and _Q2._public_signature(obs) == (('SMOOTHIE_SHOP',),) + ...`
- **Route Selected**: `_BACKBONE (_BASE._V56_BACKBONE_ROUTE)`
- **Step Range**: Steps 72 to 718
- **Shop Dependency Analysis**: SMOOTHIE_SHOP

### V65_BRANCH_14_ATTACK_YARN
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v65_local_combined.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v65_local_combined.py)
- **Function**: `_attack_advance` (Lines 96-102)
- **Input State**: `step == 72, state['armed'] (from step 1), signature matches _attack_step72_signature`
- **Exact Condition**: `shops[0] in {'BAKERY', 'BRUNCH_SPOT', 'FARMERS_MARKET'} and mine money 149, rival 724, wheat 9975/30`
- **Route Selected**: `base_yarn (_BASE._V56_YARN_ROUTE)`
- **Step Range**: Steps 72 to 718
- **Shop Dependency Analysis**: BAKERY / BRUNCH_SPOT / FARMERS_MARKET

### V62_BRANCH_15_DEFAULT_FIRST_YARN
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v62_composite_bakery_yarn.py)
- **Function**: `_v58_base_action / _v59_route` (Lines 3656 / 3902-3903)
- **Input State**: `shops[0] == 'YARN_STORE'`
- **Exact Condition**: `first == 'YARN_STORE'`
- **Route Selected**: `_V56_YARN_ROUTE`
- **Step Range**: Steps 72 to 718
- **Shop Dependency Analysis**: YARN_STORE (Pure public shop rule! No opponent matching required!)

### V62_BRANCH_16_PET_CAFE_ROUTE
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v62_composite_bakery_yarn.py)
- **Function**: `_v58_base_action / _v59_route` (Lines 3658-3662 / 3904-3910)
- **Input State**: `first == 'PET_CAFE', future_step >= 144, shops[1] in _V57_PET_SECOND_SHOPS`
- **Exact Condition**: `first == 'PET_CAFE' and step >= 144 and len(shops) >= 2 and shops[1] in {'BAKERY', 'BRUNCH_SPOT', 'FARMERS_MARKET', 'ICE_CREAM_SHOP', 'PET_CAFE', 'PIZZA_SHOP', 'SMOOTHIE_SHOP', 'YARN_STORE'}`
- **Route Selected**: `_V57_PET_ROUTE`
- **Step Range**: Steps 144 to 718
- **Shop Dependency Analysis**: PET_CAFE + any legal second shop

### V58_BRANCH_17_FARMERS_SMOOTHIE
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v62_composite_bakery_yarn.py)
- **Function**: `_v59_route` (Lines 3880-3883)
- **Input State**: `mode == 'farmers-recovery', step >= 144, shops[1] == 'SMOOTHIE_SHOP'`
- **Exact Condition**: `mode == 'farmers-recovery' and future_step >= 144 and len(shops) >= 2 and shops[1] == 'SMOOTHIE_SHOP'`
- **Route Selected**: `_V58_SMOOTHIE_ROUTE (else _V58_RECOVERY_ROUTE)`
- **Step Range**: Steps 144 to 718
- **Shop Dependency Analysis**: FARMERS_MARKET (step 72) + SMOOTHIE_SHOP (step 144)

### V58_BRANCH_18_BAKERY_YARN
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v62_composite_bakery_yarn.py)
- **Function**: `_v59_route` (Lines 3888-3891)
- **Input State**: `mode == 'bakery-second-shop', step >= 144, shops[1] == 'YARN_STORE'`
- **Exact Condition**: `mode == 'bakery-second-shop' and future_step >= 144 and len(shops) >= 2 and shops[1] == 'YARN_STORE'`
- **Route Selected**: `_V58_BAKERY_YARN_ROUTE (else _V56_BACKBONE_ROUTE)`
- **Step Range**: Steps 144 to 718
- **Shop Dependency Analysis**: BAKERY (step 72) + YARN_STORE (step 144)

### V58_BRANCH_19_PIZZA_PET
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v62_composite_bakery_yarn.py)
- **Function**: `_v59_route` (Lines 3892-3895)
- **Input State**: `mode == 'pizza-second-shop', step >= 144, shops[1] == 'PET_CAFE'`
- **Exact Condition**: `mode == 'pizza-second-shop' and future_step >= 144 and len(shops) >= 2 and shops[1] == 'PET_CAFE'`
- **Route Selected**: `_V58_PIZZA_RECOVERY_ROUTE (else _V56_BACKBONE_ROUTE)`
- **Step Range**: Steps 144 to 718
- **Shop Dependency Analysis**: PIZZA_SHOP (step 72) + PET_CAFE (step 144)

### V58_BRANCH_20_KNOWN_YARN
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v62_composite_bakery_yarn.py)
- **Function**: `_v59_route / _v58_known_yarn` (Lines 3828-3831 / 3733-3754)
- **Input State**: `step == 96, shops[0] == 'YARN_STORE', signature matches known continuation`
- **Exact Condition**: `shops[0] == 'YARN_STORE' and (mine, opp, wheat, animals) in {(214, 214, 9982, 4, 2, 7, 12), (215, 125, 9979, 4, 2, 7, 12)}`
- **Route Selected**: `_V58_KNOWN_YARN_ROUTE`
- **Step Range**: Steps 96 to 718
- **Shop Dependency Analysis**: YARN_STORE

### V58_BRANCH_21_CLONE
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v62_composite_bakery_yarn.py)
- **Function**: `_v59_route` (Lines 3833-3841)
- **Input State**: `step >= 72, shops[0] == 'YARN_STORE', mirror_streak >= 240 at step 360`
- **Exact Condition**: `shops[0] == 'YARN_STORE' and step >= 360 and mirror_streak >= 240`
- **Route Selected**: `_V58_CLONE_ROUTE`
- **Step Range**: Steps 360 to 718
- **Shop Dependency Analysis**: YARN_STORE + exact opponent public farm clone

### V56_BRANCH_22_BASE_BACKBONE
- **Source File**: [`external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-v66-agent\candidate_v62_composite_bakery_yarn.py)
- **Function**: `_v59_route` (Lines 3911)
- **Input State**: `Default fallback if no shop branch condition triggers`
- **Exact Condition**: `True (fallback default)`
- **Route Selected**: `_V56_BACKBONE_ROUTE`
- **Step Range**: Steps 0 to 718
- **Shop Dependency Analysis**: None (default macro backbone prior)

### V54_BRANCH_23_STATIC_ROUTE
- **Source File**: [`external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py`](file:///C:\Users\Sundareswaran\Kagriculture\external_repos\lixingtao123-Kaggriculture\variant_v54_h3q4\main.py)
- **Function**: `kaggle_agent` (Lines 1-120)
- **Input State**: `All steps`
- **Exact Condition**: `None (Zero shop adaptation; completely blind to unlocked_shops)`
- **Route Selected**: `r007-1-flow3-h2q4 static route`
- **Step Range**: Steps 0 to 718
- **Shop Dependency Analysis**: None (Blind to all town shops)

