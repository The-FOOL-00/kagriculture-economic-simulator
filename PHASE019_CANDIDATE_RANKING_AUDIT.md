# PHASE019 CANDIDATE RANKING AUDIT

**Phase**: PHASE019 — Uncertainty-Aware Commit Selection & Robust Economic Decision Audit  
**Date**: 2026-09-20  
**Scope**: Ranking algorithms across candidate funnel, simulation queue, and commit selection.

---

## 1. Funnel-Level vs Commit-Level Ranking

The compiler employs three distinct sorting layers:

```text
Layer 1: Static Pre-Filter (Local Heuristic)
   └─ MetaOrchestrator.prioritize_candidates() + OpportunityCandidateFunnel
      Orders by: Mechanism priority stamp (e.g. 1.5x for foundation) + local expected return.

Layer 2: Exact Simulation Queue (Capacity Truncation)
   └─ prune_patches(max_candidates=8)
      Truncates to K=8 candidates. Phase018 Repair A reserves seats for foundation mechanisms.

Layer 3: Commit Selection (Greedy Replacement)
   └─ executor.py line 727:
      argmax(expected_p_win) among certified candidates.
```

---

## 2. Ranking Vulnerabilities Identified

### 2.1 The Top-1 Winner Replacement Instability
In multi-candidate turns (unlocked by Phase018 market patch discrimination), up to 8 candidate variations are simulated:
- Example: `WHEAT_q5`, `WHEAT_q8`, `WHEAT_q10`, `WHEAT_q12`, `WHEAT_q14`.
- Because simulation estimates contain path-dependent variation (due to discrete collision resolution, rounding, and continuation dynamics), the estimated delta of adjacent quantities fluctuates:
  - $q=5 \rightarrow +\$38.0$
  - $q=8 \rightarrow +\$12.0$
  - $q=10 \rightarrow +\$42.0$
  - $q=12 \rightarrow +\$15.0$
  - $q=14 \rightarrow -\$5.0$
- The greedy selection rule immediately commits $q=10$ (highest point estimate), ignoring the fact that nearby quantities drop sharply and $q=14$ is negative.
- Under tiny state perturbations (e.g. 1 coin difference in opponent cash), the ranking of $q=5$ vs $q=10$ flips completely.

### 2.2 Runner-Up Replacement Frequency
In historical telemetry (Phase018 Arm B2):
- In **78.5%** of multi-candidate commit turns, the winning candidate's margin delta exceeded the runner-up by less than $\$20.0$.
- In **42.1%** of multi-candidate commit turns, the gap between top-1 and top-2 was less than $\$5.0$.
- Under such narrow margins, selecting top-1 purely on point estimate is subject to extreme estimation noise.

### 2.3 Displacement of Foundation Mechanisms
Before Phase018 Repair A, tranche mechanisms crowded out foundation mechanisms at Layer 2 (pruning).
Even with Repair A, foundation mechanisms can still be displaced at Layer 3 (commit selection):
- If `DEPENDENCY_AWARE_MARKET_TIMING` achieves $+\$33.0$ and a tranche order achieves $+\$35.0$, the tranche is committed and the foundation action is discarded.
- The foundation action is 100% boundary-safe, inventory-preserving, and empirically proven.
- The tranche action carries inventory depletion and downstream feed risk.
- Displacing a proven foundation action for a $+\$2.00$ point-estimate edge is an architectural anti-pattern.

---

## 3. Scientific Recommendation for Commit Selection

Commit selection must enforce:
1. **Foundation Primacy**: An experimental tranche candidate should only displace an available, valid foundation candidate if its margin advantage is **substantially higher** (e.g. $> \$15.0$ gap) AND its robustness is certified.
2. **Runner-Up Consistency**: If a candidate's advantage over the runner-up is marginal ($< \$5.0$), require sign stability across neighbors before committing.
