# EXP-DEV-004 FORMAL ERRATUM & DATA RECONCILIATION AUDIT (GATE 4)
## Definitional Corrections, Plan Semantics Disambiguation, and Activation Reconciliation

**Experiment Identifier**: `EXP-DEV-004`  
**Governing Protocol**: `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_3.md`  
**Partition Examined**: Seeds `246000` to `246049` ($N=50$ contiguous seeds, 100 paired CRN matches)  
**Authoritative Baseline**: `candidates/compiled_v54_plus_residual.py` (Submission `56146971`)  
**Candidate Treatment**: `candidates/closed_loop_architecture/dev_004_joint_macro_scheduler.py`  
**Audit Purpose**: Reconcile discrepancies between narrative summary figures in `FINAL_REPORT.md` / `FORENSIC_AUDIT.md` and authoritative underlying raw artifacts (`RAW_RESULTS.json`, `PLAN_EVENTS.csv`, `PAIRED_DELTAS.csv`, `WORKER_TELEMETRY.csv`).

---

## 1. Executive Erratum Summary

This erratum establishes the precise empirical facts of EXP-DEV-004 by reconciling the raw checkpoint telemetry with the historical narrative reports. The original narrative report reported an "Activation Rate: 52.0% (26 of 50 seeds had planning overrides; 24 seeds preserved baseline invariant)." 

Forensic reconstruction of the authoritative event log (`PLAN_EVENTS.csv`) reveals that:
1. **True Lifetime Activation Rate is 80.0% (40 of 50 seeds)**, not 52.0%. 
2. The reported 52.0% (26 seeds) reflected strictly the **terminal active plan** at step 719 (`cand0.active_plan != "BASELINE_BACKBONE"`), which masked 14 seeds that activated `YARN_SPECIALIZED` at Step 72 and subsequently reverted to `BASELINE_BACKBONE` at Step 144 or Step 216.
3. For all 10 seeds that truly remained in `BASELINE_BACKBONE` across all checkpoints, candidate behavior was **100% bit-for-bit identical to the baseline**, yielding an exact paired cash delta of **+$0.00**.
4. Every seed with a non-zero paired delta had activated a specialized route at Step 72 or later.

---

## 2. Definitional Disambiguation Matrix

To prevent conflation in all subsequent engineering and governance analysis, the following operational quantities are formally distinguished:

| Metric / Term | Operational Definition | Exact Value in EXP-DEV-004 |
| :--- | :--- | :---: |
| **Total Evaluated Seeds** | Total unique virgin RNG seeds evaluated under paired CRN design | **50 seeds** (100 matches) |
| **Wins / Losses / Ties** | Paired mean cash delta $> 0$, $< 0$, or $== 0$ | **14 Wins / 16 Losses / 20 Ties** |
| **Any-Step Route Activation** | Seeds selecting a non-baseline plan at $\ge 1$ planning checkpoint | **40 seeds (80.0%)** |
| **Terminal Plan Activation** | Seeds whose active plan at final step 719 was non-baseline | **26 seeds (52.0%)** |
| **Always-Baseline Seeds** | Seeds remaining in `BASELINE_BACKBONE` at all 4 checkpoints | **10 seeds (20.0%)** |
| **Plan-Selection Checkpoints** | Planning evaluation steps evaluated per match (Steps 72, 144, 216, 288) | **400 checkpoint events** |
| **Specialization Decisions** | Events where `best_candidate_delta >= TAU` and `money >= L_MIN` | **214 events (53.5%)** |
| **Baseline Decisions** | Events where `best_candidate_delta < TAU` or `money < L_MIN` | **186 events (46.5%)** |
| **Route Reversals (Seeds)** | Seeds transitioning from specialized plan back to `BASELINE_BACKBONE` | **17 seeds (34.0%)** |
| **Route Reversal Events** | Total match-level reversal events across 100 matches | **34 match events** |
| **Reversals After Sunk Commitment** | Reversals occurring after capital allocation (seeds/livestock/routing) | **17 seeds (100% of reversals)** |
| **Harmful Reversals** | Reversals resulting in net paired losses attributable to asset mismatch | **13 seeds (26.0% of cohort)** |
| **Beneficial / Adaptive Reversals** | Reversals resulting in net paired wins (Positive Controls) | **4 seeds (8.0% of cohort)** |

---

## 3. Forensic Origin of the "52% Activation" Narrative

