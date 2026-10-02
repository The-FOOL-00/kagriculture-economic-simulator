# V38 Research Plan: Heuristic-Guided Hierarchical Residual PPO

**Document ID:** `V38_RESEARCH_PLAN.md`  
**Date:** 2026-09-25  
**Candidate Workspace:** `candidates/v38_heuristic_ppo/`  
**Research Scratchpad:** `scratch/v38/`  
**Benchmark Reference:** Frozen Live Production V35 (`candidates/v35_a7_opening/main.py`)  
**SHA-256 Checksum:** `1959021bdb1aeff720732aec866f5c9f3c9fa0b259ee0ab25982bda367593249` (Verified & Frozen)  

---

## 1. Executive Mission & Core Question

### Mission
Build and rigorously evaluate a new research candidate, **V38**, based on:
```text
Strong deterministic heuristic
         +
exact/near-exact forward simulation
         +
imitation learning (Behavioral Cloning)
         +
bounded residual PPO
```

The objective is **not** to replace the incumbent with a raw, end-to-end RL agent.  
The objective is to determine whether RL can learn **when and how to deviate from a strong heuristic** in economically meaningful situations while preserving the heuristic's proven physical choreography and long-horizon stability.

### The Central Research Question
> **Can a heuristic-guided hierarchical/residual PPO policy produce statistically significant matchup improvement over V35 without sacrificing V35's safety properties?**

If the answer is **no**, the project is successful provided that this is demonstrated rigorously:
`PPO ADDS NO RELIABLE VALUE` -> `KEEP_V35 / PPO_RESEARCH_ONLY`.

---

## 2. Governance, Baseline Freeze, and Seed Quarantine

### Frozen Baselines (Read-Only, Never Modified)
1. **Live Production Candidate (V35):** `candidates/v35_a7_opening/main.py`  
   SHA-256: `1959021bdb1aeff720732aec866f5c9f3c9fa0b259ee0ab25982bda367593249`
2. **Frozen A7 Incumbent:** `candidates/v30_a7_standalone/main.py`  
   SHA-256: `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f`
3. **Frozen V22R1 Archive:** `submission_aec_v22r1.tar.gz`  
   SHA-256: `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5`

### Quarantined Seed Ranges (Strictly Forbidden)
* `214200–214249` (Virgin holdout)
* `340090–340199` (Protected remainder)
* `249695–249734` (Confirmation holdout)

### Safe Seed Allowlists
* **Training Cohort:** `249635..249649` (15 seeds, safe sub-range of V32_TRAIN)
* **Dev / Validation Cohort:** `249675..249684` (10 seeds, matching V36 independent validation cohort)
* **Fresh Test Cohort:** `249685..249694` (10 seeds, untouched held-out sub-range of V32_DEV, strictly `< 249695`)

---

## 3. Architecture & Separation of Concerns

```text
                         OBSERVATION
                              │
                              ▼
                    STATE ABSTRACTION
                              │
             ┌────────────────┴────────────────┐
             │                                 │
             ▼                                 ▼
      ECONOMIC FEATURES                 PHYSICAL STATE
             │                                 │
             ▼                                 ▼
       VALUE / HEURISTIC                 DETERMINISTIC
          CONTROLLER                       PLANNER
             │                                 │
             └──────────────┬──────────────────┘
                            ▼
                    EXPERT HEURISTIC
                            │
                            ▼
                 MACRO ACTION PROPOSAL
                            │
                            ▼
                PPO RESIDUAL CONTROLLER
                            │
                 ┌──────────┴──────────┐
                 │                     │
                 ▼                     ▼
          TRUST_HEURISTIC        BOUNDED OPTION
                 │                     │
                 └──────────┬──────────┘
                            ▼
                  SAFETY ENFORCEMENT
                     (Fail-Closed)
                            │
                            ▼
                 DETERMINISTIC EXECUTOR
                            │
                            ▼
                       ENVIRONMENT
```

* **Learned Policy (PPO / BC):** Decides **WHEN**, **WHY**, and **HOW MUCH** (macro options, horizon, confidence).
* **Deterministic Controller & Physical Planner:** Decides **HOW EXACTLY** (exact spatial routing, chore execution, tool sequencing, legal checks).

---

## 4. Execution Phases

1. **Phase 1: Repository & Environment Reconnaissance**  
   Audit game rules, state representations, past RL-X2 failure mechanisms, search machinery.  
   *Deliverable:* `V38_REPOSITORY_AUDIT.md`.
