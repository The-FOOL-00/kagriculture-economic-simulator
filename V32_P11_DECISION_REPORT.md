# V32 P11 — DECISION REPORT: TERMINAL PHYSICAL SEARCH OUTCOME & FINAL COMPETITION RECOMMENDATION
**Phase:** V32 P11  
**Date:** 2026-09-23  
**Status:** FORMAL RESEARCH PHASE COMPLETE — FINAL DECISION LOCKED  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. PRIMARY CONCLUSION: SUCCESS B ACHIEVED

```text
========================================================================================
PRIMARY SCIENTIFIC CONCLUSION:
SUCCESS B CONFIRMED — NO LATENT PHYSICAL VALUE IS STRANDED BY A7 IN THE TERMINAL WINDOW.

DEFINITIVE COMPETITION DECISION:
1. FORMALLY AND PERMANENTLY FREEZE A7 AS THE LIVE COMPETITION INCUMBENT FOR SLOT B.
2. CLOSE ALL TERMINAL PLANNING AND RESIDUAL SEARCH BRANCHES PERMANENTLY.
3. RETAIN SLOT B (A7) AND SLOT A (V22R1) IN LIVE PLAY. NO OVERRIDES. DO NOT INVENT P12.
========================================================================================
```

Phase V32 P11 rigorously tested the final evidence-backed research hypothesis: whether a bounded exact physical search during steps 712–718 could recover stranded terminal value from fields and worker pockets.

In strict adherence to the competition promotion protocol (§37, §38, §39):
- **Forensic Disproof of Premise:** The claimed -$1,167.00 loss on seed `249677` against Dmitrii was reproduced down to the cent, but economic decomposition proved that A7 was *already* -$1,351.00 behind at step 712 due to mid-game price shocks. In steps 712–719, A7 actually *out-earned* Dmitrii by +$184.00 ($2,600 vs $2,416).
- **Physical Stranding is Zero:** Across all 10 development seeds, A7 leaves **$0.00** carried in worker hands, **$0.00** in shed inventory, and only $10.00–$21.00 of low-value residual fertilizer on the map.
- **Physical Search Headroom is Exhausted:** A7's 12 workers are already 100% scheduled to harvest and return cargo. Unconstrained physical search detours workers carrying cargo and destroys -$211.00 in cash. Cargo-protected physical search safely abstains ($0.00 delta).
- Per §38, **SUCCESS B** is definitively confirmed. A7 is formally frozen for the final competition submission.

---

## 2. FORMAL ANSWERS TO THE 17 COMPETITION DECISION QUESTIONS (§39)

### Q1: Was the Dmitrii terminal gap reproduced?
**Answer: YES.**
On seed `249677`, the exact -$1,167.00 margin was reproduced down to the penny in both Seat 0 and Seat 1 (A7 = $92,592.00, Dmitrii = $93,759.00).

### Q2: What exact physical value was stranded?
**Answer: VIRTUALLY ZERO ($0.00 Carried, $0.00 Shed, $13.00 Field).**
At step 719, A7 leaves $0.00 in worker pockets, $0.00 in the shed, exactly 1 unharvested cow milk ($1.00), and 12 units of fertilizer ($12.00). Total stranded physical value across the entire map was only $13.00.

### Q3: Can that value be recovered by legal physical actions?
**Answer: NO.**
Reaching the unharvested cow and residual fertilizer requires Manhattan distances $\ge 2$ tiles from available empty hands. Round-trip transit plus harvest plus return to shed plus drop requires $\ge 5$ turns. By the time workers are empty, the remaining turns ($< 4$) are insufficient to return to the shed and drop before step 718.

### Q4: What is the minimum search budget required?
**Answer: 16–34 rollouts.**
A search budget of 34 rollouts evaluates 100% of all physically reachable targets on a 10x10 board within 7 turns. Budgets of 64 or 128 evaluate zero additional feasible candidates.

### Q5: What is the minimum terminal horizon required?
**Answer: 7 steps (Steps 712–718).**
Shorter horizons (e.g. 3 or 5 steps) shrink the reachable radius from the shed to $\le 1$ tile, where zero harvestable targets exist.

### Q6: Does physical-only search work?
**Answer: NO.**
Physical search without cargo protection triggers a fatal -$211.00 cash regression because workers holding high-value cargo detour and fail to reach the shed by step 718. Physical search with cargo protection safely abstains ($0.00 delta).

### Q7: Does terminal monetization add further value?
**Answer: NO.**
A7 baseline already submits `SELL 1000` for all 9 commodities on every single step from 713 to 718. 100% of goods that reach the shed are automatically liquidated.

### Q8: What is the paired improvement versus A7?
**Answer: $0.00.**
Across all 120 benchmark legs against 6 opponent families on both historical and fresh seeds, paired delta is exactly $0.00.

### Q9: What is the worst-case loss?
**Answer: $0.00 (Fail-Closed) / -$211.00 (Unconstrained).**
With fail-closed acceptance and cargo guards active, the worst-case loss is $0.00. Without cargo guards, the worst-case loss is -$211.00.

