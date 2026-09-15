# Step-301 Divergence Audit — Frozen Champion Manifest

**Date & Time**: 2026-09-10T08:15:00+05:30  
**Audit Protocol**: Step-301 Divergence / Route-Value Causal Audit  
**Status**: IMMUTABLE RESEARCH BASELINES FROZEN  

---

## 1. Frozen Codebase Checksums

All baseline files listed below are permanently frozen. No modifications, reformatting, or tuning are permitted.

| Baseline Identifier | Relative Workspace Path | SHA256 Checksum |
| :--- | :--- | :--- |
| **Canonical V54** | `external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py` | `ef9b77603d1110126a133f972ca2155aa124a30fa3639f2f166664e0ba3361fe` |
| **Canonical V66** | `external_repos/kaggriculture-v66-agent/main.py` | `a7059fd4cdde05bbab05c140c90ed9f386f44a050574514399bd97e030a150b3` |
| **V54+ Macro Candidate** | `candidates/v54_plus_macro.py` | `8947a81051e2c31f79c68b2d66222fbabe4b7c2d9c3e630dd6ee8bea7ec01907` |
| **V54++ Champion** | `candidates/v54_plus_shop.py` | `592f0ba31b3b20b5a3aad409a753b5e6bdeb29a9eb2381342b1cd527509fa9e8` |

---

## 2. Champion Specification (V54++)
* **Base Macro Architecture**: V56 Backbone Route prior with V54 hybrid compiler (`_v51_build_policy`).
* **Tactical Overlays**:
  1. Early Step 0 Wheat Front-Run (`_v60_move_wheat_early`)
  2. Active Deficit Liquidity Fronting (`front_money_deficit=4500.0`, `preempt_money_deficit=4000.0`)
  3. Strawberry seed trim (`_v60_seed_trim`)
  4. Hour-23 shed guard (`_v60_shed_guard`)
  5. Terminal loaded unit recall [713–716] (`_route_loaded_units`)
  6. Terminal home convergence [717–718] (`_TERMINAL_UNITS`)
  7. Final market liquidation [718] (`_TERMINAL_MARKET`)
* **Shop Adaptation**: Minimal sufficient public-state gating reading strictly `obs['town']['unlocked_shops']`:
  - Step 72: Switch to Yarn route if `shops[0] == "YARN_STORE"`.
  - Step 144: Switch to Yarn route if `shops[1] == "YARN_STORE"`; switch to Bakery route if `shops[0] == "BAKERY"` and `shops[1] == "YARN_STORE"`.
  - Post-Step 144: Permanently committed. Zero Step-216 route switching.
* **Opponent Data**: ZERO opponent state, zero fingerprinting, zero replay memorization.
