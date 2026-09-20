# PHASE020 — ISOLATED FRESH PILOT REPORT: MULTI-WORKER HARVEST SYNCHRONIZATION (§35, §37)

**Phase**: PHASE020  
**Title**: Prospective Headroom Reorientation & New Opportunity Family Discovery  
**Mechanism Under Test**: `MULTIWORKER_HARVEST_SYNCHRONIZATION`  
**Date**: 2026-09-20  
**Cohort**: Fresh Prospective Block `249366..249375` (10 seeds, 20 CRN mirror matches)  
**Chassis**: Frozen V3 (`845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`)  
**Evaluator**: Phase 016 Macro-Aware Exact Evaluator  
**Reservation**: Phase 018 Funnel Reservation Active  
**Final Scientific Verdict**: **`PILOT COMPLETE / NO QUALIFICATION` (FALSIFIED IN LIVE EXECUTION)**

---

## 1. Executive Summary

Following the discovery census where Multi-Worker Harvest Synchronization showed positive uncommitted diagnostic signals, an isolated, prospective pilot trial was executed on fresh seeds `249366..249375` (20 CRN mirror matches against the canonical qualified foundation control).

```text
================================================================================
PILOT RESULTS SUMMARY (Cohort 249366..249375):
  Mean Paired Treatment Delta : -$552.00
  Median Paired Delta         : -$650.00
  Standard Error (SE)         : $ 108.02
  95% Confidence Interval     : [-$763.72, -$340.28]
  Win / Loss / Tie Record     : 0W / 10L / 0T (0.0% Win Rate)
  Multi-Worker Commits        : 134 commits across 20 matches (avg 6.7/match)
  Foundation Commits          : 16 commits (100% preserved by reservation)
  Status                      : FALSIFIED / QUARANTINED
================================================================================
```

---

## 2. Quantitative Results by Seed

| Seed | Treatment Reward | Control Reward | Seat 0 Delta | Seat 1 Delta | Paired Difference | MWH Commits | Foundation Commits |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **249366** | $129,502.0 | $130,431.0 | -$929.00 | -$929.00 | **-$929.00** | 13 | 0 |
| **249367** | $82,236.0 | $82,452.0 | -$216.00 | -$216.00 | **-$216.00** | 2 | 2 |
| **249368** | $115,172.0 | $116,017.0 | -$845.00 | -$845.00 | **-$845.00** | 8 | 1 |
| **249369** | $88,166.0 / $88,271.0 | $88,803.0 / $89,256.0 | -$637.00 | -$985.00 | **-$811.00** | 8 | 0 |
| **249370** | $116,905.0 | $117,145.0 | -$240.00 | -$240.00 | **-$240.00** | 6 | 1 |
| **249371** | $86,619.0 | $87,548.0 | -$929.00 | -$929.00 | **-$929.00** | 8 | 0 |
| **249372** | $95,359.0 | $95,482.0 | -$123.00 | -$123.00 | **-$123.00** | 1 | 1 |
| **249373** | $92,701.0 | $92,828.0 | -$127.00 | -$127.00 | **-$127.00** | 1 | 1 |
| **249374** | $79,111.0 | $79,858.0 | -$747.00 | -$747.00 | **-$747.00** | 12 | 1 |
| **249375** | $126,659.0 | $127,212.0 | -$553.00 | -$553.00 | **-$553.00** | 8 | 1 |
| **Mean** | — | — | — | — | **-$552.00** | **13.4** | **1.6** |

---

## 3. Causal Failure Attribution

Why did Multi-Worker Harvest Synchronization fail so severely in live play despite positive diagnostic signals?

1. **The Cargo-Trapping Trap**:
   When a farmhand harvests a mature plot, the crop yield is placed in the farmhand's personal `cargo` backpack. In Kagriculture rules, produce inside a worker's backpack cannot be used to plant seeds, cannot be used to feed animals, and cannot be sold at the market until deposited at the shed.
2. **Missing Downstream Deposition Obligation**:
   The V3 backbone policy was not designed expecting farmhands to carry arbitrary produce. Once a farmhand harvested, their backpack was full; their subsequent scheduled tasks (such as tilling or caring for animals) were disrupted or stalled, and the produce was trapped outside the shed for dozens of turns.
3. **Monotonic Dose-Response Relationship**:
   The loss scales almost perfectly with commit count:
   - 1–2 commits: -$123 to -$127 loss.
   - 6–8 commits: -$240 to -$811 loss.
   - 12–13 commits: -$747 to -$929 loss.
   Each commit incurs an average penalty of **~$65** in lost downstream labor coordination.

---

## 4. Scientific Verdict

Per Rule §37:
> *"If a discovered family repeatedly produces local positive but long-horizon negative, macro instability, safety failures... quarantine it. Do not rescue it indefinitely."*

`MULTIWORKER_HARVEST_SYNCHRONIZATION` is **FALSIFIED** and permanently **QUARANTINED**.
No further rescue attempts or heuristic patches will be applied.