### Q10: Does the effect survive fresh seeds?
**Answer: NOT APPLICABLE.**
There is no positive effect on historical seeds; on fresh seeds, physical inventory remains equally saturated ($0.00 carried, $0.00 shed).

### Q11: Does it survive multiple opponents?
**Answer: NOT APPLICABLE.**
The planner cleanly abstains across all 6 opponent families (`E8_DMITRII`, `E0_V3`, `E1_V22R1`, `E2_A7`, `V54`, `SYN_AGG`).

### Q12: Does it survive boundary perturbations?
**Answer: YES.**
Under all 10 adversarial boundary tests (position $\pm 1$, entry step $710–714$, price spikes/drops, cargo injection), the candidate safely abstains to A7 baseline with zero crashes, zero illegal moves, and zero tail losses.

### Q13: What is the runtime?
**Answer: 46.1 ms (Peak: 62.4 ms).**
The entire terminal search consumes only 23.5% of the 200 ms Kaggle per-turn limit. Pre-712 steps execute in 0.018 ms.

### Q14: Is the candidate safe enough for controlled live validation?
**Answer: NO (REDUNDANT).**
While completely tail-safe due to fail-closed abstention, it provides 0.0% activation and $0.00 alpha. Deploying an identical passthrough wrapper introduces deployment complexity with zero upside.

### Q15: If not, why?
**Answer:** Because A7's underlying physical route is already optimal and exhausts all realizable terminal physical value.

### Q16: Should A7 remain frozen?
**Answer: YES (DEFINITIVE FREEZE).**
A7 has conclusively beaten all challenger candidates across P8, P9, P10, and P11. It achieves a 98.3% win rate across the entire benchmark suite.

### Q17: What exact evidence would be required before changing Slot B?
**Answer:** Statistically significant ($p < 0.01$), tail-safe ($worst \ge -\$50$) improvement exceeding +$100.00 mean paired delta across $\ge 200$ prospective holdout seeds. No such evidence exists. Slot B is permanently locked to A7.

---

## 3. PROMOTION GATES AUDIT (§26)

| Gate | Requirement | Measured Result | Status |
| :--- | :--- | :--- | :---: |
| **GATE 1** | A7 identity outside terminal window | 100% bit-identical on steps 0–711 | **PASSED** |
| **GATE 2** | Zero unexpected illegal actions | 0 illegal actions across all matches | **PASSED** |
| **GATE 3** | Zero crashes | 0 crashes across 120 matches | **PASSED** |
| **GATE 4** | Zero protected-file modification | A7 SHA-256 identical (`51c1d25245f6...`) | **PASSED** |
| **GATE 5** | Reproduces intended forensic mechanism | -$1,167 reproduced; confirmed non-physical | **PASSED** |
| **GATE 6** | Positive paired terminal delta | Delta is $0.00 (Zero alpha headroom) | **FAILED (STOP)** |
| **GATE 7** | No unacceptable negative-tail behavior | Worst case is $0.00 under fail-closed | **PASSED** |
| **GATE 8** | Improvement on fresh seeds | Delta is $0.00 on fresh seeds | **FAILED (STOP)** |
| **GATE 9** | Not restricted to one opponent | Abstains across all opponents | **PASSED** |
| **GATE 10**| Acceptable runtime | 46.1 ms (Limit: 200 ms) | **PASSED** |
| **GATE 11**| Stable under boundary perturbations | 10/10 adversarial tests safely abstained | **PASSED** |
| **GATE 12**| No hidden-state dependence | Operates strictly from legal observation | **PASSED** |

**Promotion Verdict:** Because Gates 6 & 8 cannot be satisfied (physical headroom is completely exhausted by A7), the candidate is **QUARANTINED** and A7 is **PERMANENTLY FROZEN**.

---

## 4. PERMANENT STOP LIST & PROTOCOL CLOSURE (§37, §40)

With the completion of Phase 11, the following research branches are permanently closed:
- **PPO / RL / Imitation Learning:** Permanently closed (infeasible sample complexity / policy collapse).
- **Macro Strategy Rewrites / Crop Mix Swaps:** Permanently closed (worsens baseline win rate).
- **Labor Optimizer / Hiring Schedule Overhauls:** Permanently closed (destroys mid-game capital velocity).
- **Residual Market Interventions (R01, R02, R02_B, R03, R05, R07):** Permanently closed (catastrophic tail risk / redundant).
- **Terminal Physical Path Planning (P11):** Permanently closed (exhausted physical headroom; A7 already liquidates 100%).

---

## 5. FINAL COMPETITION DEPLOYMENT SPECIFICATION

For the final Kaggle submission deadline (September 30, 2026):
- **Slot A (Primary Portfolio Diversifier):** `submission_aec_v22r1.tar.gz` (V22R1).
- **Slot B (Primary Portfolio Incumbent):** `candidates/v30_a7_standalone/main.py` (`A7`).
- **Research Program Status:** **CONCLUDED AND LOCKED.**
