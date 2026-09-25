# V37 Candidate Freeze Audit: V35 Opening Controller

## 1. Frozen Candidate Verification

- **Source File**: `candidates/v35_a7_opening/main.py`
- **Computed SHA-256**: `1959021bdb1aeff720732aec866f5c9f3c9fa0b259ee0ab25982bda367593249`
- **Expected SHA-256**: `1959021bdb1aeff720732aec866f5c9f3c9fa0b259ee0ab25982bda367593249`
- **Verification Result**: **PASS — BIT-IDENTICAL MATCH**

---

## 2. Source Code Architecture & Invariance

The source code in `candidates/v35_a7_opening/main.py` consists of 88 lines implementing the frozen `V35OpeningController` and `agent` function:

1. **Step-0 Opening Intervention**:
   - Replaces the Step-0 market wash action with `[["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]]`.
   - Leaves all other components (`farmer`, `hands`) intact.
2. **Steps 1..718 Delegation**:
   - 100% bit-identical delegation to the underlying A7 standalone agent (`load_agent("E9_AST")` -> `candidates/v30_a7_standalone/main.py`).
   - Zero behavioral drift ($D(t) \to 0$ downstream).
3. **Fail-Closed Fallback**:
   - Any exception during evaluation falls back safely to A7 base action or `{"farmer": ["PASS"], "hands": [], "market": []}`.

---

## 3. Quarantined & Forbidden Concepts Scan

A complete static analysis of `candidates/v35_a7_opening/main.py` confirmed:

| Feature / Artifact | Present? | Verification Notes |
| :--- | :---: | :--- |
| **Seed Conditioning** | **NO** | No inspection of `observation.get("seed")` or environment configuration seeds. |
| **Opponent Detection / Profiling** | **NO** | No inspection of opponent name, ID, history, or behavior. |
| **Hidden Future State** | **NO** | No forward peeking (only `from __future__ import annotations` stdlib directive). |
| **Outcome Labels / Selector Training** | **NO** | No machine learning classifiers, neural weights, or regression models. |
| **Learned Weights / Checkpoints** | **NO** | Zero weight files, pickle files, or numpy arrays. |
| **Runtime Search / MCTS** | **NO** | Deterministic closed-form rule execution in $< 0.03\text{ ms}$. |
| **Protected Holdout References** | **NO** | Zero mentions of seeds `214200–214249`, `340090–340199`, or `249695–249734`. |

---

## 4. Incumbent Integrity Baseline

At audit start:
- `candidates/v30_a7_standalone/main.py`:
  `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` (EXACT MATCH)
- `submission_aec_v22r1.tar.gz`:
  `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` (EXACT MATCH)

---

## 5. Audit Verdict

**FREEZE INTEGRITY CONFIRMED**. `candidates/v35_a7_opening/main.py` is bit-frozen and clean of all forbidden conditioning, search, or learning mechanisms.
