# Champion Frozen Manifest

**Date & Time**: 2026-09-09T23:05:00+05:30  
**Status**: IMMUTABLE RESEARCH BASELINES FROZEN  
**Audit Protocol**: Early-Phase Economic Gap Audit (Steps 0–143)

---

## 1. Frozen Codebase Checksums

Every baseline file below is permanently frozen. No modifications, reformatting, or tuning are permitted.

| Baseline Identifier | Relative Workspace Path | SHA256 Checksum |
| :--- | :--- | :--- |
| **Canonical V54** | `external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py` | `ef9b77603d1110126a133f972ca2155aa124a30fa3639f2f166664e0ba3361fe` |
| **Canonical V66** | `external_repos/kaggriculture-v66-agent/main.py` | `a7059fd4cdde05bbab05c140c90ed9f386f44a050574514399bd97e030a150b3` |
| **V54+ Macro Candidate** | `candidates/v54_plus_macro.py` | `8947a81051e2c31f79c68b2d66222fbabe4b7c2d9c3e630dd6ee8bea7ec01907` |
| **V54++ Champion** | `candidates/v54_plus_shop.py` | `592f0ba31b3b20b5a3aad409a753b5e6bdeb29a9eb2381342b1cd527509fa9e8` |

---

## 2. Champion Specification (V54++)
* **Base Architecture**: V56 Backbone Route prior with V54 hybrid compiler (`_v51_build_policy`).
* **Tactical Overlays**:
  1. Hour-23 shed guard (`_v60_shed_guard`)
  2. Strawberry seed trim (`_v60_seed_trim`)
  3. Terminal loaded unit recall [713–716] (`_route_loaded_units`)
  4. Terminal home convergence [717–718] (`_TERMINAL_UNITS`)
  5. Final market liquidation [718] (`_TERMINAL_MARKET`)
* **Shop Adaptation**: Minimal sufficient public-state gating reading strictly `obs['town']['unlocked_shops']`:
  - Step 72: Switch to Yarn route if `shops[0] == "YARN_STORE"`.
  - Step 144: Switch to Yarn route if `shops[1] == "YARN_STORE"`; switch to Bakery route if `shops[0] == "BAKERY"` and `shops[1] == "YARN_STORE"`.
  - Post-Step 144: Permanently committed. Zero Step-216 route switching.
* **Opponent Data**: ZERO opponent state, zero fingerprinting, zero replay memorization.

---

## 3. Verified Benchmark Record
* **Untouched 500-Seed Holdout (1,000 Matches)**:
  - V54++ Mean: $\$88,306.17$
  - V66 Mean: $\$87,020.54$
  - Paired Margin: **$+\$1,285.64$**
  - 95% Bootstrap CI: **$[+\$689.23, +\$1,916.71]$** ($p = 4.88 \times 10^{-5}$)
* **Solo vs IDLE (25 Seeds)**:
  - V54++: $\$153,569.68$ vs Canonical V66: $\$152,500.28$ (V54++ leads by $+\$1,069.40$)
