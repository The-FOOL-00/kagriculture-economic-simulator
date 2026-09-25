# V34 Strict-Future Evaluation Protocol & Seed Governance

**Program:** Kagriculture V34 Research Program (A7 Tactical Forward Search)  
**Author:** Lead Research Scientist, Competitive-Programming Engineer, Simulator Engineer, and Implementation Owner  
**Date:** 2026-09-24  
**Scope:** Protocol specification for chronological and partition-isolated evaluation, preventing temporal leakage and seed overfitting.  

---

## 1. Governance Principles & Strict-Future Partitioning

In competitive game theory and reinforcement learning, policy evaluation must respect strict chronological and environment boundaries. In Kaggriculture, seed IDs generate initial shop configurations, market supply elasticities, and land obstacle layouts. Evaluating candidates on the same seeds used for opportunity discovery introduces severe sample memorization.

To ensure true out-of-distribution generalization, V34 establishes a 4-tier strict-future partition:

```
[ Tier 1: Historical Discovery ]   --> Seeds 249635..249674 (V32_TRAIN, 40 seeds)
               |
               v
[ Tier 2: Development Validation ] --> Seeds 249675..249694 (V32_DEV, 20 seeds)
               |
               v
[ Tier 3: Fresh League Benchmark ] --> Fresh Unseen Seeds (e.g. 250000..250020)
               |
               v
[ Tier 4: Virgin Holdouts ]        --> 214200..214249, 340090..340199, 249695..249734 (LOCKED)
```

---

## 2. Partition Rules & Usage Matrix

| Partition Name | Seed Range | Permitted Operations | Prohibited Operations | Governance Status |
| :--- | :---: | :--- | :--- | :---: |
| **Tier 1: Historical** | `249635..249674` | Feature discovery, offline census, opportunity labeling, GBDT training. | Final promotion gating. | **OPEN** |
| **Tier 2: Development** | `249675..249694` | Hyperparameter validation, threshold tuning, candidate filtering. | Re-training models after failure. | **CONTROLLED** |
| **Tier 3: Fresh League** | `250000..250020` | Out-of-distribution paired evaluation, ablation testing, win-rate benchmarking. | Model selection, threshold adjustment. | **SINGLE-PASS** |
| **Tier 4: Virgin Holdouts** | `214200–214249`<br>`340090–340199`<br>`249695–249734` | Final pre-submission verification only (frozen binary). | Any exploratory execution, parameter tuning. | **STRICTLY LOCKED** |

---

## 3. Strict-Future Gating Rules

1. **Chronological Lock:**
   No tactical contract discovered on Tier 1 may adjust its activation threshold or signature based on Tier 2 or Tier 3 outcomes. If a contract fails on Tier 2 or Tier 3, it is classified as `QUARANTINED` or `RETIRED`. It may not be "tweaked" to pass.
2. **Deterministic Reproducibility:**
   All match executions in Tiers 2, 3, and 4 must produce identical rewards across repeated runs with identical random seeds.
3. **No Retrospective Leakage:**
   Features extracted at step $t$ must never access information from steps $t' > t$, nor ground-truth opponent parameters.
4. **Freeze Before Virgin Touch:**
   Before any execution touching virgin holdout partitions (if authorized), code, weights, search parameters, and contracts must be frozen with an immutable SHA-256 commit hash.
