# V38 Static and Dynamic Information Leakage Audit

**Document ID:** `V38_LEAKAGE_AUDIT.md`  
**Date:** 2026-09-25  
**Candidate:** `candidates/v38_heuristic_ppo/`  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. Governance and Quarantine Integrity

The V38 codebase was audited against all governance mandates regarding quarantined data and frozen candidates:

### 1.1 Quarantined Seed Ranges
The following seed ranges are strictly prohibited from all evaluation, tuning, training, or benchmarking:
* `214200–214249` (Virgin holdout)
* `340090–340199` (Protected remainder)
* `249695–249734` (V32 confirmation holdout)

**Verification:**
* `config.py` defines `QUARANTINED_SEEDS` and executes `assert_seed_safe(seed)` on every seed passed into any training, rollout, or evaluation loop.
* Grep audit confirmed zero occurrences of quarantined seed integers across all `candidates/v38_heuristic_ppo/` and `scratch/v38/` code.

### 1.2 Frozen Baseline SHA-256 Hashes
* **V35:** `1959021bdb1aeff720732aec866f5c9f3c9fa0b259ee0ab25982bda367593249` (**UNTOUCHED & VERIFIED**)
* **A7:** `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` (**UNTOUCHED & VERIFIED**)
* **V22R1:** `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` (**UNTOUCHED & VERIFIED**)

---

## 2. Observational Leakage Audit (Causal Observability)

To prevent the methodological flaws identified in V33 (such as oracle opponent-ID conditioning and seed lookup tables), V38 enforces strict causal observability:

### 2.1 Opponent State Isolation
* **Opponent Private State:** The policy has zero access to opponent `shed`, `seeds`, or unit `inventories`.
* **Opponent Policy State:** The policy does not inspect `opp_id`, opponent internal variables, or future action tapes.
* **Visible Opponent Attributes:** The state representation extracts only legally visible opponent properties:
  * Public liquid cash (`opp_farm.money`)
  * Publicly visible units (`farmer`, `hands`)
  * Publicly visible tiles on the opponent's farm grid (`opp_farm.tiles`)
  * Publicly visible unlocked quadrants (`opp_farm.unlocked_quadrants`)

### 2.2 Temporal / Future Information Isolation
* **No Future Lookahead at Inference:** During actual gameplay (`main.py` and `act()`), all features are computed strictly from observations $\le t$.
* **Forward Simulator Quarantined to Offline Research:** The `CounterfactualEngine` is used exclusively during offline dataset generation and counterfactual evaluation; it is not called during production `agent()` execution.
* **No Seed-Conditioned Rules:** Decision rules in `macro_options.py` and `heuristic.py` contain zero branches conditioned on `seed` or episode ID.

---

## 3. Audit Certification

| Audit Item | Status | Verified By |
| :--- | :---: | :--- |
| **Quarantined Seed Isolation** | **CERTIFIED ZERO ACCESS** | Hardcoded assertion in `config.assert_seed_safe` |
| **Frozen File Immutability** | **CERTIFIED 100% BIT-IDENTICAL** | SHA-256 cryptographic verification |
| **Opponent Information Isolation** | **CERTIFIED 100% LEGAL** | Observation schema audit in `state_features.py` |
| **Strictly Causal Inference** | **CERTIFIED ZERO LEAKAGE** | Inspection of `candidates/v38_heuristic_ppo/main.py` |
