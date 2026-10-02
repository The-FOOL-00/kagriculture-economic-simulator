# Kagriculture Scratch Directory Content-Level Audit

**Audit Date**: October 2, 2026  
**Auditor**: Forensic Pre-Push Audit  
**Total Tracked Scripts in `scratch/`**: 1,473  
**Total Untracked Debris Purged**: 377 files (65.84 MB)  
**Disposable Untracked Files Remaining**: 0  

---

## 1. Executive Summary

A comprehensive content-level audit of `scratch/` was conducted to distinguish reusable research tooling from historical exploration scripts and disposable simulation dumps. 

1. **Promoted Tools**: Eight reusable, production-grade forensic analysis scripts have been permanently promoted to [`research/tools/`](file:///c:/Users/Sundareswaran/Kagriculture/research/tools) with full documentation in [`research/tools/README.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/tools/README.md).
2. **Purged Debris**: 377 untracked, disposable raw JSON simulation logs and tournament dumps (~65.84 MB) in `scratch/` (including `scratch/jit_melon_results/`) have been removed from the working tree.
3. **Retained Historical Scripts**: The remaining 1,473 Python scripts in `scratch/` represent the step-by-step diagnostic and ablation history across the tournament. They remain preserved in Git history as part of the immutable project record established in commit `07b80b8`.

---

## 2. Reusable Forensic Tools Promoted to `research/tools/`

| Tool Name | Size (Bytes) | Category | Functional Purpose & Reproducibility Value |
| :--- | :---: | :---: | :--- |
| `trace_milk_sales.py` | 1,829 | **Economic Tracer** | Turn-by-turn simulation tracer tracking cow production, milk spoilage, and market cash realization using `FastKagricultureSim`. |
| `build_causal_traces.py` | 2,742 | **Causal Forensics** | Step-by-step state divergence and action diff generator between competing agent variants. |
| `build_divergence_detector.py` | 3,915 | **State Forensics** | Detects observable vs. unobservable state bifurcation points in competitive matches. |
| `deep_forensic_four_losses.py` | 8,992 | **Failure Analysis** | Microscopic forensic autopsy of V49's 4 historical loss regimes, reconstructing queue priorities and step 697 collision mechanics. |
| `run_full_counterfactual_matrix.py` | 12,739 | **Counterfactual Engine** | Evaluates candidate action alterations across multi-seed rollouts to measure policy value delta ($\Delta Q$). |
| `audit_blocked_actions_comprehensive.py` | 1,747 | **Action Integrity** | Comprehensive scanner detecting and classifying illegal or engine-blocked action attempts. |
| `verify_prefix_parity_and_reconstruct.py` | 4,134 | **Engine Verification** | Validates prefix execution parity between `FastKagricultureSim` and official `kaggle-environments 1.32.7`. |
| `inspect_candidate_transforms.py` | 1,378 | **Action Inspection** | Inspects action transformation pipelines and filters applied to agent candidate outputs. |

---

## 3. Disposed Scratch Debris (Purged from Working Tree)

The following classes of untracked intermediate outputs were safely purged:

| Directory / Pattern | File Count | Size (MB) | Reason for Disposal |
| :--- | :---: | :---: | :--- |
| `scratch/*.json` | 309 | 51.54 MB | Ephemeral raw episode telemetry dumps; intermediate outputs fully regenerable from scripts. |
| `scratch/jit_melon_results/*.json` | 19 | 12.20 MB | Temporary JIT melon timing simulation output logs. |
| `scratch/v39/live/logs/*.json` | 16 | 0.60 MB | Stale V39 ladder connection test logs. |
| `scratch/v39/loss_states/*.json` | 7 | 0.54 MB | Temporary loss state checkpoints superseded by V56 forensic dossiers. |
| `scratch/checkpoints/*.json` | 4 | 0.51 MB | Ephemeral intermediate solver states. |
| `scratch/v38/*.json` | 9 | 0.34 MB | Obsolete V38 PPO loss telemetry dumps. |
| `scratch/v39/public_meta/*.json` | 8 | 0.06 MB | Cached public ladder metadata snapshots. |
| **Total** | **377** | **65.84 MB** | **All disposable untracked items eliminated.** |

---

## 4. Retained Historical Scripts Classification

The 1,473 tracked scripts in `scratch/` fall into the following historical categories:

1. **Ablation Studies (`scratch/ablation_agents_v4/`, `scratch/ablation_forensics/`)**: Preserved historical counterfactual agents testing removal of emergency liquidity, feed buffers, and cycle-2 melons.
2. **Adversarial Agents (`scratch/adversaries/`, `scratch/adv_agents/`)**: Preserved stress-test opponents (e.g., melon predator, wheat cornerer, cow juggernaut).
3. **Phase-Specific Explorations (`scratch/v38/`, `scratch/v39/`)**: Preserved investigative scripts documenting the progression from early heuristic models to the V49 Meta Fusion chassis.

All active and ongoing investigation tools should reference [`research/tools/`](file:///c:/Users/Sundareswaran/Kagriculture/research/tools).
