# V34 Physical Synchronization & Choreography Safety Audit

**Program:** Kagriculture V34 Research Program (A7 Tactical Forward Search)  
**Author:** Lead Research Scientist, Competitive-Programming Engineer, Simulator Engineer, and Implementation Owner  
**Date:** 2026-09-24  
**Scope:** Quantitative evaluation of worker physical displacement, task divergence, and resynchronization dynamics following tactical interventions.  

---

## 1. Executive Summary: The Choreography Integrity Invariant

In Kaggriculture, A7 achieves its top-tier competitive standing not through complex dynamic planning, but through **tick-exact, deterministic choreography**:
- Farmers and hired hands navigate fixed spatial paths across farm tiles.
- Sowing, daily watering, fertilizer application, feeding, and harvesting follow tightly coupled dependencies ($P(\text{watered}) = 1.0$ when hands arrive on schedule).
- If an intervention causes even a single worker to be displaced by 1 tile ($D_{\text{Manhattan}} \ge 1$), that worker misses its scheduled watering or harvest, triggering unwatered crop penalties, delayed inventory arrival, and cascading desynchronization.

V34 establishes a mandatory **Physical Safety Invariant**:
```
A tactical intervention that earns positive cash but displaces workers
or breaks future A7 choreography is strictly INVALID.
```

---

## 2. Tracking Worker Divergence & State Distance

For every evaluated candidate rollout, worker states are tracked against the undisturbed A7 baseline:

1. **Farmer Manhattan Displacement:**
   $$D_{\text{farmer}}(t) = |x_t^{\text{cand}} - x_t^{\text{base}}| + |y_t^{\text{cand}} - y_t^{\text{base}}|$$
2. **Hand Position Divergence:**
   $$D_{\text{hands}}(t) = \sum_{i=1}^{N_{\text{hands}}} \left(|x_{t,i}^{\text{cand}} - x_{t,i}^{\text{base}}| + |y_{t,i}^{\text{cand}} - y_{t,i}^{\text{base}}|\right)$$
3. **Task Feasibility Check:**
   Verifies whether the next scheduled A7 action $a_{t+1}^{\text{base}}$ remains legally executable by the unit at its actual position.

---

## 3. Physical Safety Profiles by Candidate Cohort

| Tactical Candidate Cohort | Unit Physical Impact | Farmer Displacement ($D_{\text{farmer}}$) | Hand Displacement ($D_{\text{hands}}$) | Resynchronization Ticks Required | Physical Safety Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Cohort A: Step 0 Wash Sizing** | Market orders only (`farmer=["PASS"]`) | **0.0** | **0.0** | **0 ticks (Instant)** | **100% SAFE** |
| **Cohort B: Late Planting Cutoff** | Converts futile `PLANT` to `PASS` | **0.0** | **0.0** | **0 ticks (Stationary)** | **100% SAFE** |
| **Cohort C: Pre-Liquidation Dump** | Market orders only | **0.0** | **0.0** | **0 ticks (Instant)** | **100% SAFE** |
| **Cohort D: Pre-Wage Reserve Buffer** | Market orders only | **0.0** | **0.0** | **0 ticks (Instant)** | **100% SAFE** |
| **P12 Land Expansion (Macro)** | Worker redirected to build | $\ge 4.0$ | $\ge 8.0$ | 28 ticks | **DISQUALIFIED** |
| **V33 Dmitrii Splicing (Macro)** | Spliced animal logic onto crop farm | $\ge 12.0$ | $\ge 24.0$ | $\infty$ (Failed resync) | **DISQUALIFIED** |

---

## 4. Policy Decision

All promoted tactical candidates in V34 operate with **zero spatial displacement ($D = 0$)**:
- Workers remain on their choreographed paths.
- Tactical deviations modify only transaction quantities, pricing timings, and terminal planting cutoffs.
- Physical synchronization remains 100% intact across all 720 game steps.