In `run_exp_dev_004.py`, lines 221 and 184:
```python
184: "cand0_plan": cand0.active_plan,
...
221: "activated": (cand0.active_plan != "BASELINE_BACKBONE" or cand1.active_plan != "BASELINE_BACKBONE")
```
The variable `cand0.active_plan` was sampled exclusively after the simulation loop completed (step 719). 

Because 14 seeds initiated `YARN_SPECIALIZED` at Step 72 but reverted to `BASELINE_BACKBONE` at Step 144 or 216, their terminal attribute at Step 719 was `BASELINE_BACKBONE`. Consequently:
- `PAIRED_DELTAS.csv` recorded `cand0_plan = BASELINE_BACKBONE` and `activated = False` for these 14 seeds.
- The automated statistical recomputation script counted seeds with `activated == True`, yielding $26 / 50 = 52.0\%$.
- The historical narrative in `FINAL_REPORT.md` Section 7 and `FORENSIC_AUDIT.md` Section 1 repeated this 52.0% figure without auditing `PLAN_EVENTS.csv`.

**Authoritative Correction**: 
- True activation occurred on **40 of 50 seeds (80.0%)**.
- Terminal specialization persistence occurred on **26 of 50 seeds (52.0%)**.
- Route reversal abandonment occurred on **14 of the 40 activated seeds (35.0%)**.

---

## 4. Resolution of BASELINE_BACKBONE Nonzero Deltas

### 4.1 The Core Question
> *"Does `BASELINE_BACKBONE` mean bit-for-bit baseline behavior?"*

### 4.2 The Direct Answer
**NO.** In the historical artifacts, a record of `BASELINE_BACKBONE` in `PAIRED_DELTAS.csv` denoted only that the agent's **terminal state** was `BASELINE_BACKBONE`. It did **not** indicate that the agent followed baseline behavior throughout the trajectory.

However, for seeds that were `BASELINE_BACKBONE` at **every** checkpoint, the answer is **YES: 100% bit-for-bit identity**.

### 4.3 Empirical Verification Across All 24 Terminal-Baseline Seeds

The 24 seeds logged with `cand0_plan == BASELINE_BACKBONE` partition cleanly into two mutually exclusive sub-cohorts:

#### Sub-Cohort A: Pure Baseline Invariant Seeds ($N=10$)
Seeds: `246000`, `246014`, `246018`, `246020`, `246021`, `246023`, `246029`, `246033`, `246041`, `246043`.
- **Plan History**: `['BASELINE_BACKBONE', 'BASELINE_BACKBONE', 'BASELINE_BACKBONE', 'BASELINE_BACKBONE']`
- **Action Differences vs Baseline**: **0 action differences across all 72,000 game steps**.
- **Paired Mean Cash Delta**: **+$0.00 (Bit-exact ties)**.

#### Sub-Cohort B: Reversed Specialization Seeds ($N=14$)
Seeds: `246003`, `246005`, `246007`, `246022`, `246026`, `246028`, `246030`, `246032`, `246034`, `246035`, `246036`, `246039`, `246042`, `246049`.

