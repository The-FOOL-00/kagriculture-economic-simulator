# Parameter Provenance Audit: Residual Preemption Configuration

**Protocol**: Championship Experiment — Residual Candidate Independent Replication Audit  
**Target Candidate**: `candidates/v54_plus_residual.py`  
**Parameters Audited**:
- `preempt_money_deficit = 2000.0`
- `preempt_minimum_delta = 4.0`
- `preempt_maximum_batch = 12`

---

## 1. Binary Provenance Question

> **WAS THE 1,000-MATCH HOLDOUT USED TO CHOOSE THESE PARAMETERS?**

### Direct Answer:
**NO.** The 1,000-match holdout (seeds 910,001 to 910,500) was **NOT** used to choose, tune, or optimize these parameters.

### Detailed Provenance Timeline:

1. **Initial Protocol Specification**:
   - In Prompt 1, Section 6 ("Test enable/disable both directions"), the protocol directed:
     *"For every important mechanism test: BASELINE, DISABLED, AGGRESSIVE, CONSERVATIVE. But define aggressive/conservative from the existing source semantics."*
2. **First Parameter Instantiation**:
   - In `scratch/instrumented_v54_plus.py` (committed at 09:15:59 local time), the switch `aggressive_preempt` was defined with:
     ```python
     elif self.switches.get("aggressive_preempt"):
         self.config_dict["preempt_money_deficit"] = 2000.0  # (baseline was 4000.0)
         self.config_dict["preempt_minimum_delta"] = 4.0      # (baseline was 8.0)
         self.config_dict["preempt_maximum_batch"] = 12       # (baseline was 8)
     ```
   - These values were selected as a halving/doubling heuristic from the baseline parameters (`preempt_money_deficit` halved from $4,000 to $2,000; `preempt_minimum_delta` halved from $\$8.0$ to $\$4.0$; `preempt_maximum_batch` increased from 8 to 12).
3. **Exploratory Counterfactual Gauntlet**:
   - At 09:33:13, `scratch/run_residual_counterfactuals.py` executed across 100 fresh seeds (seeds 900,501 to 900,600).
   - In that 100-seed run, `R2_agg_preempt` achieved a mean delta of $+\$10.16$ (95% CI: $[+\$3.3, +\$17.1]$).
4. **Candidate Freezing**:
   - The candidate `candidates/v54_plus_residual.py` was created with these exact three parameters.
5. **Holdout Evaluation**:
   - The 1,000-match holdout (`scratch/run_holdout_gauntlet.py`) was launched at 10:28:54 on fresh seeds 910,001 to 910,500.
   - Zero parameter changes were made during or after the holdout run.

---

## 2. Methodological Rigor Gap Identified

While the 1,000-match holdout was strictly un-tuned, the parameter choice originated from an informal, un-registered heuristic in the 100-seed exploratory gauntlet. 

To meet the gold standard of championship reproducibility:
1. We must execute a formal, pre-registered discovery grid on a new 500-seed discovery partition ($930,001\text{--}930,500$).
2. We must pre-register an explicit selection rule (maximizing the lower bound of the 95% bootstrap CI).
3. We must validate the selected candidate on a brand-new, completely untouched 1,000-match holdout ($940,001\text{--}940,500$).
