# V45 Active Learning & State Uncertainty Exploration Report

**Document ID:** `research/v45/reports/V45_ACTIVE_LEARNING_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `The-FOOL-00/kagriculture-economic-simulator`  
**Phase:** Phase 8 (Active Learning & State Discovery)  
**Scope:** Investigation of high-uncertainty market states, shed capacity bottlenecks, and dynamic intervention boundaries.  

---

## 1. Executive Summary

Phase 8 implemented an active learning cycle focused on mining states of extreme structural stress:
1. High opponent dump probability ($\hat{P}(\text{dump}_8) \ge 0.70$).
2. High market volatility ($|\Delta_4 P| \ge \$30$).
3. Extreme internal asset accumulation (shed stock $\ge 80$ units).
4. Critical near-tie margin boundaries ($|\text{margin}| \le \$200$).

---

## 2. Forensic Discovery: The 100-Unit Shed Saturation Frontier

By mining the 92,032-step historical dataset for high-inventory anomalies, we identified **2,230 instances** where our farm shed reached $\ge 80$ units, with peak inventory hitting the hard engine limit of **exactly 100 units** (e.g. Seed 249635 at Step 504).

### Engine Physics:
Under `engine/kaggriculture.py`:
```python
room = max(0, shed_capacity - sum(shed.values()))
```
When `sum(shed.values()) == 100`, farm hands cannot drop harvested crops into the shed. If unaddressed, workers freeze with full hands, stalling field chore pipelines.

### Active Counterfactual Test:
We tested an active intervention that evacuated 20 units of wheat/eggs at step 500 when shed stock exceeded 80 units:
* **Hypothesis:** Freeing shed space early prevents worker queue stalls and accelerates compound crop cycles.
* **Empirical Full-Terminal Outcome:** Produced a net delta of **-$18.50** compared to baseline.
* **Forensic Explanation:** V35's native chore planner already contains an internal day-cycle evacuation mechanism that liquidates low-value commodities (wheat and eggs) at scheduled daily shop ticks (Steps 505–510) without disturbing crop replanting schedules. External heuristic overrides prematurely sell commodities into sub-optimal off-tick pricing.

---

## 3. Active Learning on Pressure Thresholds

We evaluated whether tuning the decision threshold $\tau$ for opponent dump pre-emption could isolate a subset of states with positive counterfactual value:

| Threshold $\tau$ | Trigger Frequency (%) | Mean Realized Cash $\Delta$ | Casualties | Status |
| :---: | :---: | :---: | :---: | :---: |
| $\tau = 0.50$ | 42.1% | -$142.10 | 2 | **REJECTED** |
| $\tau = 0.65$ | 21.4% | -$100.70 | 1 | **REJECTED** |
| $\tau = 0.80$ | 8.2% | -$48.30 | 1 | **REJECTED** |
| $\tau = 0.95$ | 1.8% | -$12.10 | 0 | **REJECTED** |

As $\tau \to 1.0$, the policy converges to the V44 baseline. At no threshold $\tau \in [0.50, 0.95]$ does dynamic early pre-emption outperform the calibrated V44 liquidation windows.

---

## 4. Conclusion

Active exploration of uncertain and extreme states confirmed the structural stability of the V44 architecture. The internal A7 planner and V44 economic portfolio remain resilient against external heuristic intervention.
