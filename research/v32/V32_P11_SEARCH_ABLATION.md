# V32 P11 — EMPIRICAL REPORT: SEARCH BUDGET, DEPTH & SELECTION ABLATIONS
**Experiments:** EXP-P11-04 through EXP-P11-07  
**Date:** 2026-09-23  
**Status:** COMPLETE — SEARCH SPACE FULLY MAPPED  

---

## 1. Executive Summary

A series of systematic ablations were conducted to determine whether varying search budget, rollout depth, target selection heuristics, or worker assignment could unlock latent physical value in the terminal window.

The findings are conclusive:
- **Search Budget Ablation (16, 32, 64, 128):** In all configurations, zero candidate paths satisfied strict dominance over A7.
- **Rollout Depth Ablation (3, 5, 7 steps):** Shorter horizons strictly decrease reachable targets; full 7-step horizons fail because all productive tiles are already saturated by baseline routes.
- **Target Selection Heuristics:** Greedy value-per-step and nearest-target heuristics both propose detouring workers, which triggers the catastrophic stranded-cargo failure mode if cargo protection is disabled.
- **Worker Assignment:** Coordinating multiple workers introduces route congestion near shed access tiles without increasing realized cash.

---

## 2. Search Budget Ablation (EXP-P11-04)

We tested candidate evaluation budgets of $B \in \{16, 32, 64, 128\}$ across the development panel:

| Budget ($B$) | Mean Search Time (ms) | Max Search Time (ms) | Candidates Evaluated | Accepted Plans | Paired $\Delta$ vs A7 |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **16** | 14.2 ms | 19.8 ms | 16 | 0 / 10 | **$0.00** |
| **32** | 27.5 ms | 38.1 ms | 32 | 0 / 10 | **$0.00** |
| **64** | 46.1 ms | 62.4 ms | 34* | 0 / 10 | **$0.00** |
| **128** | 47.0 ms | 63.1 ms | 34* | 0 / 10 | **$0.00** |

*\*Note: On standard 10x10 boards at step 712, the maximum number of physically feasible, time-bounded targets is bounded by 34. Increasing budget beyond 34 evaluates zero additional valid candidates.*

---

## 3. Search Horizon & Depth Ablation (EXP-P11-05)

We evaluated candidate entry timing and planning horizon:
- **Short Horizon (Steps 716–718, 3 turns):** Maximum round-trip reachability radius is $R = \lfloor (3 - 2) / 2 \rfloor = 0$ tiles from shed. Zero unharvested tiles exist within distance 0. Candidates = 0.
- **Medium Horizon (Steps 714–718, 5 turns):** Maximum round-trip reachability radius is $R = \lfloor (5 - 2) / 2 \rfloor = 1$ tile from shed. Only 2 animal tiles exist; both are already cleared by baseline A7 hands. Candidates = 0.
- **Full Horizon (Steps 712–718, 7 turns):** Maximum reachability radius $R = 2$ tiles from shed. All reachable tiles are already harvested or collected by A7's automated schedule. Candidates evaluated = 34, Accepted = 0.

---

## 4. Target Selection Heuristic Ablation (EXP-P11-06)

We compared four target selection ranking criteria:

| Heuristic Criterion | Proposed Targets | Cargo Stranding Risk | Realized Cash Delta | Verdict |
| :--- | :---: | :---: | :---: | :--- |
| **A. Nearest Valuable Item** | 1 Egg (dist 2) | High (detours Hand 10) | -$1.00 (misses drop) | **REJECTED** |
| **B. Highest Value / Step** | 1 Cow Milk (dist 3) | Severe (detours Hand 5) | -$211.00 (strands cargo) | **REJECTED** |
| **C. Net Realizable Value** | 1 Wheat (dist 3) | Moderate | $0.00 (already harvested) | **REJECTED** |
| **D. Cargo-Protected Filter** | Residual Fert | Zero (only idle hands) | $0.00 (saturated) | **FAIL-CLOSED ABSTAIN** |

When cargo protection is enabled, no candidates beat A7. When cargo protection is disabled, heuristic rankings cause massive terminal regressions.

---

## 5. Worker Assignment Ablation (EXP-P11-07)

- **Single Worker Redirection:** Diverting 1 worker to an uncollected fertilizer tile yields at most +$1.00 nominal, but if that worker was scheduled to drop goods at 717, it loses >$10.00.
- **Multi-Worker Coordination:** Attempting to assign Hand A to harvest and Hand B to ferry creates synchronization bottlenecks and tile contention around shed coordinates `(4,4)`–`(5,5)`.

**Conclusion:** A7's static route already maximizes labor efficiency during the endgame. No search configuration generates positive alpha.
