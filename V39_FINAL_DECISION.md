# V39 Final Research & Governance Decision

## 1. Decision State

```text
================================================================================
FINAL DECISION: V39_PROMOTION_CANDIDATE (RESEARCH QUALIFIED / SUBMISSION QUARANTINED)
================================================================================
ACTIVE PRODUCTION STATE: V35 REMAINS LIVE ON KAGGLE (SUBMISSION ID: 56540535)
================================================================================
```

---

## 2. Gate Verification Audit (Phase 26 Compliance)

| Gate # | Promotion Criterion | Target Requirement | Measured V39 Value | Status |
| :---: | :--- | :--- | :---: | :---: |
| **G1** | **Live-Derived Mechanism** | Repeated across live losses | 100% of analyzed live losses | **PASSED** |
| **G2** | **Legal Observability** | No private/future/seed leakage | Step & Shed inventory only | **PASSED** |
| **G3** | **Exact Counterfactuals** | Deficit reduction on exact replay | Rescued up to +$631/game | **PASSED** |
| **G4** | **Generalization** | Safe seeds outside holdout | 10 Seeds (5 Dev + 5 Fresh) | **PASSED** |
| **G5** | **Preserve V35 Wins** | $\ge 99\%$ baseline wins intact | **100.0%** (108 / 108 preserved) | **PASSED** |
| **G6** | **Zero Casualties** | Casualties $\le 0$ | **0 Casualties** (0.0%) | **PASSED** |
| **G7** | **Runtime Safety** | Execution time delta $< 5$ ms | **$< 0.1$ ms** per step | **PASSED** |
| **G8** | **Cleanroom Execution** | Standalone runner compliance | 100% pass | **PASSED** |
| **G9** | **Adversarial Resilience** | No negative trigger corner cases | Audited in `V39_ADVERSARIAL_TEST.md` | **PASSED** |
| **G10**| **Paired Superiority vs V35** | Direct H2H win rate $> 50\%$ | **20W / 0L / 0T (100.0%)**, Margin +$491.70 | **PASSED** |

---

## 3. Quantitative Summary

### Direct Head-to-Head: V39 vs V35
* **Matches**: 20 (10 Seeds $\times$ 2 Seats)
* **V39 Record**: **20 Wins, 0 Losses, 0 Ties (100.0% Win Rate)**
* **Mean Margin**: **+$491.70**
* **Statistical Significance**: $p = 9.54 \times 10^{-7}$ (Exact Binomial Test)

### Paired League Tournament (100 Matches)
* **V35 Baseline Wins**: 97 / 100 (97.0%)
* **V39 Candidate Wins**: **98 / 100 (98.0%)**
* **Rescues**: **1** (`E2_A7` Seed 249679 Seat 0, flipped from Loss to Win)
* **Casualties**: **0** (Zero V35 wins compromised)
* **Mean Paired Cash Delta**: **+$67.59**
* **95% Bootstrap Confidence Interval**: **[+$43.02, $+92.10]** (strictly positive)

### Live Replay Counterfactual Gauntlet (17 Matches)
* **Target Losses Researched**: 6
* **Deficit Recovery**: +$631 on Ep 113183263 (Yassine Chritt), +$604 on Ep 113164394, +$569 on Ep 113153701
* **Narrow Wins Preserved**: 11 / 11 (100.0%)
* **Live Replay Casualties**: 0

---

## 4. Governance & Deployment Invariants

1. **V35 Remains Untouched**:
   - Production candidate `candidates/v35_a7_opening/main.py` remains completely frozen (SHA-256 `1959021bdb1aeff720732aec866f5c9f3c9fa0b259ee0ab25982bda367593249`).
2. **Untouched Reference Standards**:
   - A7 standalone (`candidates/v30_a7_standalone/main.py`) remains frozen.
   - V22R1 (`submission_aec_v22r1.tar.gz`) remains frozen.
3. **Quarantined Holdout Security**:
   - Quarantined seed ranges (`214200–214249`, `340090–340199`, `249695–249734`) were strictly untouched throughout all research phases.
4. **Zero-Submission Mandate Enforced**:
   - No competition submissions were created or executed.
   - Live state remains: **`V35 LIVE / V39 RESEARCH ONLY`**.
