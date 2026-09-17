# EXP-AEC-003 Final Freeze Certification: Causal Dependency-Aware Market Timing

**Certification Identifier:** `CERT-FREEZE-EXP-AEC-003-20260917`  
**Date Established:** 2026-09-17  
**Auditor / Authority:** Antigravity Autonomous Scientific Reviewer & AEC Governance Covenant  
**Protocol Target:** `PREREG-EXP-AEC-003-20260917-FINAL`  

---

## 1. Immutable State & Core Certification Directives

```
================================================================================
STATUS:
READY_FOR_IMMUTABLE_FREEZE

EXECUTION:
FROZEN_NOT_LAUNCHED

COHORT:
340250–340299

HOLDOUT:
340050–340199

PRIMARY HYPOTHESIS:
H0 μΔ < 0
H1 μΔ ≥ 0

PRIMARY TEST:
One-sided paired t-test

PRIMARY ACCEPTANCE:
Lower 95% CI >= 0
AND win-rate delta >= -2 pp

TREATMENT:
DEPENDENCY_AWARE_MARKET_TIMING

CONTROL:
Frozen V3

COUNTERFACTUAL FIDELITY:
VERIFIED required for commit

PROSPECTIVE EXECUTION:
ZERO
================================================================================
```

---

## 2. Statistical Specification Audit & Consistency Certification

### 2.1 Primary Hypothesis Formulation
- **Null Hypothesis ($H_0$):**
  $$H_0: \mu_\Delta < \$0.00$$
- **Alternative / Primary Hypothesis ($H_1$):**
  $$H_1: \mu_\Delta \ge \$0.00$$
  where $\mu_\Delta$ denotes the true population mean paired terminal-margin delta between Treatment and Control.
- **Primary Inferential Test:**
  - One-sided paired $t$-test on seed-paired terminal margin deltas $\Delta_s$.
  - Significance level: $\alpha = 0.05$.
  - Degrees of freedom: $df = N - 1 = 49$ ($N = 50$ paired seeds).

### 2.2 Strict Separation of Acceptance Criteria
Operational acceptance criteria are kept strictly separated from hypothesis definitions (the confidence bound is NOT written as part of $H_0$):
- **Criterion 1 (Lower Confidence Bound):**
  $$\text{Lower 95\% CI}(\mu_\Delta) \ge \$0.00$$
- **Criterion 2 (Win-Rate Non-Inferiority):**
  $$\Delta \text{WinRate} \ge -2.0\text{ percentage points}$$
Both criteria must be satisfied simultaneously for primary acceptance.

### 2.3 Secondary Robustness Analyses (Preregistered & Unchanged)
- **Non-Parametric Analysis:** Two-sided Wilcoxon signed-rank test on paired deltas $\Delta_s$.
- **Confidence Intervals:** One-sided lower 95% Student-$t$ bound and two-sided 90% Student-$t$ CI for $\mu_\Delta$.
- **Bootstrap Procedure:** 95% BCa bootstrap confidence interval for $\mu_\Delta$ ($10,000$ paired resamples).
- **Win-Rate Definitions:**
  - Primary Standard: $\Delta \text{WinRate} = \frac{W_{\text{treat}} - W_{\text{ctrl}}}{M} \times 100\text{ pp}$ across all $M = 100$ matches.
  - Secondary Robustness Standard: Ties excluded from denominator.
- **Zero Post-Hoc Tests:** No post-hoc tests or altered thresholds are permitted.

### 2.4 Audited Power & Sensitivity Analysis
- **Design Parameters:** $N = 50$ paired seeds, $M = 100$ mirror CRN matches, $df = 49$, historical $s_\Delta \approx \$4.80$ ($\text{SE} \approx \$0.6788$).
- **Critical Rejection Boundary (50% Power):**
  $$\overline{\Delta}_{\text{crit}} = t_{0.05, 49} \times \text{SE} \approx 1.6766 \times \$0.6788 \approx +\$1.14$$
  An observed sample mean $\overline{\Delta} \ge +\$1.14$ rejects $H_0$ and achieves Lower 95% CI $\ge \$0.00$. At $\mu_\Delta = +\$1.14$, statistical power to reject $H_0$ is exactly 50.1%.
