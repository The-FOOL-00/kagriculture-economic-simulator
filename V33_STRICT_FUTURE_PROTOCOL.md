# V33 Strict-Future Evaluation Protocol & Data Partitioning

**Program:** Kagriculture V33 Research Program  
**Date:** 2026-09-24  
**Objective:** Guarantee complete absence of future leakage, seed memorization, and overfitting across all V33 models and selectors.

---

## 1. Strict Partitioning Architecture

The benchmark and training splits are strictly segregated into four non-overlapping partitions:

### Partition 1: TRAIN (`249670..249674`)
- **Role:** Route feature mining, observation signature extraction, and initial classifier parameter fitting.
- **Access:** Unrestricted during training phases.

### Partition 2: DEV (`249675..249679`)
- **Role:** Route-vs-route tournament, non-transitivity testing, threshold tuning, and counterfactual transition analysis.
- **Access:** Read/evaluate during hyperparameter selection.

### Partition 3: FRESH_DEV (`249680..249694`, 15 seeds)
- **Role:** Out-of-sample validation of the integrated candidate package against the full 6-opponent league.
- **Constraint:** Zero feature selection, zero parameter adjustment, zero threshold tuning.

### Partition 4: VIRGIN_HOLDOUT (Protected)
The following seed ranges remain completely untouchable and protected:
- `214200..214249` (50 seeds)
- `249695..249734` (40 seeds)
- `340090..340199` (110 seeds)
- **Constraint:** NEVER accessed during development. Only touched during final frozen acceptance gating.

---

## 2. Temporal & Causal Hygiene Rules

At every simulation step $t$:
1. **Zero Future Information:**
   - Features may only be computed from observations up to step $t$.
   - Strictly forbidden: accessing terminal cash, future prices, future opponent moves, or post-$t$ state.
2. **Zero Hidden Identifiers:**
   - Deployed selectors must NEVER ingest `seed`, `opponent_id`, `seat_id`, or leaderboard rank.
   - All routing decisions must depend exclusively on physical game observations (market prices, visible worker count, inventory, player cash).
3. **Audit Verification:**
   - All dataset generators and selector pipelines must pass `candidates/v33_meta_strategy/replay_leakage_audit.py` with zero warnings.
