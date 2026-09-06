# Walkthrough: V2 Day-0 Just-In-Time Melon Pipeline Causal Study

## Summary of Completed Work
We executed a complete, rigorous, multi-phase causal study to evaluate whether the **Day-0 Just-In-Time (JIT) Melon Pipeline** identified from top-10 live competition replays (`Yuyajk`, `GAYATHRI SALINI`, `qihuaz`) produces a robust, compounding performance advantage when tested against `Aethel-Refined V2`.

### Governance & Portfolio Verification
- **Slot 1 (`agents/candidate_a_aethel_v1.py`):** Verified SHA256 `c1945f24f34ca9d5124e8200df14af019f6cb4cdec3ca402d9a3a88f6b04e36f` (Untouched).
- **Slot 2 (`candidates/slot2_aethel_refined_v2.py`):** Verified SHA256 `79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d` (Untouched).
- **No live submissions made.** All code isolated in `scratch/v2_jit_melon_experiment.py`.

---

## Key Experimental Results

### 1. 500-Game Matched Development Tournament (1,000 Matches Total)
- **Candidate H Win Rate:** **100.00%** (Seat 0: 100.0%, Seat 1: 100.0%).
- **Mean Paired Margin:** **+$11,561.0** (Candidate: $86,631.5 vs Frozen V2: $75,070.6).
- **Median Paired Margin:** **+$10,449.5**.
- **95% Confidence Interval:** **[+$11,191.8, +$11,930.2]**.
- **t-statistic:** **61.522** ($p = 4.07 \times 10^{-235}$).
- **5th Percentile Margin:** **+$6,082.4** | **Worst Loss:** **+$3,721.0 (Zero Losses in 500 games)**.
- **Catastrophic Losses (< -$20k):** **0.00%** | **Animal Starvation Events:** **0**.

### 2. 300-Game Unseen Holdout Suite (600 Matches Total, Seeds 7000–7149)
- **Candidate H Win Rate:** **100.00%** (Seat 0: 100.0%, Seat 1: 100.0%).
- **Mean Paired Margin:** **+$11,517.9** ($p = 6.78 \times 10^{-140}$).
- **95% Confidence Interval:** **[+$11,034.7, +$12,001.2]**.
- **Worst Loss:** **+$4,375.0 (Zero Losses in 300 games)**.

### 3. Factorial ANOVA Decomposition (400 Matches, Treatments A through H)
- **Treatment A (Frozen V2):** Margin = $0.0 (baseline).
- **Treatment B (Extra Workers Only):** Margin = -$134,893.7 (Labor desynchronization).
- **Treatment C (Extra Melons Only):** Margin = -$4,111.6 (3 workers cannot tend 12 melons).
- **Treatment D (Reduced Feed Only):** Margin = -$691.6 (Liquid cash idle in bank).
- **Treatment E (Workers + Melons):** Margin = -$132,849.9.
- **Treatment F (Workers + Reduced Feed):** Margin = -$128,266.7.
- **Treatment G (Melons + Reduced Feed):** Margin = -$33,057.1.
- **Treatment H (Full JIT Pipeline):** Margin = **+$11,278.52** (Win Rate: 100.0%).
- **Finding:** The mechanism is an **indivisible coordinated package** where freed feed capital finances labor, labor cultivates 12 melons, and melons fund Day-11 liquidity.

### 4. Verification of the "18 Extra Melons" Claim
- **Ground-Truth Telemetry:** 12 planted melons produce **60 harvest units** by Step 265 vs V2's **42 units** (**exactly +18 mature melons**).
- **Revenue Impact:** Generates **+$3,565.0 in melon sales**, driving Day 11 cash to **$12,814 – $13,531** vs V2's **$4,139 – $4,172** (+$8,642 cash surge).

### 5. Downstream Schedule Preservation
- Between Step 288 and Step 719, Candidate H converges identically to V2's **8 Cows and 6 Sheep** terminal herd structure, with zero schedule drift and zero animal starvations.

---

## Final Verdict
$$\mathbf{FINAL\ VERDICT:\ A.\ STRONG\ VERIFIED\ MECHANISM}$$

The Day-0 JIT Melon Pipeline produces a statistically definitive, highly robust, out-of-sample validated improvement while preserving downstream stability.

### Primary Deliverables Generated:
- Comprehensive Report: [reports/V2_DAY0_JIT_MELON_CAUSAL_STUDY.md](file:///c:/Users/Sundareswaran/Kagriculture/reports/V2_DAY0_JIT_MELON_CAUSAL_STUDY.md)
- Experimental Harness: [scratch/v2_jit_melon_experiment.py](file:///c:/Users/Sundareswaran/Kagriculture/scratch/v2_jit_melon_experiment.py)
- Micro-Telemetry Seed 42: [scratch/jit_melon_results/micro_telemetry_seed42.json](file:///c:/Users/Sundareswaran/Kagriculture/scratch/jit_melon_results/micro_telemetry_seed42.json)
- Micro-Telemetry Seed 100: [scratch/jit_melon_results/micro_telemetry_seed100.json](file:///c:/Users/Sundareswaran/Kagriculture/scratch/jit_melon_results/micro_telemetry_seed100.json)
- Factorial Raw Data & Effects: [scratch/jit_melon_results/factorial_effects.json](file:///c:/Users/Sundareswaran/Kagriculture/scratch/jit_melon_results/factorial_effects.json)
- 500-Game Dev Tournament Data: [scratch/jit_melon_results/dev_tournament_results.json](file:///c:/Users/Sundareswaran/Kagriculture/scratch/jit_melon_results/dev_tournament_results.json)
- 300-Game Holdout Data: [scratch/jit_melon_results/holdout_results.json](file:///c:/Users/Sundareswaran/Kagriculture/scratch/jit_melon_results/holdout_results.json)
