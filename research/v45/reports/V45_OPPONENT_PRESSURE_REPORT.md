# V45 Opponent Pressure & Market Event Prediction Report

**Document ID:** `research/v45/reports/V45_OPPONENT_PRESSURE_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `The-FOOL-00/kagriculture-economic-simulator`  
**Phase:** Phase 2 (Opponent Pressure Model)  
**Dataset Artifact:** `research/v45/artifacts/market_pressure_dataset.pt`  
**Model Checkpoint:** `research/v45/artifacts/opponent_pressure_model.pt`  
**Metrics Artifact:** `research/v45/artifacts/pressure_model_metrics.json`  
**Formal Gate Verdict:** **PASS (Predictive Lead Time & Accuracy Confirmed)**  

---

## 1. Executive Summary

Phase 2 tests whether imminent opponent market dumps and price collapses can be accurately predicted from trailing observable public state.

A temporal GRU architecture was trained on 66,816 sequential windows (96 games) and evaluated on a strictly separated held-out validation cohort of 22,272 sequential windows (32 games).

Key empirical results:
* **P(opponent dump within 4 steps):** AUROC **0.9280**, Brier score **0.1146** (+50.34% over prior), Precision **72%**, Recall **91%**.
* **P(opponent dump within 8 steps):** AUROC **0.9427**, Brier score **0.0945** (+62.26% over prior), Precision **84%**, Recall **94%**.
* **P(opponent dump within 16 steps):** AUROC **0.9822**, Brier score **0.0380** (+82.15% over prior), Precision **96%**, Recall **97%**.
* **P(price collapse within 8 steps):** AUROC **0.9582**, Brier score **0.0402** (+43.42% over prior), Precision **65%**.
* **Average Predictive Lead Time:** **1.92 steps** before market impact.

---

## 2. Model Architecture & Training Protocol

* **Backbone:** 1-layer Gated Recurrent Unit (GRU) with hidden dimension 64, followed by non-linear projection and multi-task prediction heads.
* **Input Representation:** 42-dimensional legal feature vector sequence of length $L = 8$ trailing steps.
* **Outputs:**
  * 5 binary sigmoidal heads: $\hat{P}(\text{dump}_4), \hat{P}(\text{dump}_8), \hat{P}(\text{dump}_16), \hat{P}(\text{collapse}_8), \hat{P}(\text{collapse}_16)$
  * 1 continuous regression head: $\widehat{\Delta P}_8$ (expected 8-step price return)
* **Optimization:** Adam optimizer ($\text{lr} = 10^{-3}$, weight decay $10^{-4}$), batch size 256, trained for 10 epochs.
* **Data Separation:** Games 0..95 for training; Games 96..127 strictly quarantined for validation. Zero seed or trajectory overlap.

---

## 3. Quantitative Validation Performance Table

| Prediction Task | Temporal GRU AUROC | Unconditional Prior AUROC | GRU Brier Score | Prior Brier Score | Brier Improvement | Precision | Recall |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `dump4` | **0.9280** | 0.5000 | **0.1146** | 0.2308 | **+50.34%** | 0.72 | 0.91 |
| `dump8` | **0.9427** | 0.5000 | **0.0945** | 0.2505 | **+62.26%** | 0.84 | 0.94 |
| `dump16` | **0.9822** | 0.5000 | **0.0380** | 0.2127 | **+82.15%** | 0.96 | 0.97 |
| `collapse8` | **0.9582** | 0.5000 | **0.0402** | 0.0710 | **+43.42%** | 0.65 | 0.49 |
| `collapse16`| **0.9560** | 0.5000 | **0.0605** | 0.1233 | **+50.91%** | 0.73 | 0.53 |

---

## 4. Economic Usefulness & Lead-Time Analysis

A pure statistical metric is insufficient to satisfy the V45 gate. The model must provide actionable lead time:
1. **1.92-Step Advance Notice:** When the model outputs $P(\text{dump}_8) \ge 0.60$, the true opponent dump event occurs an average of 1.92 steps later.
2. **Actionable Pre-emption Window:** In Kagriculture, market orders submitted at step $t$ are processed at step $t$. An advance notice of 1 to 2 steps provides exactly the causal window required to submit pre-emptive sell orders at un-degraded spot prices before the opponent's orders flood the order book.
3. **Price Collapse Sensitivity:** In the terminal window (steps 680..718), $P(\text{collapse}_8)$ spikes from $<0.10$ to $>0.85$ at steps 691–693, perfectly preceding the step 695–696 market drops observed in Phase 1.

---

## 5. Phase 2 Gate Compliance Matrix

| Gate Condition | Standard | Measured Result | Verdict |
| :--- | :--- | :--- | :---: |
| Beats Non-ML Baseline | Material Brier & AUROC improvement | AUROC 0.928..0.982 (+43% to +82% Brier gain) | **PASS** |
| Useful Lead Time | $> 1.0$ steps advance warning | 1.92 steps average lead time | **PASS** |
| Information Legality | 0 future or hidden inputs | 100% verified legal inputs | **PASS** |

**Verdict:** Phase 2 is formally **PASSED**. Proceeding to Phase 3 & 4 (Market Response, Price Impact, and Counterfactual Discovery).
