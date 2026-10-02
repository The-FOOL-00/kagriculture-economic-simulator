# V38 Behavioral Cloning (BC) Warm-Start Results

**Document ID:** `V38_BC_RESULTS.md`  
**Date:** 2026-09-25  
**Candidate:** `candidates/v38_heuristic_ppo/`  
**Checkpoint:** `scratch/v38/bc_policy.pt`  
**Metrics:** `scratch/v38/bc_metrics.json`  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. Executive Summary

Behavioral Cloning was trained to initialize the `MacroActorCritic` network using the audited counterfactual expert dataset. On an independent, held-out validation seed cohort (`seed 249638`), the BC model achieved **87.50% macro-option validation accuracy**, **100.0% heuristic agreement**, and **0.0% false intervention rate**, with an average output confidence of **90.63%**.

---

## 2. Experimental Setup

* **Model Architecture:** `MacroActorCritic` MLP (64 input features $\to$ 128 hidden $\to$ 128 hidden $\to$ 11 macro logits, LayerNorm, Tanh activations, masked logits).
* **Optimizer:** AdamW ($\text{lr} = 10^{-3}$, weight decay $= 10^{-4}$, batch size $= 16$).
* **Loss Function:** Masked Cross-Entropy Loss on macro target option + MSE Loss on estimated value.
* **Epochs:** 60 epochs.
* **Split Strategy:**
  * Training Set: 96 states across seeds `249635`, `249636`, `249637`.
  * Validation Set: 32 states on strictly held-out seed `249638`.

---

## 3. Empirical Results

| Metric | Random Baseline | Final BC Model | Benchmark Target | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Validation Accuracy** | 9.09% | **87.50%** | $\ge 75.0\%$ | **PASSED** |
| **Training Accuracy** | 9.09% | **92.71%** | $\ge 80.0\%$ | **PASSED** |
| **Heuristic Agreement** | 9.09% | **100.00%** | $\ge 95.0\%$ | **PASSED** |
| **False Intervention Rate** | ~90.0% | **0.00%** | $\le 5.0\%$ | **PASSED (Perfect Invariance)** |
| **Mean Output Confidence** | ~9.0% | **90.63%** | $\ge 70.0\%$ | **PASSED** |
| **Training Wall Time** | — | **4.7 seconds** | $< 30$ seconds | **PASSED** |

---

## 4. Analysis of Learned Policy Dynamics

1. **Perfect Retention of the Heuristic Bedrock:**
   On all validation states where the expert determined that no deviation produced positive alpha, the BC policy chose `0: TRUST_HEURISTIC` with 100% fidelity. It produces **0.0% false interventions**, completely eliminating the unguided exploration collapse that ruined RL-X2.
2. **Selective Intervention Discovery:**
   The policy successfully learned the economic signatures for `EXPAND_LAND` (action 1) and `RECOVERY` (action 10), activating only when liquidity buffers and arable space thresholds were satisfied.
3. **PPO Warm-Start Readiness:**
   Because Behavioral Cloning reliably learned the expert prior and achieved 87.5% validation accuracy, Phase 11 (PPO Fine-Tuning) is authorized to proceed.
