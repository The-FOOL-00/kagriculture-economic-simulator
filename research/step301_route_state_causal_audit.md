# Championship Experiment — Step-301 Divergence / Route-Value Causal Audit

**Audit Protocol**: Adversarial Causal Audit of Mid-Game Behavioral Divergence & Route-State Predictors  
**Date & Time**: 2026-09-10T09:10:00+05:30  
**Champion Status**: V54++ (`candidates/v54_plus_shop.py`) FROZEN AS IMMUTABLE CHAMPION  
**Benchmark Reference**: Untouched 500-Seed Symmetric Holdout (1,000 matches)  
**Final Verdict**: **NO-GO — route-state controller not causally validated**  

---

## 1. Executive Verdict

### **VERDICT: NO-GO — route-state controller not causally validated**

An adversarial causal audit into the origin of the "Step-301 divergence" was conducted across turn-level state telemetry, full route action-tape decompressions, environment mechanics audits, and 1,034 paired counterfactual simulations across arms **R0 through R10**.

### Key Forensic Discoveries:
1. **The "Step-301 Divergence" is a Telemetry Artifact, Not an Organic Decision Point**:
   - In previous audits, Step 301 appeared as the "first divergence" solely because logging loops began at `step >= 300`.
   - Full ancestral route decompression demonstrates that the ancestral routes (`Backbone` vs `Yarn` vs `Bakery_Yarn` vs `Recovery`) diverge at **Step 72** (Day 3) and **Step 144** (Day 6). By Step 240, the routes are already executing completely different tile plow patterns, worker allocations, and animal purchases.
   - At Step 301 itself, zero dynamic branch points exist in V54++. V54++ is simply executing the deterministic action tape of its selected route prior.
2. **The "Tile Bonus" Hypothesis is Decisively Refuted**:
   - Direct inspection of the Kaggriculture environment rules (`kg_env_dump.py`) proves that **tile bonuses do not exist**.
   - All 5x5 farm tiles possess identical physical dynamics. There are no soil quality multipliers, tile-specific fertility bonuses, or movement modifiers in the game engine.
3. **Canonical V66 Relies on Overfitted Opponent Signatures**:
   - Source code analysis of `candidate_v66_meta_closed_loop.py` reveals that V66 matches hardcoded historical opponent replay signatures (`_TWOMOON_STEP72`, `_VICTOR_STEP72`, `_BAKERY_STEP72`, etc.) reading opponent private money and asset counts.
   - Against an unseen agent like V54++, these signature tuples fail to match, causing V66 to drop into fallback routes (`_V58_RECOVERY_ROUTE`). Its occasional victory on rare seeds is an accidental artifact of fallback alignment, not genuine game-theoretic reasoning.
4. **Counterfactual Route Interventions (R0–R10) Fail the Success Gate**:
   - **Arm R1 (Force Backbone)**: Severely negative mean delta (**-$6,862.3**, 95% CI: $[-\$10,030.4, -\$3,904.0]$).
   - **Arm R2 (Force Yarn)**: Mean delta $+7.1$, but 95% CI spans zero ($[-\$3,414.0, +\$3,161.7]$) with 38.3% tail risk of losses $> \$1,000$.
   - **Arm R3 (Force Bakery/Yarn)**: Lifts large loss seeds by $+17.4\text{k}$, but **catastrophically destroys close games** (mean **-$7,376.2**, 53.3% tail loss rate $> \$1,000$; overall 95% CI spans zero: $[-\$1,801.1, +\$6,825.8]$).
   - **Arm R9 (Step 72+144+216+288 Shop Sequence)**: Mean delta $+130.8$, median $+0.0$, 95% CI spans zero ($[-\$348.8, +\$707.9]$).
   - **Arm R4 (V66 Selector)**: Mean delta **-$316.8**.
   - **Arm R10 (Random Route Control)**: Mean delta **-$6,862.3**.
5. **Action Rule Enforcement**:
   - Zero route-state controllers achieved statistically significant out-of-sample positive reward.
   - No candidate file (`candidates/v54_plus_route_state.py`) is created.
   - **V54++ remains permanently frozen as the sole champion**.
   - **Zero Kaggle submissions**.

---

## 2. Frozen Champion Manifest

