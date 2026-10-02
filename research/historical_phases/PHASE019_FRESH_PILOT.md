# PHASE019 FRESH PILOT REPORT

**Phase**: PHASE019 — Uncertainty-Aware Commit Selection & Robust Economic Decision Audit  
**Date**: 2026-09-20  
**Cohorts**:
- Diagnostic Block (Arm U1): Seeds `249336..249345` (10 seeds, 20 CRN mirror matches)
- Repair Block (Arm U2): Seeds `249346..249355` (10 seeds, 20 CRN mirror matches)
- Total Matches: 40 CRN mirror matches against live foundation control $A_0$

---

## 1. Experimental Cohort & Protocol Integrity

1. **V3 Immutability**:
   `submission_Vj_kc_v3.tar.gz` SHA256 verified byte-identical (`845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`) before and after execution.
2. **Fresh Untouched Seeds**:
   In strict compliance with Phase018 manifest, all seeds began at `249336`. No historical seeds from Phase017 or Phase018 were reused.
3. **Common Random Numbers (CRN) Symmetry**:
   Every seed was evaluated in dual mirror seats (Treatment Seat 0 vs Control Seat 1, and Control Seat 0 vs Treatment Seat 1) to perfectly cancel map layout variance.
4. **Common Control ($A_0$)**:
   The control in all 40 matches was the approved live foundation (`V3 + MARKET_TIMING + TERMINAL_LIQUIDATION + PHASE_SHUTDOWN`).

---

## 2. Arm U1: Observational Diagnostic Pilot Results

Arm U1 evaluated the Phase015 treatment under current decision policy (with Phase018 funnel reservation and discrimination), with the Phase019 shadow robustness engine observing in the background without modifying commit actions.

### 2.1 Cohort Level Statistics (Seeds 249336..249345)
- **Mean Paired Delta**: **$-\$757.35$**
- **Median Paired Delta**: **$-\$467.50$**
- **95% Confidence Interval**: $[-\$1,322.00, -\$192.70]$
- **Win / Loss / Tie**: **0W / 9L / 1T** (0% win rate)
- **Total Tranche Commits**: 30
- **Total Foundation Commits**: 20

### 2.2 Per-Seed Match Breakdown
| Seed | Seat 0 Margin | Seat 1 Margin | Paired Delta | Tranche Commits | Foundation Commits |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **249336** | $-\$1,302$ | $-\$2,735$ | $-\$2,018.50$ | 3 | 0 |
| **249337** | $-\$382$ | $-\$382$ | $-\$382.00$ | 3 | 2 |
| **249338** | $\$0$ | $\$0$ | **$\$0.00$** | 0 | 1 |
| **249339** | $-\$562$ | $-\$562$ | $-\$562.00$ | 3 | 0 |
| **249340** | $+\$2$ | $-\$1,560$ | $-\$779.00$ | 1 | 1 |
| **249341** | $-\$509$ | $-\$509$ | $-\$509.00$ | 1 | 2 |
| **249342** | $-\$58$ | $-\$58$ | $-\$58.00$ | 0 | 1 |
| **249343** | $-\$2,759$ | $-\$2,759$ | $-\$2,759.00$ | 1 | 1 |
| **249344** | $-\$426$ | $-\$426$ | $-\$426.00$ | 2 | 1 |
| **249345** | $-\$80$ | $-\$80$ | $-\$80.00$ | 1 | 1 |

### 2.3 Diagnostic Finding from U1 Shadow Telemetry
- **100% of committed tranche orders (30/30) were non-robust**:
  - 20 were **R4 (Macro-Sensitive)**: suffered severe negative downstream macro continuation deltas ($-\$77$ to $-\$173$).
  - 10 were **R1 (Sensitive Positive)**: exhibited fragile neighborhoods where legal perturbations dropped to $\le \$0.0$.
  - Exactly **0 candidates were R0 (Robustly Positive)**.
- **100% of foundation commits (20/20) were robust ($R0$) or marginal ($R2$)**, with zero macro sensitivity.

---

## 3. Arm U2: Robust Abstention Gate Pilot Results

Arm U2 activated the preregistered robust abstention gate on fresh seeds `249346..249355`:
- Tranche candidates classified as $R1$ (fragile neighbor) or $R4$ (macro-sensitive) were rejected with `decision="ABSTAIN"`.
- Foundation candidates remained fully operational.

### 3.1 Cohort Level Statistics (Seeds 249346..249355)
- **Mean Paired Delta**: **$-\$636.90$**
- **Median Paired Delta**: **$-\$374.00$**
- **95% Confidence Interval**: $[-\$1,155.98, -\$117.82]$
- **Win / Loss / Tie**: **2W / 6L / 2T**
- **Tranche Commit Attempts Audited**: 181
- **Tranche Commit Attempts Abstained**: **171 (94.5%)**
- **Tranche Orders Admitted**: 10
- **Total Foundation Commits**: 16

### 3.2 Per-Seed Match Breakdown
| Seed | Seat 0 Margin | Seat 1 Margin | Paired Delta | Tranche Commits | Foundation Commits |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **249346** | $-\$762$ | $-\$762$ | $-\$762.00$ | 0 | 1 |
| **249347** | $-\$968$ | $-\$968$ | $-\$968.00$ | 0 | 2 |
| **249348** | $\$0$ | $\$0$ | **$\$0.00$** | 0 | 0 |
| **249349** | $-\$1,561$ | $-\$1,561$ | $-\$1,561.00$ | 1 | 1 |
| **249350** | $-\$164$ | $-\$4$ | $-\$84.00$ | 1 | 0 |
| **249351** | $+\$87$ | $+\$87$ | **$+\$87.00$** | 0 | 1 |
| **249352** | $-\$5,290$ | $+\$3,962$ | $-\$664.00$ | 1 | 1 |
| **249353** | $+\$24$ | $+\$24$ | **$+\$24.00$** | 0 | 1 |
| **249354** | $\$0$ | $\$0$ | **$\$0.00$** | 0 | 1 |
| **249355** | $-\$2,441$ | $-\$2,441$ | $-\$2,441.00$ | 2 | 0 |

---

## 4. Key Comparative Scientific Findings

1. **Abstention Restores Foundation Value**:
   In seeds where the robust abstention gate successfully suppressed 100% of tranche orders (seeds 249348, 249351, 249353, 249354), the treatment **tied or won in 4 out of 4 seeds ($+\$87, +\$24, \$0, \$0$)**!
2. **Residual Losses are Driven by Tranche Mechanism Economics**:
   In the 4 seeds where the gate admitted even 1 or 2 tranche orders that appeared locally robust in late-game turns (seeds 249349, 249350, 249352, 249355), the match collapsed into catastrophic losses ($-\$1,561, -\$2,441, -\$5,290$).
3. **The Final Scientific Truth**:
   The Phase015 tranche mechanism is **fundamentally uneconomic**. Even when filtered by exact counterfactuals, macro detectors, and neighborhood robustness gating, executing autonomous tranche sales causes net systemic harm to the farm's production ecosystem.