2. **Phase 2: Reward Formulation**  
   Define sparse vs differential vs dense vs counterfactual advantage rewards.  
   *Deliverable:* `V38_REWARD_DESIGN.md`.
3. **Phase 3: Deterministic Expert Heuristic**  
   Build a complete, closed-loop economic heuristic that reasons about expansion, hiring, livestock, crops, and liquidation while executing physical choreography deterministically.  
   *Deliverable:* `V38_EXPERT_HEURISTIC.md`.
4. **Phase 4: Economic State Representation**  
   Create structured, zero-leakage observable economic state features separating financial from physical state.  
   *Deliverable:* `V38_ECONOMIC_MODEL.md`.
5. **Phase 5: Forward Simulator & Lookahead Engine**  
   Build exact $H$-step forward simulator with cloneable state for counterfactual evaluation.  
   *Deliverable:* `V38_COUNTERFACTUAL_ENGINE.md`.
6. **Phase 6: Macro Action Interface**  
   Define the discrete macro action vocabulary with explicit preconditions, postconditions, and resource bounds.  
   *Deliverable:* `V38_MACRO_ACTIONS.md`.
7. **Phase 7: Safety & Residual Architecture**  
   Build fail-closed safety layer, liquidity guard, cooldown guard, and heuristic fallback.
8. **Phase 8 & 9: Expert Dataset Generation & Quality Audit**  
   Generate counterfactual rollouts across safe seeds; check for seed/class imbalance, leakage, and duplicates.  
   *Deliverable:* `V38_DATASET_AUDIT.md`.
9. **Phase 10: Behavioral Cloning Warm Start**  
   Train imitation policy on expert macro targets; evaluate calibration, macro accuracy, and agreement.  
   *Deliverable:* `V38_BC_RESULTS.md`.
10. **Phase 11: PPO Residual Fine-Tuning**  
    Train PPO with actor-critic, action masking, conservative learning rate, entropy regularization.  
    *Deliverable:* `V38_PPO_RESULTS.md`.
11. **Phase 12, 13, 14: Critical A/B Evaluation, Intervention Forensics, & Causal Analysis**  
    Test paired rollouts against V35 and league opponents; classify interventions as Successful, Neutral, False Positive, Harmful.  
    *Deliverables:* `V38_INTERVENTION_FORENSICS.md`, `V38_CAUSAL_ANALYSIS.md`.
12. **Phase 15, 16, 17: Value Function, Curriculum & Adversarial Testing**  
    Test stress regimes (liquidity squeeze, market glut, high wage costs).  
    *Deliverable:* `V38_ADVERSARIAL_RESULTS.md`.
13. **Phase 18 & 19: RL-X2 Guardrails & Ablation Matrix**  
    Controlled comparison across 6 ablation configurations.  
    *Deliverable:* `V38_ABLATION.md`.
14. **Phase 20: Compute Ledger**  
    Record all runtime, training wall-clock time, parameter count.  
    *Deliverable:* `V38_COMPUTE_LEDGER.md`.
15. **Phase 21 & 22: Held-Out & Out-of-Sample Matchup Benchmark**  
    Rigorous paired 120-match mirrored tournament vs V35 across Dev and Fresh cohorts.  
    *Deliverables:* `V38_MATCHUP_RESULTS.md`, `V38_STATISTICS.md`.
16. **Phase 23 & 24: Promotion Gates & PPO Efficacy Decision**  
    Determine whether PPO produces genuine, generalizable value over V35.
17. **Phase 25, 26, 27: Cleanroom Audit & Distillation (if applicable)**  
    Verify imports, latency, determinism, zero leakage.  
    *Deliverables:* `V38_RUNTIME.md`, `V38_LEAKAGE_AUDIT.md`.
18. **Phase 28: Final Decision Report**  
    Issue authoritative final status: `PPO_NO_VALUE` or `HEURISTIC_ONLY_PROMISING` or `V38_PROMISING_NEEDS_MORE_VALIDATION` or `V38_PROMOTION_CANDIDATE`.  
    *Deliverable:* `V38_FINAL_DECISION.md`.

---

## 5. Non-Negotiable Operational Principles
1. **Background all long jobs (>10-15s):** Never block on long runs.
2. **Never edit V35, A7, or V22R1.**
3. **Never touch protected holdouts.**
4. **Heuristic before RL:** The deterministic baseline must be established first.
5. **No submission of V38:** Research only.
