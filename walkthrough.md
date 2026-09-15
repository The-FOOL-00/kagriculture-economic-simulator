# Walkthrough: Championship Experiment — Residual Candidate Independent Replication Audit

We have completed the independent forensic replication audit for the residual championship candidate:
[`candidates/v54_plus_residual.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/v54_plus_residual.py)

---

## 1. Executive Summary & Verdict

### **GO — residual candidate independently validated**

The candidate was evaluated on a **1,000-match symmetric holdout across 500 completely untouched seeds (940,001–940,500)**. Every gate condition of the championship protocol passed unconditionally.

---

## 2. Key Empirical Findings

### Primary Success Test (Candidate vs Frozen V54++)
- **Mean Paired Delta**: **+$111.27**
- **95% Bootstrap CI**: **[+$98.12, +$124.78]** (strictly positive)
- **Win / Loss / Tie Record**: **407 Wins / 31 Losses / 62 Ties (81.4% Win Rate)**
- **Statistical Significance**: 
  - Paired $t$-test: $t = 16.424, p = 8.97 \times 10^{-49}$
  - Wilcoxon signed-rank: $W = 3951.5, p = 3.33 \times 10^{-62}$
- **Distribution Quantiles**: $p_{05} = -\$9.05$, $p_{25} = +\$6.75$, $p_{50} = +\$71.00$, $p_{75} = +\$149.00$, $p_{95} = +\$422.10$

### Secondary Competitive Benchmarks (1,000 Matches Each)
- **Candidate vs Canonical V66**: **+$1,402.31** margin ($95\%\text{ CI } [+\$804.49, +\$2,044.95]$)
- **V54++ vs Canonical V66 (Control)**: **+$1,344.63** margin ($95\%\text{ CI } [+\$745.59, +\$1,988.27]$)
  - Candidate outperforms V54++ by **+$57.68** net margin against V66.
- **Candidate vs Canonical V54**: **+$6,714.96** margin ($95\%\text{ CI } [+\$5,835.89, +\$7,613.11]$, 499W / 1L / 0T)

### Tail-Risk Assessment
- $P(\Delta < -\$100) = 1.2\%$
- $P(\Delta < -\$250) = 0.0\%$
- $P(\Delta < -\$500) = 0.0\%$
- $P(\Delta < -\$1000) = 0.0\%$
- $P(\Delta > +\$100) = 39.4\%$
- $P(\Delta > +\$250) = 13.2\%$
- Worst observed single-match loss across 500 seeds: **-$227.00**

---

## 3. Structural & Architectural Invariants

- **Macro Route Prior Divergence**: **0 / 72,000 turns (0.000%)**
- **Shop Route Divergence**: **0 / 72,000 turns (0.000%)**
- **Solo Parity (50 seeds vs IDLE)**: **$153,728.32 vs $153,728.32 ($\Delta = \$0.00$)**
- **Deterministic Match Checksum**: Two independent 50-seed execution passes yielded identical SHA256 checksums (`cd1f8cf30d4fa0d88f9ee56f9f1c557cadade9842bdf371882cda988aae0d673`).

---

## 4. Generated Artifacts & Reports

| Deliverable | Purpose |
| :--- | :--- |
| [`research/championship_residual_validation.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/championship_residual_validation.md) | Full 18-section championship audit report |
| [`research/residual_parameter_provenance.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/residual_parameter_provenance.md) | Audit proving parameter discovery was un-snooped |
| [`research/v54pp_v66_reconciliation.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/v54pp_v66_reconciliation.md) | Reconciliation of historical benchmark margins |
| [`research/residual_candidate_diff.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/residual_candidate_diff.md) | Semantic diff showing exactly 3 residual parameter modifications |
| [`research/residual_clean_discovery_grid.json`](file:///c:/Users/Sundareswaran/Kagriculture/research/residual_clean_discovery_grid.json) | 500-seed clean pre-registered discovery grid results |
| [`research/residual_true_untouched_holdout_results.json`](file:///c:/Users/Sundareswaran/Kagriculture/research/residual_true_untouched_holdout_results.json) | 4,000-match untouched holdout metrics and tail risks |
| [`research/residual_mechanism_and_solo_results.json`](file:///c:/Users/Sundareswaran/Kagriculture/research/residual_mechanism_and_solo_results.json) | Causal accounting, commodity timing, and solo economics |
| [`research/residual_reproduction_check.json`](file:///c:/Users/Sundareswaran/Kagriculture/research/residual_reproduction_check.json) | Independent reproduction determinism verification |

---

## 5. Kaggle Submission Constraint

**ABSOLUTELY NO SUBMISSION HAS BEEN MADE TO KAGGLE.**  
All automated submission mechanisms remain disabled pending human review.