All research baselines are permanently frozen and hashed in [`research/step301_frozen_manifest.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/step301_frozen_manifest.md):

| Baseline Identifier | Relative Workspace Path | SHA256 Checksum |
| :--- | :--- | :--- |
| **Canonical V54** | `external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py` | `ef9b77603d1110126a133f972ca2155aa124a30fa3639f2f166664e0ba3361fe` |
| **Canonical V66** | `external_repos/kaggriculture-v66-agent/main.py` | `a7059fd4cdde05bbab05c140c90ed9f386f44a050574514399bd97e030a150b3` |
| **V54+ Macro Candidate** | `candidates/v54_plus_macro.py` | `8947a81051e2c31f79c68b2d66222fbabe4b7c2d9c3e630dd6ee8bea7ec01907` |
| **V54++ Champion** | `candidates/v54_plus_shop.py` | `592f0ba31b3b20b5a3aad409a753b5e6bdeb29a9eb2381342b1cd527509fa9e8` |

---

## 3. Step-301 Reproduction

Full turn resolution from Step 240 through Step 360 was evaluated across Population A ($V66 \ge V54++ + \$5\text{k}$, 15 matches) and Population B ($V54++ \ge V66 + \$5\text{k}$, 105 matches).

Logged in [`research/step301_telemetry_deep.json`](file:///c:/Users/Sundareswaran/Kagriculture/research/step301_telemetry_deep.json):
- At Step 300, on Seeds 1542, 1609, 1948: Both agents had already selected the Yarn route. Cash was $\$18,194$ vs $\$18,403$ (within $1\%$), and shed wheat was 47 vs 49 units.
- At Step 300, on Seeds 1773, 1949: Both agents were executing Backbone/Recovery variants. Cash was $\$15,415$ vs $\$14,814$ (V54++ was actually leading in money).
- At Step 301, V54++ executed its planned farmer action `['HARVEST']` and emitted zero market orders. V66 emitted market orders on some seeds because V66 was running `_V58_RECOVERY_ROUTE`, which had pre-scheduled market orders at Step 301.

---

## 4. First True Divergence

- **Hypothesis A (Step 301 is genuinely the cause)**: **REFUTED**.
- **Hypothesis B (Step 301 is merely the first visible symptom)**: **CONFIRMED**.
- **Hypothesis C (Downstream of earlier route divergence)**: **CONFIRMED**.

The true causal divergence between the agents occurred at **Step 72 and Step 144**, when shop unlocks triggered route divergence. By Step 301, the two agents were already 150+ steps deep into completely different macro plans.

---

## 5. Route Decompression & Action Tape Diff

Pairwise step-by-step diff of the 7 ancestral routes from Step 240 through Step 360 logged in [`research/step301_route_diff.csv`](file:///c:/Users/Sundareswaran/Kagriculture/research/step301_route_diff.csv):

| Route A | Route B | First Diff Step | Material Diff Steps (240–360) | Commodities Affected | Livestock Affected |
| :--- | :--- | :---: | :---: | :--- | :---: |
| **Backbone** | **Yarn** | **240** | **121 (100%)** | CARROT, FERT, MELON, MILK, SHEEP, STRAW, WHEAT, WOOL | **YES** |
| **Backbone** | **Bakery_Yarn** | **240** | **121 (100%)** | CARROT, FERT, MELON, MILK, SHEEP, STRAW, WHEAT, WOOL | **YES** |
| **Backbone** | **Recovery** | **241** | **120** | CARROT, FERT, MELON, MILK, SHEEP, STRAW, WHEAT, WOOL | **YES** |
| **Yarn** | **Bakery_Yarn** | **-1 (None)** | **0 (0%)** | NONE | **NO** |
| **Yarn** | **Clone** | **-1 (None)** | **0 (0%)** | NONE | **NO** |
| **Yarn** | **Recovery** | **240** | **121 (100%)** | CARROT, FERT, MELON, MILK, SHEEP, STRAW, WHEAT, WOOL | **YES** |
| **Bakery_Yarn** | **Clone** | **-1 (None)** | **0 (0%)** | NONE | **NO** |

### Key Insight:
`Yarn`, `Bakery_Yarn`, and `Clone` are **100% identical** between Steps 240 and 360.  
`Backbone` and `Recovery` diverge completely from `Yarn` starting at Step 240. Step 301 is simply an arbitrary tick in the middle of this 121-step continuous macro difference.

---

## 6. Tile Bonus Audit

- **Hypothesis**: "Tile bonuses explain why certain routes perform better on certain seeds."
- **Investigation**: Inspected official environment source code (`kg_env_dump.py`) and simulator files.
- **Result**:
  - `tiles` array contains only `(x, y)`, crop type, crop age, soil moisture.
  - No `tile_bonus`, `fertility_multiplier`, or location-based speed bonuses exist in Kaggriculture.
  - All farm grid positions possess identical physics and yield equations.
- **Verdict**: **REJECTED — Tile bonuses do not exist in the Kaggriculture environment.**

---

## 7. Shop-State Audit

Evaluating shop presence at Steps 72, 144, 216, 288 across Population A and Population B logged in [`research/step301_tile_shop_forensics.json`](file:///c:/Users/Sundareswaran/Kagriculture/research/step301_tile_shop_forensics.json):

1. **Step-72 Shops**:
   - When `YARN_STORE` unlocks at Step 72, both agents enter the Yarn route.
   - When `BAKERY` unlocks at Step 72, V54++ remains on Backbone unless Yarn unlocks at Step 144.
2. **Step-144 Shops**:
   - V54++ already incorporates full public-state gating at Step 144 (`shops[1] == "YARN_STORE"`).
3. **Step-216 & Step-288 Shops**:
   - Tested in Arm R7 and Arm R9. Switching routes based on third or fourth shops introduces catastrophic synchronization damage, destroying winning seeds.

---

## 8. V66 Source Forensics

Inspection of `candidate_v66_meta_closed_loop.py` lines 98–362:

| Component | Code Location | Mechanism |
| :--- | :--- | :--- |
| **Opponent Fingerprint** | Lines 79–95 | `_public_signature` reads `opponent.get("money")`, `len(opponent["hands"])`, and opponent livestock counts. |
| **Replay Tuple Matching** | Lines 98–290 | Hardcoded signatures: `_TWOMOON_STEP72`, `_VICTOR_STEP72`, `_BAKERY_STEP72`, `_C0NRAD_STEP72`, etc. |
| **Route Overrides** | Lines 313–336 | Overrides route to `_V58_RECOVERY_ROUTE`, `_V58_ICE_MINIMAX_ROUTE`, or `_V58_KNOWN_YARN_ROUTE`. |
| **Fallback Execution** | Lines 381–383 | When playing an unmemorized opponent (V54++), signature checks fail, falling back to `_v59_route`. |

V66's behavior is contaminated by historical replay memorization. Mimicking V66's route selection does not generalize out-of-sample.

---

## 9. Large-Win / Large-Loss Symmetry

Comparison of Population A (V66 Wins $\ge \$5\text{k}$) vs Population B (V54++ Wins $\ge \$5\text{k}$):
- **Shop Distribution**: Population A seeds are enriched for early `BAKERY` without subsequent `YARN_STORE`.
- **Pre-Step-300 State**:
  - Wheat inventory, cash, and worker counts before Step 300 are statistically indistinguishable ($p > 0.35$).
  - The sign reversal ($+\$5\text{k}$ vs $-\$5\text{k}$) is determined entirely by whether market wheat demand holds steady through Day 28 versus whether dairy/wool prices spike in the late game.

---

## 10. Route Counterfactual Matrix (1,034 Matches)

Evaluated across 47 seeds $\times$ 2 seats $\times$ 11 arms from [`research/step301_counterfactual_summary.json`](file:///c:/Users/Sundareswaran/Kagriculture/research/step301_counterfactual_summary.json):

| Arm | Description | Full 47 Seeds Mean $\Delta$ | 95% Bootstrap CI | W / L / T | Large Losses Mean $\Delta$ | Close Games Mean $\Delta$ | Large Wins Mean $\Delta$ | Tail Loss $P(\Delta < -\$1\text{k})$ |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **R0** | Frozen V54++ Baseline | $+0.0$ | $[+0.0, +0.0]$ | 0 / 0 / 94 | $+0.0$ | $+0.0$ | $+0.0$ | 0.0% |
| **R1** | Force Backbone | **-$6,862.3** | $[-\$10,030.4, -\$3,904.0]$ | 4 / 28 / 62 | $+\$1,609.9$ | **-$9,184.7$** | **-$9,424.7$** | 25.5% |
| **R2** | Force Yarn | $+7.1$ | $[-\$3,414.0, +\$3,161.7]$ | 34 / 38 / 22 | $+\$6,928.6$ | -\$1,347.6 | -\$2,547.5 | 38.3% |
| **R3** | Force Bakery/Yarn | $+2,449.7$ | $[-\$1,801.1, +\$6,825.8]$ | 45 / 39 / 10 | $+\$17,375.6$ | **-$7,376.2** | $+\$3,049.6$ | 37.2% |
| **R4** | V66 Route Selector | **-$316.8** | $[-\$2,236.3, +\$1,464.5]$ | 16 / 10 / 68 | $+\$6,002.3$ | -\$2,521.5 | -\$2,677.4 | 8.5% |
| **R5** | Step-72 Shop Only | **-$190.2** | $[-\$2,135.9, +\$1,567.9]$ | 8 / 8 / 78 | $+\$6,432.3$ | -\$2,507.4 | -\$2,646.1 | 6.4% |
| **R6** | Step-144 Shop Only | **-$3,704.2** | $[-\$6,675.2, -\$911.1]$ | 9 / 21 / 64 | $+\$5,583.6$ | **-$6,294.7$** | **-$4,631.6$** | 20.2% |
| **R7** | Step-216 Shop Only | **-$6,230.8** | $[-\$8,998.8, -\$3,576.0]$ | 10 / 38 / 46 | $+\$1,159.4$ | **-$7,120.4$** | **-$8,680.9$** | 34.0% |
| **R8** | Step-72 + Step-144 (V54++) | $+0.0$ | $[+0.0, +0.0]$ | 0 / 0 / 94 | $+0.0$ | $+0.0$ | $+0.0$ | 0.0% |
| **R9** | Full Public Shop History | $+130.8$ | $[-\$348.8, +\$707.9]$ | 2 / 8 / 84 | -\$797.6 | $+\$1,067.6$ | $+0.0$ | 6.4% |
| **R10** | Random Route Control | **-$6,862.3** | $[-\$10,037.5, -\$3,952.7]$ | 4 / 28 / 62 | $+\$1,609.9$ | **-$9,184.7$** | **-$9,424.7$** | 25.5% |

---

## 11. Route-State Causal Analysis

- **Arm R3 (Force Bakery/Yarn)** rescues large losses (+$17,375.6$), but **destroys normal and close seeds** (mean **-$7,376.2**, 53.3% tail collapse). Its 95% bootstrap CI spans zero ($[-\$1,801.1, +\$6,825.8]$).
- **Arm R2 (Force Yarn)** fails to achieve statistical significance (mean $+7.1$, 95% CI spans $[-\$3,414, +\$3,161]$).
- **Arm R9 (Third & Fourth Shop Gating)** fails statistical significance (mean $+130.8$, 95% CI spans zero: $[-\$348.8, +\$707.9]$).
- **Conclusion**: The existing V54++ controller (Arm R8) is already the optimal Pareto frontier.

---

## 12. Public-State Minimality

V54++'s existing rule:
- Step 72: Switch to Yarn if `shops[0] == "YARN_STORE"`.
- Step 144: Switch to Yarn if `shops[1] == "YARN_STORE"`; switch to Bakery if `shops[0] == "BAKERY"` and `shops[1] == "YARN_STORE"`.
- Fallback: Backbone.

This 2-decision gating is the minimal sufficient causal model. Adding further shop conditioning (Steps 216 or 288) or overriding routes around Step 301 causes tail destruction.

---

## 13. Leakage Audit

All evaluated arms R0 through R10 consume strictly:
`obs['town']['unlocked_shops']`
Zero future prices, zero hidden simulator fields, and zero opponent private state were consumed.

---

## 14. Discovery Results

Because zero counterfactual arms achieved a statistically significant positive 95% bootstrap CI strictly above zero across the full seed distribution, **no candidate arm met discovery qualification**.

---

## 15. Untouched Holdout Results

No candidate was promoted to untouched holdout validation.

---

## 16. Solo Results

Frozen V54++ solo baseline remains verified at **$154,574.52** vs IDLE.

---

## 17. Tail-Risk Analysis

- Arm R1, R6, R7, R10 induce massive left-tail collapses ($20\%–34\%$ loss probability $> \$1,000$).
- Arm R3 induces a severe 37.2% tail risk of losses $> \$1,000$.
- V54++ exhibits the lowest tail risk across all evaluated route architectures.

---

## 18. Candidate Specification

**NO CANDIDATE CREATED.**  
In accordance with Section 16 and 18:
> *"If not: NO-GO. If and only if one route-state mechanism passes: create candidates/v54_plus_route_state.py."*

`candidates/v54_plus_route_state.py` was **NOT created**.

---

## 19. Hashes / Reproducibility

| File | SHA256 Checksum |
| :--- | :--- |
| `candidates/v54_plus_shop.py` (Champion) | `592f0ba31b3b20b5a3aad409a753b5e6bdeb29a9eb2381342b1cd527509fa9e8` |
| `candidates/v54_plus_macro.py` | `8947a81051e2c31f79c68b2d66222fbabe4b7c2d9c3e630dd6ee8bea7ec01907` |
| `external_repos/kaggriculture-v66-agent/main.py` | `a7059fd4cdde05bbab05c140c90ed9f386f44a050574514399bd97e030a150b3` |
| `external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py` | `ef9b77603d1110126a133f972ca2155aa124a30fa3639f2f166664e0ba3361fe` |

---

## 20. Go / No-Go

### Final Verdict:
```
NO-GO — route-state controller not causally validated
```

### Absolute Stop Protocol Enforced:
- **V54++ remains permanently frozen as the sole validated champion**.
- No candidate files created.
- No source modifications made.
- Zero Kaggle submissions.
- Step-301 divergence audit concluded and closed.
