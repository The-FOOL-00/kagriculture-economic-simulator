# DEVELOPMENT HOLDOUT REGISTRY

## Centralized Official Registry of Certified Virgin Holdout Partitions

**Governing Standard**: Section 8 Holdout Protection Covenant & Anti-Contamination Rules  
**Registry Version**: 1.0 (Post-Gate 0.3 Certification)  
**Date Established**: 2026-09-11  
**Status**: **ACTIVE & IMMUTABLE**  

---

## 1. Registry Covenant & Protection Invariants

Under Section 8 of the Development Gate Protocol:
> *"Once certified, this partition must never be used for:*
> - *exploration*
> - *tuning*
> - *debugging*
> - *model selection*
> *It is reserved for final confirmation only."*

### Absolute Invariants:
1. **Never Accessed in Development**: Scripts implementing `EXP-DEV-001` through `EXP-DEV-005` are strictly prohibited from referencing, loading, or simulating the registered holdout partition during hypothesis generation or parameter qualification.
2. **Confirmatory Qualification Only**: A candidate agent may only be evaluated on the registered holdout partition after its source code, hyper-parameters, and execution tape have been frozen and certified under Git commit.
3. **No Retuning on Failure**: If a frozen candidate fails on the holdout partition, the candidate is marked `FAILED`. Modifying the candidate and re-evaluating on the same holdout is strictly prohibited.

---

## 2. Certified Partition Specification: Cohort 1

| Registry Field | Official Record |
| :--- | :--- |
| **Partition Identifier** | `HOLDOUT-COHORT-V1` |
| **Designation Date** | 2026-09-11 |
| **Seed Range** | `214200` to `214249` (Inclusive) |
| **Sample Size ($N$)** | **50 Seeds** (100 paired Common Random Number matches) |
| **Exact Seed IDs** | `[214200, 214201, 214202, 214203, 214204, 214205, 214206, 214207, 214208, 214209, 214210, 214211, 214212, 214213, 214214, 214215, 214216, 214217, 214218, 214219, 214220, 214221, 214222, 214223, 214224, 214225, 214226, 214227, 214228, 214229, 214230, 214231, 214232, 214233, 214234, 214235, 214236, 214237, 214238, 214239, 214240, 214241, 214242, 214243, 214244, 214245, 214246, 214247, 214248, 214249]` |
| **Provenance Audit Document** | [`DEVELOPMENT_GATE_0_3_HOLDOUT_PROVENANCE.md`](file:///c:/Users/Sundareswaran/Kagriculture/DEVELOPMENT_GATE_0_3_HOLDOUT_PROVENANCE.md) |
| **Provenance Audit SHA256** | `8f0cc52e6ce16ed0accfc0a134d21f7e18450bc093d01d269e41ff05a397af0f` |
| **Evidence Search Scope** | Entire workspace and Git history: `.py`, `.json`, `.csv`, `.md`, `.txt`, `.log`, `.yaml`, `.yml`, replay files, generated datasets, loops, and manifests |
| **Contamination Result** | **0 / 50 seeds contaminated (100% Verified Virgin)** |
| **Simulator Compatibility** | 100% of seeds execute 719 steps, unlocking 8 shops across 41 unique opening pairs |

---

## 3. Disqualified Historical Cohorts (Permanently Retired)

The following seed ranges are formally recorded as contaminated and must never be designated as holdouts:
1. **Seeds 50150–50199**: Contaminated by `scratch/test_phase16_generalization.py` (Seeds 50155, 50161), live tournament match `107564294` (Seed 50186), and Phase 3 macro census (`results/phase3_shop_census_500seeds.json`).
2. **Seeds 60000–60049**: Contaminated by `parameter_and_lookahead_sweeps.py` (Seeds 60000–60019) and `evaluate_batch8_predictive_challenger.py` (Seeds 60000–60049).
3. **Seeds 50100–50149**: Retained as an **Audited Benchmark Partition** (evaluated in Audit 2/2.1/2.2); not virgin.

---

## 4. R1 Addendum — Consumed Tournament Cohort (2026-09-20)

**Registry Version**: 1.1 (additive; §§1–3 above unchanged).
**Status**: **CONSUMED / RETIRED HOLDOUT**

4. **Seeds 340300–340349** (inclusive, 50 seeds): consumed by `EXP-AEC-004`
   (Sept 18; 100 CRN mirror matches with real scores and commits;
   `experiments/EXP-AEC-004/`, `results/EXP_AEC_004_MATCHES.csv`,
   `results/EXP_AEC_004_SUMMARY.json`). Falsely re-certified "Virgin /
   Untouched" in Phase 022 documents (`PHASE022_BASELINE_FREEZE.md` §4 and
   dependents); that label is retracted in `PHASE022R1_HOLDOUT_INTEGRITY.md`.
   Permanently retired: never reuse for exploration, tuning, debugging,
   selection, or future qualification. History preserved — this entry corrects
   by re-designation, not by editing the record of what happened.
