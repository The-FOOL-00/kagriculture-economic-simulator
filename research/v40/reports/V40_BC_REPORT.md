# V40 Behavioral Cloning Initialization Report

**Document ID:** `research/v40/reports/V40_BC_REPORT.md`  
**Date:** 2026-09-25 14:46:32  
**Model Architecture:** `V40RecurrentActorCritic` (obs=112, hidden=128, GRU core, actions=16)  
**Best Validation Accuracy:** **97.7%**  
**Training Duration:** 48.3s across 25 epochs  
**Checkpoint Path:** `C:\Users\Sundareswaran\Kagriculture\research\v40\checkpoints\v40_bc_model.pt`  

---

## 1. Executive Summary

Phase 10 initialized the V40 strategic recurrent policy via supervised Behavioral Cloning on expert demonstrations. The objective was to ground the model in the baseline's core chore stability and initial macroeconomic timing while establishing initial critic convergence for terminal value and win probability predictions.

### Final Metrics

- **Training Accuracy:** 99.0%
- **Validation Accuracy (Held-out seeds):** **97.7%**
- **Action Entropy:** 0.050
- **Critic Convergence:** Stable convergence across value, margin, and win probability loss components.

---

## 2. Epoch Progression

| Epoch | Train Loss | Train Acc (%) | Val Loss | Val Acc (%) | Action Entropy | LR |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | 4.7218 | 79.9% | 0.3231 | 85.1% | 0.401 | 1.0e-03 |
| 2 | 2.5242 | 90.0% | 0.2380 | 91.3% | 0.266 | 9.8e-04 |
| 3 | 2.1694 | 92.6% | 0.2037 | 93.1% | 0.241 | 9.7e-04 |
| 4 | 1.5595 | 92.9% | 0.1825 | 93.6% | 0.223 | 9.4e-04 |
| 5 | 1.1494 | 93.0% | 0.1786 | 93.7% | 0.220 | 9.1e-04 |
| 6 | 0.5752 | 94.0% | 0.1603 | 94.4% | 0.145 | 8.7e-04 |
| 7 | 0.5164 | 93.9% | 0.1516 | 94.6% | 0.181 | 8.2e-04 |
| 8 | 0.5424 | 94.6% | 0.1973 | 93.5% | 0.098 | 7.7e-04 |
| 9 | 0.3812 | 94.7% | 0.1206 | 94.9% | 0.121 | 7.2e-04 |
| 10 | 0.3769 | 94.9% | 0.1071 | 96.0% | 0.155 | 6.6e-04 |
| 11 | 0.4575 | 95.3% | 0.1211 | 95.4% | 0.091 | 6.0e-04 |
| 12 | 0.2991 | 95.2% | 0.1326 | 94.9% | 0.100 | 5.4e-04 |
| 13 | 0.2874 | 95.3% | 0.1202 | 95.3% | 0.080 | 4.7e-04 |
| 14 | 0.2463 | 96.3% | 0.0850 | 96.2% | 0.095 | 4.1e-04 |
| 15 | 0.2465 | 96.5% | 0.0959 | 96.3% | 0.109 | 3.5e-04 |
| 16 | 0.2191 | 96.9% | 0.0905 | 95.9% | 0.090 | 2.9e-04 |
| 17 | 0.2035 | 97.3% | 0.0873 | 96.2% | 0.081 | 2.4e-04 |
| 18 | 0.1878 | 97.9% | 0.0809 | 97.1% | 0.065 | 1.9e-04 |
| 19 | 0.1769 | 97.9% | 0.0746 | 97.5% | 0.056 | 1.4e-04 |
| 20 | 0.1710 | 98.3% | 0.0752 | 97.4% | 0.059 | 1.0e-04 |
| 21 | 0.1630 | 98.6% | 0.0746 | 97.5% | 0.054 | 7.1e-05 |
| 22 | 0.1604 | 98.4% | 0.0751 | 97.5% | 0.050 | 4.5e-05 |
| 23 | 0.1528 | 98.7% | 0.0742 | 97.6% | 0.051 | 2.6e-05 |
| 24 | 0.1505 | 99.0% | 0.0742 | 97.7% | 0.051 | 1.4e-05 |
| 25 | 0.1475 | 99.0% | 0.0744 | 97.7% | 0.050 | 1.0e-05 |

---

## 3. Verdict on BC Initialization

**Status: APPROVED FOR RECURRENT PPO INITIALIZATION.**  
The model has successfully acquired the expert prior without complete entropy collapse (0.050 entropy remaining), ensuring sufficient exploration bandwidth for reinforcement learning discovery.