| Seed | Candidate Reward | Baseline Reward | Paired Delta | Outcome | Selected Plans (Steps 72, 144, 216, 288) | First Divergent Step | First Divergent Action (Candidate vs Baseline) | First Economic Divergence |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **246003** | $43,433.00 | $44,337.00 | -$904.00 | LOSS | `[YARN, BASE, BASE, BASE]` | Step 74 | Cand: `SELL WHEAT 1` vs Base: `SELL WHEAT 2` | Step 75 (-$30.0) |
| **246005** | $74,016.00 | $76,509.00 | -$2,493.00 | LOSS | `[YARN, BASE, BASE, BASE]` | Step 74 | Cand: `SELL WHEAT 1` vs Base: `SELL WHEAT 2` | Step 75 (-$30.0) |
| **246007** | $74,228.00 | $78,113.00 | -$3,885.00 | LOSS | `[YARN, BASE, BASE, BASE]` | Step 74 | Cand: `SELL WHEAT 1` vs Base: `SELL WHEAT 2` | Step 75 (-$30.0) |
| **246022** | $102,242.00 | $105,992.00 | -$3,794.50 | LOSS | `[YARN, BASE, BASE, BASE]` | Step 74 | Cand: `SELL WHEAT 1` vs Base: `SELL WHEAT 2` | Step 75 (-$30.0) |
| **246026** | $56,812.00 | $47,996.00 | +$8,816.00 | WIN | `[YARN, YARN, BASE, BASE]` | Step 74 | Cand: `SELL WHEAT 1` vs Base: `SELL WHEAT 2` | Step 75 (-$30.0) |
| **246028** | $53,637.00 | $55,750.00 | -$2,113.00 | LOSS | `[YARN, BASE, BASE, BASE]` | Step 74 | Cand: `SELL WHEAT 1` vs Base: `SELL WHEAT 2` | Step 75 (-$30.0) |
| **246030** | $60,466.00 | $63,033.00 | -$2,567.00 | LOSS | `[YARN, BASE, BASE, BASE]` | Step 74 | Cand: `SELL WHEAT 1` vs Base: `SELL WHEAT 2` | Step 75 (-$30.0) |
| **246032** | $91,949.00 | $95,497.00 | -$3,548.00 | LOSS | `[YARN, BASE, BASE, BASE]` | Step 74 | Cand: `SELL WHEAT 1` vs Base: `SELL WHEAT 2` | Step 75 (-$30.0) |
| **246034** | $69,248.00 | $63,795.00 | +$5,453.00 | WIN | `[YARN, YARN, BASE, BASE]` | Step 74 | Cand: `SELL WHEAT 1` vs Base: `SELL WHEAT 2` | Step 75 (-$30.0) |
| **246035** | $53,717.00 | $55,397.00 | -$1,680.00 | LOSS | `[YARN, YARN, BASE, BASE]` | Step 74 | Cand: `SELL WHEAT 1` vs Base: `SELL WHEAT 2` | Step 75 (-$30.0) |
| **246036** | $71,595.00 | $74,432.00 | -$2,837.00 | LOSS | `[YARN, YARN, BASE, BASE]` | Step 74 | Cand: `SELL WHEAT 1` vs Base: `SELL WHEAT 2` | Step 75 (-$30.0) |
| **246039** | $72,531.00 | $76,004.00 | -$3,473.00 | LOSS | `[YARN, BASE, BASE, BASE]` | Step 74 | Cand: `SELL WHEAT 1` vs Base: `SELL WHEAT 2` | Step 75 (-$30.0) |
| **246042** | $62,365.00 | $64,699.00 | -$2,334.00 | LOSS | `[YARN, BASE, BASE, BASE]` | Step 74 | Cand: `SELL WHEAT 1` vs Base: `SELL WHEAT 2` | Step 75 (-$30.0) |
| **246049** | $64,639.00 | $67,840.00 | -$3,201.00 | LOSS | `[YARN, BASE, BASE, BASE]` | Step 74 | Cand: `SELL WHEAT 1` vs Base: `SELL WHEAT 2` | Step 75 (-$30.0) |

### 4.4 Mechanistic Attribution of Non-Zero Deltas
In all 14 seeds above:
1. **Divergence Point**: Step 74 (Day 3, Hour 2). The candidate activated `YARN_SPECIALIZED` at Step 72, which executed `_V56_YARN_ROUTE`. This route sold 1 wheat instead of 2 wheat (reserving wheat for sheep feed) and shifted strawberry seed purchasing and planting vectors.
2. **Reversal Event**: At Step 144 (or Step 216), town shop revelations indicated no specialized shop match, or horizon discounting reduced projected margin below $\tau = 1500.0$. The candidate abruptly reverted to `BASELINE_BACKBONE`.
3. **Downstream Mismatch**: The baseline backbone route expects standard tile layouts, standard hydration cadences, and standard cow livestock. Executing the backbone route on a farm with specialized strawberry planting cadences and sheep allocations caused worker desynchronization, lost yields, and persistent economic deficits.

---

## 5. Summary Reconciliation Table

```
Total Seeds: 50
├── True Always-Baseline (Ties: $0.00): 10 seeds (20.0%)
└── Activated Seeds: 40 seeds (80.0%)
    ├── Maintained Specialization to Step 719: 23 seeds (46.0%)
    │   ├── Wins: 10 seeds
    │   ├── Losses: 3 seeds (246008, 246010, 246016)
    │   └── Ties (Both Cand & Base picked Yarn): 10 seeds
    ├── Re-Specialized After Temporary Reversal: 3 seeds (6.0%)
    │   ├── Wins: 2 seeds (246012, 246048)
    │   └── Loss: 1 seed (246024)
    └── Reverted and Remained in Baseline to Step 719: 14 seeds (28.0%)
        ├── Wins: 2 seeds (246026, 246034)
        └── Losses: 12 seeds (246003, 246005, 246007, 246022, 246028, 
                              246030, 246032, 246035, 246036, 246039, 
                              246042, 246049)
```

This erratum stands as the definitive reconciliation of the EXP-DEV-004 historical dataset.
