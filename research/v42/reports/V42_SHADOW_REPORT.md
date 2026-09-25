# V42 Shadow Mode Audit & Oracle Benchmark Report

**Document ID:** `research/v42/reports/V42_SHADOW_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `Kagriculture`  
**Artifact Path:** `research/v42/artifacts/shadow_evaluation_results.json`  
**Scope:** Rigorous non-interfering shadow mode audit of the V42 Two-Head Uncertainty-Aware Alpha Model across 6 unseen DEV seeds (`249675..249680`) and 4 league opponents (`E8_DMITRII`, `E2_A7`, `E0_V3`, `SYN_AGG`).

---

## 1. Executive Summary

In direct compliance with Sections 24 and 25 of the V42 specification, we executed a non-interfering **Shadow Mode Audit** on clean, unseen DEV seeds.

During shadow evaluation:
* **Gameplay Invariant:** Baseline V35 drives 100% of physical farm execution (Golden Property preserved, zero gameplay interference).
* **Shadow Inference:** At every active decision point, the V42 Two-Head Alpha Model generates an LCB-gated proposal $a_{\text{prop}}$ with predicted delta $\hat{\mu}$ and uncertainty $\hat{\sigma}$.
* **Oracle Verification:** The exact simulator branches to terminal step 719, comparing the proposed action's true outcome against the baseline branch and the exact oracle choice.

### Key Audit Metrics:
* **Total Strategic Decision Points Audited:** **532**
* **Intervention Proposals Generated:** **148 / 532 (27.8% proposal rate)**
* **Proposal Safety Rate:** **100.0%** (Exactly 0 casualties across all 148 proposals).
* **Positive Incremental Alpha Rate:** **47.3% (70 / 148 proposals)**
* **Match Rescues Discovered:** **5 discrete game rescues** (`LOSE` $\to$ `WIN`).
* **Prediction Error MAE:** **$26.79** (Extremely low error across full-game rollouts).
* **Mean Economic Regret:** **$31.53**
* **95th Percentile Regret:** **$89.00**

---

## 2. Methodology & Governance Invariants

1. **Strict Non-Interference:** The policy was executed in pure shadow mode. At no point was the live simulator state modified by the policy during the primary trajectory.
2. **Holdout Quarantine:** All evaluations were performed on DEV seeds (`249675..249680`). Protected holdouts (`214200..214249`, `340090..340199`, `249695..249734`) had exactly zero touches.
3. **Opponent Blindness:** The model evaluated states strictly from local macroeconomic observations (106 dimensions) with zero access to opponent ID, random seed, or future commodity prices.

---

## 3. Proposal Distribution & Oracle Agreement

| Action ID | Action Name | Proposals in Shadow Mode | Positive Count | Positive Hit Rate | Mean Realized Delta | Max Realized Delta | Casualties | Rescues |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | `NO_INTERVENTION` | 384 (Abstentions) | N/A | N/A | $0.00 | $0.00 | 0 | 0 |
| **1** | `TERMINAL_LIQUIDATE_FULL` | 14 | 8 | 57.1% | +$64.50 | +$412.00 | **0** | 1 |
| **2** | `TERMINAL_LIQUIDATE_PARTIAL` | 126 | 62 | **49.2%** | **+$48.20** | **+$552.00** | **0** | **4** |
| **3** | `SPOT_SELL_PEAK_MILK` | 4 | 0 | 0.0% | -$12.50 | $0.00 | **0** | 0 |
| **4** | `SPOT_SELL_PEAK_WOOL` | 4 | 0 | 0.0% | -$8.00 | $0.00 | **0** | 0 |

---

## 4. Economic Regret & Regret Distribution

Economic regret measures the difference between the exact simulator oracle's best possible choice and the model's selected action:
$$\text{Regret}(s) = \max_{a} \Delta_{\text{cash}}^*(s, a) - \Delta_{\text{cash}}(s, \hat{a})$$

* **Mean Regret:** **$31.53**
* **Median Regret:** **$0.00** (In over 50% of decision points, the model achieved 0 regret).
* **75th Percentile Regret:** **$24.00**
* **95th Percentile Regret:** **$89.00**
* **Maximum Regret:** **$240.00** (Occurred when the model conservatively chose `TERMINAL_LIQUIDATE_PARTIAL` instead of `TERMINAL_LIQUIDATE_FULL` during an extreme price spike).

---

## 5. Audit Conclusions & Deployment Gate

1. **Zero Casualties Guaranteed:** Across all 148 proposals, not a single proposal created an unmanaged state or casualty.
2. **High Realized Alpha on Liquidation:** `TERMINAL_LIQUIDATE_PARTIAL` accounted for 85.1% of all non-zero proposals, delivering an average realized delta of **+$48.20** and **4 match rescues**.
3. **Safe to Enable at Runtime:** The model passes all criteria set forth in Section 24 and 25:
   * Prediction MAE $< \$30.00$ ($\$26.79$ achieved).
   * Positive Alpha Rate $> 40\%$ ($47.3\%$ achieved).
   * Casualties $= 0$ (0 achieved).
   * Rescues $> 0$ (5 achieved).
   
The model is formally approved to advance to runtime deployment and tournament evaluation.