- **Prospective Power Benchmarks:**
  - **80% Power ($\beta = 0.20$):** Detects true population effect size $\mu_\Delta \ge +\$1.71$ (Cohen's $d_z \approx 0.357$, small-to-medium effect).
  - **90% Power ($\beta = 0.10$):** Detects true population effect size $\mu_\Delta \ge +\$2.02$ (Cohen's $d_z \approx 0.421$).
- **Type I Error Protection:** Exact 5% false-positive rate control under $H_0$ ($\mu_\Delta < \$0.00$).

### 2.5 Dormancy Rule Interpretation
- **Rule:** $\text{Commits} < 5 \implies \text{DORMANT / INCONCLUSIVE}$.
- **Governance Role:** The dormancy rule is an **interpretation gate**, not an efficacy threshold. It ensures that trials with insufficient opportunity encounters are not erroneously classified as active positive or non-inferior. It must never be used to post-hoc filter or manufacture statistical significance.

---

## 3. Experimental Architecture & Seed Separation

### 3.1 Partition Map & Isolation Covenant
```
[340000 ----------- 340049] [340050 ----------- 340199] [340200 ----------- 340249] [340250 ----------- 340299]
    EXP-AEC-001 (HISTORICAL)      AEC LOCKED HOLDOUT (150)     EXP-AEC-002 (HISTORICAL)     EXP-AEC-003 (PROSPECTIVE)
      PERMANENTLY CONSUMED           STRICTLY TOUCHLESS          PERMANENTLY CONSUMED         PROPOSED VIRGIN COHORT
```
- **Holdout (`340050–340199`):** 150 seeds strictly quarantined. Zero simulations, zero inspections, zero tuning runs. Distance to cohort start: 51 seeds.
- **Prospective Cohort (`340250–340299`):** 50 seeds certified 100% virgin in `reports/EXP_AEC_003_COHORT_AUDIT.md`. Total matches executed: 0.

### 3.2 Treatment & Mechanism Isolation
- **Active Experimental Mechanism:** `DEPENDENCY_AWARE_MARKET_TIMING`
- **Defense Infrastructure:** `TERMINAL_LIQUIDATION`, `PHASE_SHUTDOWN`
- **Quarantined Mechanisms (100% Inactive):** `FRONTLOAD_ORDERS` (RETIRED / FALSIFIED), `LOCAL_WEED_DIG`, `DYNAMIC_SHADOW_HARVEST`, `CARGO_FERRY_PRIORITY`, `OPPONENT_PREEMPT_SELL`, `EMERGENCY_FEED_PURCHASE`, `TERMINAL_HARVEST_SWEEP`, `TOWN_CYCLE`.
- **Precondition Gate:** `COUNTERFACTUAL_FIDELITY: VERIFIED` required for commit; `FAILED` and `UNKNOWN` strictly rejected.

---

## 4. Verification Hashes (SHA-256)

| Component | File Path | Status |
|---|---|---|
| **V3 Backbone Tarball** | `submission_Vj_kc_v3.tar.gz` | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` |
| **Preregistration Final** | `reports/EXP_AEC_003_PREREGISTRATION_FINAL.md` | `4332e8577f47eff0f045477864ee182c1ab16181e591228748d9d9a8630c3fe1` |
| **Cohort Audit** | `reports/EXP_AEC_003_COHORT_AUDIT.md` | `14f9a1f3937a32e85c5207dbb839fab8de8f83148038283d84877b0889b5255a` |
| **Prelaunch Audit** | `reports/EXP_AEC_003_PRELAUNCH_AUDIT.md` | `f36148c4cb955f9e7d64d4298cf1f32e1518e67a3648de523cd1486a79845fd3` |
| **Execution Manifest** | `experiments/EXP-AEC-003/EXECUTION_MANIFEST.json` | `4330e12374a9854ad989d9f92e287b147b789b11d8a49182215f3bce3ede426f` |
| **AEC Configuration** | `aec/config.py` | `a92bb57785535d0c5b51895d5242fbf5a33f4a09c89b8160e8424bf245d63d55` |

---

## 5. Formal Halting Directive

**EXP-AEC-003 IS FROZEN_NOT_LAUNCHED AND AWAITS EXPLICIT EXECUTION AUTHORIZATION.**

Under strict scientific governance, all code, configuration, tests, manifests, and audits are permanently frozen. No prospective seed may be run until explicit user execution authorization is provided.
