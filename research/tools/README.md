# Reusable Scientific & Forensic Tools

This directory contains the production-grade diagnostic, counterfactual analysis, and forensic tools developed during the V49–V60 research campaigns. These utilities were promoted from historical exploration scratchpads to permanent repository tooling.

---

## Tool Catalog

| Script | Size (Bytes) | Category | Description & Usage |
| :--- | :---: | :---: | :--- |
| `trace_milk_sales.py` | 1,829 | **Economic Tracer** | Fast milk sales and commodity cash-flow tracer using `FastKagricultureSim`. Simulates and records exact turn-by-turn milk production, spoilage, and market sale timestamps. |
| `build_causal_traces.py` | 2,742 | **Causal Forensics** | Generates step-by-step diff trees and state divergence logs between two competing agents across arbitrary random seeds. |
| `build_divergence_detector.py` | 3,915 | **State Forensics** | Detects observable vs. unobservable divergence points in head-to-head matches, mapping the exact boundary of opponent predictability. |
| `deep_forensic_four_losses.py` | 8,992 | **Failure Analysis** | Microscopic forensic autopsy script for V49's 4 historical loss regimes. Reconstructs full inventory, market order queues, and step 697 collision mechanics. |
| `run_full_counterfactual_matrix.py` | 12,739 | **Counterfactual Engine** | Evaluates combinatorial candidate actions across multi-seed counterfactual rollouts to measure statistical alpha ($\Delta Q > 0$). |
| `audit_blocked_actions_comprehensive.py` | 1,747 | **Action Integrity** | Comprehensive audit utility that scans thousands of simulation steps to detect and quantify illegal or engine-blocked action attempts. |
| `verify_prefix_parity_and_reconstruct.py` | 4,134 | **Engine Verification** | Validates prefix execution parity between `FastKagricultureSim` and official `kaggle-environments 1.32.7`, reproducing full tournament traces. |
| `inspect_candidate_transforms.py` | 1,378 | **Action Inspection** | Inspects action transformation pipelines and filters applied to agent candidate outputs before engine submission. |

---

## Execution Environment

All tools in this directory are standalone and executable from the repository root:

```bash
python research/tools/trace_milk_sales.py
python research/tools/deep_forensic_four_losses.py
python research/tools/run_full_counterfactual_matrix.py
```
