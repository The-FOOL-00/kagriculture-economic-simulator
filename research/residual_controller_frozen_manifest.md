# V54++ Residual Controller Causal Audit — Frozen Manifest

**Audit Protocol**: Championship Experiment — V54++ Residual Controller Causal Audit  
**Status**: IMMUTABLE RESEARCH BASELINES FROZEN  
**Target Candidate**: `candidates/v54_plus_shop.py` (V54++)  
**Rule**: Zero modifications to frozen baselines. Zero Kaggle submission.

---

## 1. Frozen Codebase Checksums

| Baseline Identifier | Relative Workspace Path | SHA256 Checksum |
| :--- | :--- | :--- |
| **Canonical V54** | `external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py` | `ef9b77603d1110126a133f972ca2155aa124a30fa3639f2f166664e0ba3361fe` |
| **Canonical V66** | `external_repos/kaggriculture-v66-agent/main.py` | `a7059fd4cdde05bbab05c140c90ed9f386f44a050574514399bd97e030a150b3` |
| **V54+ Macro Candidate** | `candidates/v54_plus_macro.py` | `8947a81051e2c31f79c68b2d66222fbabe4b7c2d9c3e630dd6ee8bea7ec01907` |
| **V54++ Champion** | `candidates/v54_plus_shop.py` | `592f0ba31b3b20b5a3aad409a753b5e6bdeb29a9eb2381342b1cd527509fa9e8` |

---

## 2. Champion Architectural Contract (V54++)
* **Protected Macro Route Core**:
  - Backbone: `_V56_BACKBONE_ROUTE` (`candidate_v62_composite_bakery_yarn.py`)
  - Yarn Route: `_V56_YARN_ROUTE`
  - Bakery Route: `_V58_BAKERY_YARN_ROUTE`
  - Policy Builder: `mod_v54._v51_build_policy(route, _CONFIG)`
* **Active Tactical Overlays**:
  1. `_v60_move_wheat_early`: Step 0 wheat front-run
  2. `_V54_CONFIG`: Active Deficit Liquidity Fronting (`front_money_deficit=4500.0`, `preempt_money_deficit=4000.0`, `front_on_near=True`, `preempt_enabled=True`)
  3. `_v60_seed_trim`: Strawberry seed trim
  4. `_v60_shed_guard`: Hour-23 shed capacity guard
  5. `_route_loaded_units`: Terminal loaded unit recall [713–716]
  6. `_TERMINAL_UNITS`: Terminal home convergence [717–718]
  7. `_TERMINAL_MARKET`: Final market liquidation [718]
* **Minimal Public Shop Controller**:
  - Step 72: Switch to Yarn if `shops[0] == "YARN_STORE"`
  - Step 144: Switch to Yarn if `shops[1] == "YARN_STORE"`; switch to Bakery if `shops[0] == "BAKERY"` and `shops[1] == "YARN_STORE"`
  - Post-Step 144: Permanently committed. Zero dynamic route switching.

---

## 3. Decisively Closed Research Branches
The following branches are completely closed and excluded from investigation:
- Step-301 route switching
- Step-216 adaptation
- Runtime route changes after Step 144
- Wheat-price threshold controllers
- Wheat/livestock conversion policies
- Tile-bonus hypotheses
- Public shop routing after Step 144

---

## 4. Audit Objective
Determine if the **tactical / residual controller** can improve V54++ while keeping the macro route byte-for-byte identical.
