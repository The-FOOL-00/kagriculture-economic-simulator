# Stage 1 — Reproduce and Localize Step-301 Divergence

**Date & Time**: 2026-09-10T09:12:00+05:30  
**Audit Phase**: STAGE 1 — Reproduction and Localization  
**Artifacts Generated**:
- Route Action Tape Comparison: [`research/step301_route_diff.csv`](file:///c:/Users/Sundareswaran/Kagriculture/research/step301_route_diff.csv)
- Turn Telemetry (Steps 240–360): [`research/step301_telemetry_deep.json`](file:///c:/Users/Sundareswaran/Kagriculture/research/step301_telemetry_deep.json)

---

## 1. Frozen Codebase Hashing & Immutability Check

| Baseline | Path | SHA256 Checksum | Status |
| :--- | :--- | :--- | :--- |
| **Canonical V54** | `external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py` | `ef9b77603d1110126a133f972ca2155aa124a30fa3639f2f166664e0ba3361fe` | FROZEN |
| **Canonical V66** | `external_repos/kaggriculture-v66-agent/main.py` | `a7059fd4cdde05bbab05c140c90ed9f386f44a050574514399bd97e030a150b3` | FROZEN |
| **V54+ Macro** | `candidates/v54_plus_macro.py` | `8947a81051e2c31f79c68b2d66222fbabe4b7c2d9c3e630dd6ee8bea7ec01907` | FROZEN |
| **V54++ Champion** | `candidates/v54_plus_shop.py` | `592f0ba31b3b20b5a3aad409a753b5e6bdeb29a9eb2381342b1cd527509fa9e8` | FROZEN |

- **[FACT]**: All SHA256 checksums match the frozen manifest in [`research/step301_frozen_manifest.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/step301_frozen_manifest.md). Zero files modified.

---

## 2. Ancestral Route Decompression (Steps 240–360)

Decompression and pairwise comparison of the 7 ancestral route action tapes across the 121-step window (Steps 240 through 360) yields:

| Route A | Route B | First Diff Step | Material Diff Steps (240–360) | Commodities Affected | Worker Affected | Market Affected | Livestock Affected |
| :--- | :--- | :---: | :---: | :--- | :---: | :---: | :---: |
| **Backbone** | **Yarn** | **240** | **121 (100%)** | CARROT;FERTILIZER;MELON;MILK;SHEEP;STRAWBERRY;WHEAT;WOOL | True | True | True |
| **Backbone** | **Bakery_Yarn** | **240** | **121 (100%)** | CARROT;FERTILIZER;MELON;MILK;SHEEP;STRAWBERRY;WHEAT;WOOL | True | True | True |
| **Backbone** | **Recovery** | **241** | **120** | CARROT;FERTILIZER;MELON;MILK;SHEEP;STRAWBERRY;WHEAT;WOOL | True | True | True |
| **Backbone** | **Ice_Minimax** | **240** | **93** | CARROT;FERTILIZER;MELON;MILK;SHEEP;STRAWBERRY;WHEAT;WOOL | True | True | True |
| **Backbone** | **Known_Yarn** | **240** | **121 (100%)** | CARROT;FERTILIZER;MELON;MILK;SHEEP;STRAWBERRY;WHEAT;WOOL | True | True | True |
| **Backbone** | **Clone** | **240** | **121 (100%)** | CARROT;FERTILIZER;MELON;MILK;SHEEP;STRAWBERRY;WHEAT;WOOL | True | True | True |
| **Yarn** | **Bakery_Yarn** | **-1 (None)** | **0 (0%)** | **NONE** | **False** | **False** | **False** |
| **Yarn** | **Clone** | **-1 (None)** | **0 (0%)** | **NONE** | **False** | **False** | **False** |
| **Bakery_Yarn** | **Clone** | **-1 (None)** | **0 (0%)** | **NONE** | **False** | **False** | **False** |
| **Yarn** | **Recovery** | **240** | **121 (100%)** | CARROT;FERTILIZER;MELON;MILK;SHEEP;STRAWBERRY;WHEAT;WOOL | True | True | True |
| **Yarn** | **Known_Yarn** | **250** | **70** | FERTILIZER;MELON;MILK;WHEAT;WOOL | True | True | True |

### Evidence Classifications:
- **[FACT]**: The ancestral routes `Backbone` and `Yarn` differ on **100% of steps** between 240 and 360.
- **[FACT]**: `Yarn`, `Bakery_Yarn`, and `Clone` are **bit-for-bit identical** between Steps 240 and 360 (zero differences).
- **[FACT]**: In `candidates/v54_plus_shop.py`, route selection occurs strictly at Step 72 and Step 144. No route selection code, residual branch, or dynamic threshold exists at Step 301.
- **[INFERENCE]**: Step 301 is **not an organic decision point**. It is an arbitrary tick in the middle of a continuous 121-step macro divergence established upstream at Day 3 (Step 72) and Day 6 (Step 144).
- **[INFERENCE]**: The characterization of Step 301 as the "first consequential divergence" was an artifact of earlier forensic scripts that initialized logging loops at `step >= 300`.

---

## 3. Turn-Level Telemetry Across Population A & Population B

From the 1,000-match holdout dataset, 15 matches from **Population A** ($V66 \ge V54++ + \$5\text{k}$) and 15 matches from **Population B** ($V54++ \ge V66 + \$5\text{k}$) were traced turn-by-turn from Step 240 to 360:

### Case 1: Seed 1542 (Population A — Large V66 Win: $-\$5,559$)
- **Step 300 State**:
  - V54++ Cash: $\$18,194$, V66 Cash: $\$18,403$ (difference $<\$210$).
  - V54++ Shed Wheat: 47 units, V66 Shed Wheat: 49 units.
  - Animals: 0 cows, 0 sheep for both agents.
  - Prices: Wheat $\$41$, Wool $\$235$, Milk $\$122$.
- **Step 301 Action**:
  - V54++: `farmer: ['COLLECT_FERTILIZER']`, `market: [['SELL', 'WHEAT', 29]]`
  - V66: `farmer: ['COLLECT_FERTILIZER']`, `market: []`
- **[FACT]**: V54++ emitted a wheat sale order of 29 units at Step 301 because it was executing `_V56_YARN_ROUTE`. V66 was executing a different replay branch (`_V58_RECOVERY_ROUTE`) that had scheduled sales at different ticks.

### Case 2: Seed 1773 (Population A — Large V66 Win: $-\$15,502$)
- **Step 300 State**:
  - V54++ Cash: $\$15,415$, V66 Cash: $\$14,814$ (V54++ leading by $+\$601$).
  - V54++ Shed Wheat: 35 units, V66 Shed Wheat: 36 units.
- **Step 301 Action**:
  - Both agents executed their respective planned route ticks. Zero market transactions occurred at Step 301 for either agent.

### Case 3: Seed 1803 (Population B — Large V54++ Win: $+\$14,244$)
- **Step 300 State**:
  - V54++ Cash: $\$16,820$, V66 Cash: $\$15,100$.
- **[FACT]**: Both agents maintained positive cash and identical farm layouts. V54++'s terminal liquidation overlay secured the margin in the final hours (Steps 713–718).

---

## 4. Stage 1 Localization Verdict

1. **Hypothesis A (Step 301 is genuinely the cause)**: **REFUTED [FACT]**.
   - Neither agent makes a dynamic decision at Step 301. Both agents execute deterministic route priors that were chosen over 150 steps prior.
2. **Hypothesis B (Step 301 is merely the first visible symptom)**: **CONFIRMED [INFERENCE]**.
   - It is the first step where scheduled market orders in the Yarn tape become visible to telemetry loggers starting at Step 300.
3. **Hypothesis C (Downstream of earlier route divergence)**: **CONFIRMED [FACT]**.
   - The route divergence occurred at Step 72 and Step 144 when `obs['town']['unlocked_shops']` triggered route commitments.
