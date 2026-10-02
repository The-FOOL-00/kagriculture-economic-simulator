# PHASE020 — OPPORTUNITY FAMILY MATRIX (§23, §41)

**Phase**: PHASE020  
**Title**: Prospective Headroom Reorientation & New Opportunity Family Discovery  
**Date**: 2026-09-20  
**Chassis**: Frozen V3 (`845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`)  
**Evaluator**: Phase 016 Macro-Aware Exact Evaluator  
**Cohort**: Seeds `249356..249365` (10 seeds, 20 mirror matches)  

---

## 1. Required Final Family Matrix (§41)

| Opportunity Family | Frequency | Mean Long-Horizon Delta | Max | Seeds | Macro Stability | Safety | Non-Tranche | Representable | Decision |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Multi-worker** | **2,408** | **+$44.97** | **+$6,477.00** | **10 / 10** | **79.7%** | **77.3%** | **YES** | **YES** | **QUALIFIED FOR PILOT** |
| **Terminal** | 160 | +$44.45 | +$122.00 | 10 / 10 | 100.0% | 38.8% | YES | YES | SECONDARY / LATE-GAME ONLY |
| **Route/spatial** | 31,804 | -$18.85 | +$17,753.00 | 10 / 10 | 79.8% | 62.1% | YES | YES | ELIMINATED (NET NEGATIVE) |
| **Worker allocation** | 1,376 | -$35.96 | +$6,487.00 | 10 / 10 | 76.2% | 70.2% | YES | YES | ELIMINATED (NET NEGATIVE) |
| **Market timing** | 58 | -$60.03 | $0.00 | 0 / 10 | 65.5% | 65.5% | YES | YES | ELIMINATED (NO HEADROOM) |
| **Production timing** | 0 | $0.00 | $0.00 | 0 / 10 | N/A | N/A | YES | YES | NO ACTIVATION (V3 SATURATES) |
| **Liquidity/capital timing** | 0 | $0.00 | $0.00 | 0 / 10 | N/A | N/A | YES | YES | NO ACTIVATION (V3 DISCRETION) |
| **Opponent interaction** | 0 | $0.00 | $0.00 | 0 / 10 | N/A | N/A | YES | YES | NO ORTHOGONAL SIGNAL |
| *Tranche (Quarantined Control)* | 5,364 | -$74.20 | +$140.00 | 3 / 10 | 33.2% | 35.1% | NO | YES | PERMANENT QUARANTINE |

---

## 2. Frequency × Magnitude Matrix (§23)

```text
               High Magnitude (Mean Delta > +$20)
                       │
       [EMPTY]         │    ★ Multi-worker Synchronization
                       │      (Freq: 2,408 | Mean: +$44.97 | Max: +$6,477)
                       │
                       │      Terminal Timing (Late Game)
                       │      (Freq: 160 | Mean: +$44.45 | Max: +$122)
───────────────────────┼─────────────────────────────────────────────
                       │
       Market Timing   │      Route / Spatial Detours
       (Freq: 58)      │      (Freq: 31,804 | Mean: -$18.85)
                       │
                       │      Worker Allocation (Task Swaps)
                       │      (Freq: 1,376 | Mean: -$35.96)
                       │
                Low Magnitude (Mean Delta <= $0)
      Low Frequency (<500)       High Frequency (>=500)
```

### Strategic Implications:
1. **Multi-Worker Synchronization is in the Ideal Quadrant**:
   It demonstrates both **high frequency** (2,408 probes across all seeds) and **high economic magnitude** (+44.97 mean delta).
2. **Route/Spatial and Worker Allocation are High Frequency / Negative Magnitude**:
   Generating arbitrary detours or ad-hoc task swaps produces negative expected value. They destroy tight V3 spatial efficiency.
3. **Market Timing is Low Frequency / Negative Magnitude**:
   Attempting to reorder transactions or advance purchases without selling inventory provides zero economic advantage.

---

## 3. Decision Verdict (§34, §36)

Per Phase 020 Rule §34:
> *"First implementation: exactly ONE new opportunity family. No combinations. No 'all surviving opportunities.' This preserves causal attribution."*

**Selected Family for Implementation & Pilot**:
`MULTIWORKER_SYNCHRONIZATION` (Multi-Worker Harvest Synchronization).
All other families are set aside or eliminated.
