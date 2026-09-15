# Stage 2 — Identify Candidate Causal Variables

**Date & Time**: 2026-09-10T09:14:00+05:30  
**Audit Phase**: STAGE 2 — Candidate Causal Variable Identification  
**Artifact Generated**: [`research/step301_tile_shop_forensics.json`](file:///c:/Users/Sundareswaran/Kagriculture/research/step301_tile_shop_forensics.json)

---

## 1. Test of the "Tile Bonus" Claim

- **Hypothesis**: "Tile bonuses determine route optimality around Step 301."
- **Investigation**: Inspected engine rules and simulator source code in [`kg_env_dump.py`](file:///c:/Users/Sundareswaran/Kagriculture/kg_env_dump.py) across all tile, farm, and grid mechanics.
- **Evidence**:
  - **[FACT]**: The `tiles` data structure in Kaggriculture contains strictly: coordinates `(x, y)`, tile state (`dirt`, `plowed`, `planted`, `watered`), `crop_type`, and `crop_age`.
  - **[FACT]**: Zero tile-specific yield multipliers, soil quality coefficients, or movement speed variations exist anywhere in the game engine.
  - **[FACT]**: The only production multipliers in Kaggriculture are:
    1. Animal care (+1 product per care before milking/shearing).
    2. Town shops (purchasing specific goods at price premiums when unlocked).
- **Verdict**: **REJECTED [FACT]**. Tile bonuses do not exist in the environment. This hypothesis is permanently eliminated.

---

## 2. Test of the "Shop Availability" Claim

- **Hypothesis**: "Public shop unlock sequences at Steps 72, 144, 216, and 288 determine which route is optimal around Step 301."
- **Evidence**:
  - **[FACT]**: When `YARN_STORE` unlocks at Step 72, both agents switch to the Yarn route.
  - **[FACT]**: V54++ already incorporates full public-state gating for Step 144:
    - If `shops[1] == "YARN_STORE"`, it switches to Yarn.
    - If `shops[0] == "BAKERY"` and `shops[1] == "YARN_STORE"`, it switches to Bakery-Yarn.
  - **[FACT]**: In Population A (where V66 wins $\ge \$5\text{k}$), $80\%$ of seeds unlock `BAKERY` at Step 72 or Step 144 without an early `YARN_STORE`.
  - **[INFERENCE]**: When `BAKERY` unlocks early without `YARN_STORE`, V54++ remains on Backbone while V66 accidentally falls back to `_V58_RECOVERY_ROUTE` or `_V58_BAKERY_YARN_ROUTE`.
  - **[HYPOTHESIS]**: Switching routes at Step 216 or Step 288 based on late shop unlocks may improve performance. (To be tested in Stage 3 counterfactuals).

---

## 3. Source-Level V66 Forensics

Audited lines 98–362 of [`candidate_v66_meta_closed_loop.py`](file:///c:/Users/Sundareswaran/Kagriculture/external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py#L98-L362):

- **File**: `external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py`
- **Function**: `_advance` (Lines 300–362)
- **Mechanism**:
  - **[FACT]**: V66 defines `_public_signature(obs)` which reads:
    1. `opponent.get("money")`
    2. `len(opponent["hands"])`
    3. Opponent livestock counts (`cows`, `sheep`)
  - **[FACT]**: V66 checks equality against hardcoded tuples from historical Kaggle replays:
    - `signature == _TWOMOON_STEP72 -> route = 'yarn'`
    - `signature == _YAT_STEP72 -> route = 'recovery'`
    - `signature == _VICTOR_STEP72 -> state['victor_armed'] = True`
    - `signature == _BAKERY_STEP72 -> route = 'bakery_yarn'`
    - `signature == _C0NRAD_STEP72 -> route = 'ice_minimax'`
    - `signature == _JOHNBLAKE_STEP72 -> route = 'known_yarn'`
  - **[FACT]**: Against an unseen agent like V54++, the opponent asset signatures **never match** because V54++ does not execute historical opponent tapes.
  - **[FACT]**: When all signatures fail to match, V66 defaults to its fallback routing logic, which selects `_V58_RECOVERY_ROUTE` on Bakery seeds.
  - **[INFERENCE]**: V66's victories on specific Bakery seeds are not the result of closed-loop public-state reasoning. They are accidental artifacts of fallback route alignment on historical replay signatures.

---

## 4. Summary of Candidate Causal Variables for Stage 3

| Candidate Variable | Status | Stage 3 Arm |
| :--- | :--- | :---: |
| **Tile Bonuses** | **KILLED [FACT]** (Nonexistent in engine) | N/A |
| **Pure Route Priors (Backbone, Yarn, Bakery)** | **Viable [HYPOTHESIS]** | R1, R2, R3 |
| **V66 Route Selector** | **Viable [HYPOTHESIS]** | R4 |
| **Step-72 Shop Gating Only** | **Viable [HYPOTHESIS]** | R5 |
| **Step-144 Shop Gating Only** | **Viable [HYPOTHESIS]** | R6 |
| **Step-216 Shop Gating Only** | **Viable [HYPOTHESIS]** | R7 |
| **Step-72 + Step-144 Shop Gating (V54++)** | **Baseline Champion** | R0, R8 |
| **Step 72 + 144 + 216 + 288 Full Shop History** | **Viable [HYPOTHESIS]** | R9 |
| **Random Route Assignment Control** | **Null Control** | R10 |
