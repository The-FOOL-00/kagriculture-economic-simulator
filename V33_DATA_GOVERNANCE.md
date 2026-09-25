# V33 Data Governance Protocol

**Program:** Kagriculture V33 Research Program  
**Effective Date:** 2026-09-24  
**Author:** Lead Research Engineer, Competition Scientist, and Implementation Owner  
**Status:** **ACTIVE AND STRICTLY ENFORCED**

---

## 1. Data Partitioning & Cohort Definitions

To ensure strict scientific integrity, prevent memorization, and eliminate information leakage, all simulation, replay, and evaluation data is partitioned into mutually exclusive, strictly governed cohorts:

| Partition | Seed Range / Source | Allowed Purpose | Forbidden Purpose | Status |
| :--- | :--- | :--- | :--- | :---: |
| **TRAIN** | `249635–249674` & Public Replays | Route extraction, clustering, feature learning, initial model fitting | Hyperparameter selection, promotion decisions | OPEN |
| **DEV** | `249675–249694` | Threshold tuning, early stopping, validation, ablation benchmarks | Route extraction, training set augmentation | OPEN |
| **FRESH_DEV** | `249735–249774` | Unseen validation of route portfolio, out-of-sample win rate tests | Model fitting, threshold selection | OPEN |
| **VIRGIN_HOLDOUT 1** | `214200–214249` (Gate 0) | Final single-touch gate verification | Any tuning, inspection, feature extraction | **STRICTLY PROTECTED** |
| **VIRGIN_HOLDOUT 2** | `340090–340199` (Remainder) | Final championship qualification | Any tuning, inspection, feature extraction | **STRICTLY PROTECTED** |
| **VIRGIN_HOLDOUT 3** | `249695–249734` (V32_CONFIRM) | Production freeze regression audit | Any tuning, inspection, feature extraction | **STRICTLY PROTECTED** |

---

## 2. Anti-Leakage Invariants

Any candidate policy, selector, or feature encoder must strictly satisfy the following causal invariants at decision step $t$:

1. **Temporal Causality:**
   $$\forall \mathbf{f}_t \in \mathcal{F}_t, \quad \mathbf{f}_t = g(o_0, a_0, o_1, a_1, \dots, o_t)$$
   No feature $\mathbf{f}_t$ may depend on $o_{t+k}$ or $a_{t+k}$ for $k > 0$.
2. **No Terminal Information:**
   No feature may access `final_reward`, `match_result`, `total_cash`, `terminal_liquidation`, or any metric computed post-game.
3. **No Hidden Opponent Identity:**
   Features must be derived strictly from observable environment state (prices, volumes, visible farm coordinates, public orders). Feeding `opponent_id`, `opponent_name`, `seed_id`, or leaderboard rating into the runtime agent is strictly prohibited.
4. **No Future Market Leakage:**
   Market features must reflect spot prices and visible history at step $t$. Anticipating future shop spawns or future price adjustments before they are visible in $o_t$ is an automatic failure.

---

## 3. Automated Leakage Audit (`replay_leakage_audit.py`)

A mandatory automated audit script runs before any benchmark to verify:
- Complete absence of future observation keys in feature vectors.
- Seed boundary enforcement (raising immediate `RuntimeError` if any seed in `REFUSED` or holdout ranges is requested during training).
- Deterministic reproducibility of features given identical observation prefixes.
- Zero reliance on hidden opponent identity strings.
