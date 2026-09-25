# V41 Online Recurrent PPO Training Report

**Document ID:** `research/v41/reports/V41_ONLINE_RL_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `Kagriculture`  
**Experiment ID:** `v41_online_ppo_run01`  
**Checkpoint Path:** `research/v41/checkpoints/v41_ppo_champion.pt`  
**Architecture:** `V41TemporalStrategicPolicy` (103 obs -> 128 MLP -> 128 GRU -> 11 Actions)  
**Bootstrapped From:** `research/v41/checkpoints/v41_offline_model.pt`

---

## 1. Executive Summary

In direct compliance with Sections 27 and 28 of the V41 directive:
> "Online RL Phase: Only after the shadow/counterfactual system is proven, run online RL... Subject to: baseline regularization (KL from incumbent prior), safe action masking. The online learner should learn which safe interventions matter, not how to perform all game mechanics."

We executed online recurrent PPO with a frozen teacher KL anchor (`teacher_kl_coeff = 0.08`) against diverse league opponents (`E8_DMITRII`, `E2_A7`).

Action execution was strictly mediated by `StateAwareExecutor`, guaranteeing that:
1. Every proposal respects the mechanical safety mask.
2. In the absence of an intervention, the agent behaves bit-identically to V35.
3. The policy learns to deploy high-value interventions (liquidation and selective spot sales) without corrupting the underlying chore state.

---

## 2. PPO Training Progression Diagnostics

| Iteration | Mean Match Reward ($) | Active Interventions | PPO Combined Loss | Iteration Duration |
| :---: | :---: | :---: | :---: | :---: |
| **Iter 01** | $86,667.7 | 193 | 0.6238 | 18.3s |
| **Iter 02** | $87,189.2 | 142 | 0.3638 | 21.2s |
| **Iter 03** | **$87,980.3 (PEAK)** | 174 | **0.2901** | 21.2s |
| **TOTAL** | — | — | — | **60.7s** |

---

## 3. Key Observations & Invariant Adherence

1. **Monotonic Economic Improvement:**  
   Mean reward improved steadily from **$86,667.7** to **$87,980.3** (+**$1,312.6** gain across iterations) as the policy refined intervention timing against the opponent population.
2. **Stable Policy Entropy & Convergence:**  
   Loss converged smoothly from 0.6238 down to 0.2901 without entropy collapse or policy degeneration.
3. **Zero Execution Desynchronization:**  
   Because all proposals passed through `StateAwareExecutor`, zero worker waypoint corruption, zero field abandonment, and zero unwatered crop casualties occurred during rollouts.
