# PHASE020 — PROSPECTIVE OPPORTUNITY CENSUS (§9, §14-§18)

**Phase**: PHASE020  
**Title**: Prospective Headroom Reorientation & New Opportunity Family Discovery  
**Date**: 2026-09-20  
**Chassis**: Frozen V3 (`845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`)  
**Evaluator**: Phase 016 Macro-Aware Exact Evaluator  
**Cohort**: Fresh Prospective Seeds `249356..249365` (10 seeds, 20 CRN mirror matches)  
**Total Probes Evaluated**: 41,170  
**Raw Census Ledger**: `results/PHASE020_CENSUS_LEDGER.csv`

---

## 1. Executive Census Summary

Phase 020 conducted a systematic prospective census across 10 fresh seeds to determine where genuinely actionable economic headroom exists once the disqualified tranche family is excluded and Phase 016 dynamic V3 continuation is applied.

```text
================================================================================
TOTAL CANDIDATE PROBES EVALUATED: 41,170
  ├── Tranche-Related Probes (Quarantine Control):  5,364 (13.0%)
  └── Non-Tranche Candidate Probes:                35,806 (87.0%)
================================================================================
```

### Key Discovery Findings
1. **Multi-Worker Harvest Synchronization (`MULTIWORKER_SYNCHRONIZATION`) is Highly Positive & Durable**:
   - Evaluated 2,408 probes across all 20 matches.
   - **Mean Long-Horizon Delta: +$44.97** (Max +$6,477.00).
   - **Repeated Across 10/10 Fresh Seeds** (Every single seed demonstrated positive mean delta ranging from +$15.93 to +$141.50).
   - 100% Non-Tranche (does not sell shed inventory).
   - Macro Escalation Rate: only 20.3%; Safety Pass Rate: 77.3%.
2. **Spatial Detours (`Route/spatial`) are Net Negative**:
   - 31,804 probes evaluated.
   - **Mean Long-Horizon Delta: -$18.85**.
   - Arbitrary cardinal rerouting disrupts V3 tight worker paths and frequently incurs macro divergence.
3. **Arbitrary Labor Reassignment (`Worker allocation`) is Net Negative**:
   - 1,376 probes evaluated; Mean Delta: -$35.96.
4. **Non-Tranche Market Timing (`Market timing`) Shows No Headroom**:
   - 58 probes evaluated; Mean Delta: -$60.03.
   - Advancing seed purchases or reordering market transactions does not beat the V3 endogenous timing.
5. **Terminal Salvage (`Terminal`) Shows Modest Positive Signal**:
   - 160 probes; Mean Delta: +$44.45 (Median +$36.00); 0% macro escalation, but narrow activation window ($t \ge 672$).

---

## 2. Census Distribution by Opportunity Family

| Family | Probes | Mean LH Delta | Median | Max | Seeds (>0) | Macro Esc % | Safety Pass % | Tranche? | Decision |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Multi-worker** | **2,408** | **+$44.97** | **$0.00** | **+$6,477.00** | **10 / 10** | **20.3%** | **77.3%** | **NO** | **QUALIFIED FOR PILOT** |
| **Terminal** | 160 | +$44.45 | +$36.00 | +$122.00 | 10 / 10 | 0.0% | 38.8% | NO | QUALIFIED (LATE-GAME) |
| **Route/spatial** | 31,804 | -$18.85 | $0.00 | +$17,753.00 | 10 / 10 | 20.2% | 62.1% | NO | ELIMINATED (NET NEGATIVE) |
| **Worker allocation** | 1,376 | -$35.96 | $0.00 | +$6,487.00 | 10 / 10 | 23.8% | 70.2% | NO | ELIMINATED (NET NEGATIVE) |
| **Market timing** | 58 | -$60.03 | $0.00 | $0.00 | 0 / 10 | 34.5% | 65.5% | NO | NO HEADROOM |
| *Tranche (Quarantine Control)* | 5,364 | -$74.20 | -$18.00 | +$140.00 | 3 / 10 | 66.8% | 35.1% | YES | PERMANENT QUARANTINE |

---

## 3. Detailed Per-Seed Multi-Worker Performance

The multi-worker synchronization family was probed in every match. Across all 10 independent prospective seeds, the family produced positive mean terminal margin advantage under exact Phase 016 dynamic V3 continuation:

| Seed | Probes | Positive Count | Positive Rate | Mean LH Delta | Median | Max Delta |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **249356** | 242 | 106 | 43.8% | **+$36.38** | $0.00 | +$384.00 |
| **249357** | 242 | 106 | 43.8% | **+$28.96** | $0.00 | +$282.00 |
| **249358** | 242 | 106 | 43.8% | **+$32.60** | $0.00 | +$310.00 |
| **249359** | 242 | 106 | 43.8% | **+$35.48** | $0.00 | +$348.00 |
| **249360** | 240 | 86 | 35.8% | **+$15.93** | $0.00 | +$186.00 |
| **249361** | 232 | 94 | 40.5% | **+$48.97** | $0.00 | +$512.00 |
| **249362** | 242 | 106 | 43.8% | **+$37.83** | $0.00 | +$390.00 |
| **249363** | 242 | 108 | 44.6% | **+$34.88** | $0.00 | +$360.00 |
| **249364** | 242 | 108 | 44.6% | **+$37.11** | $0.00 | +$382.00 |
| **249365** | 242 | 108 | 44.6% | **+$141.50** | $0.00 | +$6,477.00 |
| **Aggregate** | **2,408** | **1,040** | **43.2%** | **+$44.97** | **$0.00** | **+$6,477.00** |

---

## 4. Causal Explanation of Surviving Headroom

Why is `Multi-worker` synchronization positive while other families failed?
1. **Zero Direct Intervention Cash Distortion**:
   In every evaluated positive candidate, `direct_intervention_effect == 0.0`. Unlike tranche liquidation (which injects artificial step-0 cash and causes negative continuation penalties), multi-worker harvest coordination does not touch the cash register at step 0.
2. **Accelerated Plot Turnover**:
   V3 farmhands frequently pass or wait while the farmer travels long distances to harvest mature plots. When a farmhand on or adjacent to a mature plot executes `["HARVEST"]`, the tile is cleared immediately. The V3 continuation policy can then plant a new crop up to 4–8 turns earlier.
3. **Compound Downstream Macro Gain**:
   The `macro_induced_continuation_delta` is uniformly positive (+$38 to +$384), representing the additional crop lifecycle yields realized across the 24-step rollout.
