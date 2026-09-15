# EXP-DEV-002 FORENSIC AUDIT: FINAL POSTMORTEM VERDICT

**Experiment Identifier**: `EXP-DEV-002` (Hedged Adaptive Crop Portfolio)  
**Governing Protocol**: [`DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_1.md`](file:///c:/Users/Sundareswaran/Kagriculture/DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_1.md) (SHA-256 `735ad844b727...`, Git Commit `b2a4f45`)  
**Sample Cohort**: Discovery Partition Seeds `50000` to `50049` ($N=50$ seeds, 100 matches per pair)  
**Audit Date**: 2026-09-11  
**Auditor**: Antigravity Autonomous Pair Programmer (Lead Forensic Auditor)  

---

## 1. Executive Summary & Gating Determination

Following an exhaustive forensic audit of protocol provenance, candidate treatment specification, statistical recomputation, outlier sensitivity, and adversarial security, the final qualification determination for `EXP-DEV-002` is:

> ### **QUALIFICATION-ELIGIBLE WITH SCOPE**

### Key Justifications:
1. **Procedural & Cryptographic Cleanliness**:
   - Protocol Amendment V1.1 was pre-registered and committed to Git (commit `b2a4f45`) at **19:17:37**, strictly **prior** to experimental execution at **19:19:37**.
   - Zero result files existed on disk before the Git commit.
   - Candidate implementation code [`dev_002_hedged_portfolio.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/dev_002_hedged_portfolio.py) matches the frozen protocol bit-for-bit with zero silent deviations.
2. **Security & Governance**:
   - The 14-vector adversarial leakage suite achieved **100% interception**; the candidate passed AST audit (0 violations) and runtime sandbox execution (PASS).
   - The Certified Virgin Holdout (Seeds `214200–214249`) remains **100% unexecuted, uninspected, and quarantined**.
   - The two frozen live Kaggle submission files (`56146971` and `56146947`) are **bit-for-bit identical to their frozen hashes**.
3. **Mathematical Gating Status**:
   - All three Stage 1 Discovery gating criteria passed:
     - Mean Paired Margin: **+$250.06** ($> +\$50.00$ threshold)
     - Lower-Tail Risk ($p_{05}$): **$0.00** ($\ge -\$200.00$ threshold)
     - Worst Single-Seed Loss: **-$11.00** ($\ge -\$800.00$ stop ceiling)
4. **Scope Limitations & Exploratory Caveats**:
   - The parameter `cap = 6` was selected based on developmental sweeps on Seed 50018 (a Discovery seed). The claim that "Cap 6 is globally optimal" is **UNSUPPORTED** and must remain classified as **EXPLORATORY**.
   - Total surplus is intensely concentrated: Seeds 50004 and 50018 account for **96.9%** of the net margin surplus.
   - The statistical significance threshold ($p < 0.05$) is not met in Discovery ($p = 0.1738$ vs V2; $p = 0.1117$ vs Dmitrii). Confirmatory significance must be independently proven on the fresh Qualification partition (Seeds `50050–50099`).

---

## 2. Forensic Audit of Specific Narrative Claims

### 2.1 Audit of Claim: "Catastrophic Tail Eliminated"
- **Report Statement**: *"Worst loss improved from -$2,388.00 to -$11.00; catastrophic tail eliminated."*
- **Empirical Status**: Verified on the evaluated 50 Discovery seeds.
- **Mandatory Wording Correction**:
  - **CORRECT**: *"No catastrophic loss occurred within the evaluated 50-seed Discovery set."*
  - **INCORRECT (PROHIBITED)**: *"The strategy cannot produce catastrophic losses."*
  - **Rationale**: An empirical evaluation on 50 seeds cannot mathematically bound the entire universe of possible town shop permutations.

### 2.2 Audit of Claim: "Robust Mechanism Against Demand Reversal"
- **Report Statement**: *"Bedrock Strawberry Floor provides robust protection against future demand reversal generally."*
- **Empirical Status**: Verified specifically on Seed 50018, where late Strawberry shop demand materialized after early Pizza unlocks.
- **Mandatory Wording Correction**:
  - **CORRECT**: *"Hedging protected the farm on the tested Discovery set (specifically inverting Seed 50018 from -$2,388 to +$3,820)."*
  - **INCORRECT (PROHIBITED)**: *"Hedging is proven to robustly protect against all forms of demand reversal generally."*

### 2.3 Audit of Claim: "Dmitrii Dominance"
- **Report Statement**: *"Dominates Dmitrii-LB2800 with 68% win rate and +$287.90 margin."*
- **Empirical Status**: Recomputation confirms $N=50$, Mean = +$287.90, Win Rate = 68.0% (34 wins, 16 losses, 0 ties).
- **Mandatory Wording Correction**:
  - **CORRECT**: *"The treatment achieved a higher mean (+287.90) and majority win rate (68.0%) against Dmitrii-LB2800 on this Discovery cohort."*
  - **INCORRECT (PROHIBITED)**: *"Dominates Dmitrii."*
  - **Rationale**: The Student's $t$-test yields $t = 1.6197, p = 0.1117$, and the 95% CI `[-$69.30, +$645.10]` spans zero. The margin is not statistically significant at $\alpha = 0.05$.

### 2.4 Audit of Claim: "Top-10 Signal"
- **Report Statement**: *"Discovery results support Top-10 qualification."*
- **Mandatory Wording Correction**:
  - **CORRECT**: *"The result represents a positive development signal within Discovery."*
  - **INCORRECT (PROHIBITED)**: *"Evidence of Top-10 qualification."*
  - **Rationale**: The experiment was conducted in Discovery mode on 50 synthetic simulator seeds against frozen local baselines. It cannot predict or guarantee final Kaggle leaderboard percentile.

---

## 3. Epistemic Classification of Experimental Claims

Under the Epistemic Integrity Framework, all major claims regarding `EXP-DEV-002` are categorized:

| Claim Statement | Epistemic Classification | Evidentiary Grounding | Boundary / Constraint |
| :--- | :---: | :--- | :--- |
| **Protocol Amendment V1.1 was committed to Git prior to simulation execution.** | **VERIFIED FACT** | Git commit `b2a4f45` recorded at 19:17:37; execution started at 19:19:37. | Directly proven by repository metadata. |
| **Candidate code matches frozen protocol specifications without silent drift.** | **VERIFIED FACT** | Line-by-line code audit of `dev_002_hedged_portfolio.py`. | Bit-exact parameter alignment verified. |
| **On the 50 Discovery seeds, dev_002 achieved mean paired margin +$250.06 vs V2.** | **CONFIRMED DISCOVERY FINDING** | Recomputed from `EXP-DEV-002_RAW_RESULTS.json` ($N=50$). | Confirmed for Discovery partition (50000–50049). |
| **Discovery gating criteria in Protocol V1.1 were satisfied.** | **CONFIRMED DISCOVERY FINDING** | Mean > +$50, $p_{05} \ge -\$200$, worst loss $\ge -\$800$. | Evaluated under pre-registered Stage 1 rules. |
| **No catastrophic loss occurred within the 50-seed Discovery cohort.** | **CONFIRMED DISCOVERY FINDING** | Worst single-seed loss is -$11.00 (Seed 50017). | Bounded strictly to the 50 evaluated seeds. |
| **On Seed 50018, capping tomato substitution at 6 converted a -$2,388 loss into a +$3,820 win.** | **BOUNDED EMPIRICAL** | C++ simulation trace of Seed 50018 actions, sales, and rewards. | Specific to Seed 50018's shop and market sequence. |
| **On Seed 50004, capping tomato substitution at 6 retained +$8,300 of upside.** | **BOUNDED EMPIRICAL** | C++ simulation trace of Seed 50004. | Surrendered $6,964 vs unhedged 13-tomato agent. |
| **Cap 6 is the globally optimal substitution cap for Tomato substitution.** | **EXPLORATORY** | Derived from developmental counterfactual sweep on Seed 50018. | Seed-specific exploratory tuning; NOT confirmed globally. |
| **Bedrock Strawberry floor mechanistically prevents cash collapse under demand reversal.** | **INFERENCE** | Economic model of joint strawberry and tomato cash flows. | Mechanistically coherent, but unconfirmed on unseen reversals. |
| **The treatment strategy cannot produce catastrophic losses in any environment.** | **UNSUPPORTED** | Insufficient evidence across unobserved shop draws. | Rejected claim; prohibited from official documentation. |
| **Treatment achieves Top-10 Kaggle qualification.** | **UNSUPPORTED** | Kaggle leaderboard percentiles cannot be inferred from Discovery seeds. | Rejected claim; only positive development signal permitted. |

---

## 4. Governance and Security Invariants Verification

| Governance Item | Standard Required | Verified Status | Cryptographic / System Detail |
| :--- | :--- | :---: | :--- |
| **Holdout Quarantine** | Seeds `214200–214249` strictly unexecuted | **100% UNTOUCHED** | 0 executions; programmatic assertions active in harness. |
| **14-Vector Leakage Suite** | 100% interception of adversarial vectors | **100% PASS** | All 14 vectors trapped by `ActiveContainmentSandbox`. |
| **Candidate AST Security** | 0 illegal imports, builtins, or attributes | **100% PASS** | `audit_agent_ast` returns `[]` (clean). |
| **Candidate Runtime Sandbox** | 719 steps under containment without violation | **100% PASS** | `run_runtime_leakage_audit` status = `PASS`. |
| **Submission 56146971 Hash** | Bit-for-bit match with frozen hash | **MATCH (100%)** | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` |
| **Submission 56146947 Hash** | Bit-for-bit match with frozen hash | **MATCH (100%)** | `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8` |

---

## 5. Qualification Gate Recommendation & Conditions

The Discovery phase of `EXP-DEV-002` is **valid, mathematically accurate, and procedurally compliant**.

### Conditions for Subsequent Qualification Execution:
1. **Scope Restriction**: The candidate treatment must be tested strictly under the **exact frozen parameters** registered in Protocol V1.1:
   - Strawberry floor $\ge 13$ tiles
   - Tomato substitution cap $= 6$ tiles
   - Commitment deadline $=$ Step 144
   - Base liquidity reserve $=\$500.00$
2. **Zero Re-tuning**: No adjustments to the substitution cap or threshold logic are permitted prior to or during Qualification.
3. **Partition Independence**: Qualification must be evaluated exclusively on the pre-registered **Qualification Partition (Seeds `50050–50099`, $N=50$ seeds, 100 matches per pair)**.
4. **Holdout Protection**: The Certified Virgin Holdout (Seeds `214200–214249`) must remain strictly quarantined and must **NOT** be accessed during Qualification.
5. **Stage 2 Confirmation Criteria**: To confirm qualification, the candidate must achieve $t > 1.96$ ($p < 0.05$) and worst loss $\ge -\$800.00$ on Seeds 50050–50099.

**Final Determination**: **QUALIFICATION-ELIGIBLE WITH SCOPE**.
