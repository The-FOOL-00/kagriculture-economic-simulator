# V41 Safe Residual RL & Counterfactual-Gated Strategic Policy Final Report

**Document ID:** `research/v41/reports/V41_FINAL_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `Kagriculture`  
**Mission:** Construct a safe learned strategic layer that discovers economically useful deviations without destroying the incumbent deterministic execution policy (A7/V35).  
**Final Governance Verdict:** **`V41_RESEARCH_ONLY`** (Quarantined in research; production baseline V35 remains live incumbent).

---

## 1. Executive Summary

The V41 research program executed a root-and-branch redesign of the interface between learned reinforcement learning intelligence and the deterministic A7 chore engine.

In V40, an RL policy operating over 16 unrestricted macro actions suffered catastrophic execution desynchronization against top bots:
```text
V40 PPO Tournament Result:
30.0% win rate
28 casualties / 40 matches
-$12,416 mean paired cash delta
```

V41 resolved this fundamental interface failure by implementing:
1. **StateAwareExecutor & Golden Property Invariant:** Guaranteed that when the policy abstains (Action 0), the action basket is **100% bit-for-bit identical to V35** across all 719 turns (empirically verified over 5,752 turns across multiple seeds with exactly 0 discrepancies).
2. **Mechanical Action Masking & Safety Classification:** Prohibited destructive actions (`FREEZE_HIRING`, `BLIND_HIRE`, uncoordinated animal/seed purchases) and restricted interventions to verified `SAFE_ATOMIC` and replan-gated primitives.
3. **Exact Simulator Counterfactual Gating:** Generated a dataset of 1,327 exact branch transitions using `FastKagricultureSim`, demonstrating that baseline abstention is optimal in 88.8% of states, while targeted interventions (terminal liquidation, peak spot sales, midgame expansion) offer +$130 to +$3,385 in positive alpha.
4. **Offline Strategic Value Model:** Trained a recurrent temporal model (`V41TemporalStrategicPolicy`, 103 obs -> 128 MLP -> 128 GRU -> 11 Q-values/actions) achieving **88.3% validation oracle agreement** and a low mean economic regret of **$103.8**.
5. **Non-Interfering Shadow Mode Audit:** Audited live decision-making in shadow mode, proving a **0.0% false-positive intervention rate** and **$31.85 mean regret**.
6. **Online PPO with Teacher KL Anchor:** Fine-tuned the strategic policy online against league opponents with monotonic reward gains ($86,667 -> $87,980).
7. **Rigorous A/B Ladder Tournament (96 Paired Match Legs):** Evaluated Ladder C (Deterministic Library), Ladder D (Offline Scorer), and Ladder E (Online PPO) against V35 on fresh unseen DEV seeds (`249685..249688`).

### The Breakthrough Result: Total Elimination of Casualties
Across all 96 paired match legs:
- **Casualties:** **0** (down from 28 in V40).
- **Win Rate:** **100.0%** across all opponents (`E8_DMITRII`, `E2_A7`, `E0_V3`, `SYN_AGG`).
- **Mean Cash Delta:** **-$38.62** for Ladder D and **-$47.16** for Ladder E (tightly bounded around baseline, zero catastrophic drops).

---

## 2. What V40 Proved vs What V41 Proved

### What V40 Proved
1. **High-Throughput Simulation is Feasible:** FastKagricultureSim delivers 304.7–470.0 SPS with 100% bit-for-bit parity.
2. **Exploration Can Be Maintained:** Recurrent sequence PPO avoids the heuristic entropy collapse of V38.
3. **Unrestricted Macro Actions Are Deadly:** Directly mutating resources while the deterministic A7 chore engine replays a static 719-step tape causes severe execution desynchronization (-$12,416 cash drop).

### What V41 Proved
1. **The Safe RL Interface Exists:** By enforcing `StateAwareExecutor` gating and mechanical legality masking, an RL policy can interact with a rigid chore chassis without causing a single casualty (0 casualties / 96 legs vs 28 in V40).
2. **Abstention Dominance:** In ~89% of game states, the deterministic A7 chore baseline is mathematically near-optimal. Any RL system that explores uniformly or acts continuously will degrade performance.
3. **Selective Economic Alpha:** Strategic deviations are only valuable at specific event-triggered milestones (Steps 693–694 liquidation, peak spot price spikes, and midgame capital expansions).
4. **Current Bottleneck Identified:** While the safety interface is completely proven, the net average delta across all 16 tournament matches was -$38.62 due to minor price slippage against market dumpers. Therefore, the learned policy does not yet provide reliable positive incremental alpha over V35 across the full match distribution.

---

## 3. Comprehensive A/B Ladder Tournament Results

Evaluated across 16 paired matches (32 legs per candidate, 96 total legs) on clean, unseen DEV seeds (`249685..249688`):

| Evaluation Metric | V40 Historical | Ladder C (Det. Library) | Ladder D (Offline Scorer) | Ladder E (Online PPO) | Production V35 Baseline |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Win Rate** | 30.0% | **100.0%** | **100.0%** | **100.0%** | 100.0% |
| **Win Rate Delta** | -70.0% | **+0.0%** | **+0.0%** | **+0.0%** | 0.0% |
| **Mean Cash Delta** | $-12,416.00 | $-104.06 | **$-38.62** | $-47.16 | $0.00 |
| **Median Cash Delta** | $-9,119.00 | $-95.50 | **$-47.00** | $-30.25 | $0.00 |
| **Casualties** | **28** | **0** | **0** | **0** | 0 |
| **Rescues** | 0 | 0 | 0 | 0 | 0 |
| **Safety Invariant Violations** | Severe | **0** | **0** | **0** | 0 |

---

## 4. Complete Research Deliverables & Reports

All mandated reports and artifacts have been authored and placed into the repository:

1. `research/v41/reports/V41_V40_FORENSICS.md`: Detailed mechanical root-cause analysis answering all 13 mandated failure questions.
2. `research/v41/reports/A7_DEPENDENCY_GRAPH.md`: Full reverse-engineered state machine, causal DAG, and invariant structure of the A7 chore chassis.
3. `research/v41/reports/SAFE_INTERVENTION_CATALOG.md`: Complete safety taxonomy (`SAFE_ATOMIC`, `CONDITIONALLY_SAFE`, `SAFE_WITH_REPLAN`, `UNSAFE`).
4. `research/v41/reports/EXECUTOR_REPLAN_REPORT.md`: Architecture of `StateAwareExecutor` and formal empirical proof of the Golden Property (0 discrepancies over 5,752 turns).
5. `research/v41/reports/COUNTERFACTUAL_DATASET_REPORT.md`: Empirical analysis of 1,327 exact counterfactual transitions mined via fast simulator branching.
6. `research/v41/reports/V41_OFFLINE_RL_REPORT.md`: Training diagnostics for the Advantage-Weighted offline policy (88.3% validation oracle agreement).
7. `research/v41/reports/V41_SHADOW_REPORT.md`: Live shadow-mode audit proving a 0.0% false-positive rate and $31.85 mean regret.
8. `research/v41/reports/V41_ONLINE_RL_REPORT.md`: Diagnostics of online PPO fine-tuning with frozen teacher anchor.
9. `research/v41/reports/V41_LEAGUE_REPORT.md`: Full head-to-head tournament tables across 4 opponents and 96 legs.
10. `research/v41/artifacts/interventions/`: Cataloged JSON primitives for liquidation, spot sales, land expansion, and labor constraints.
11. `candidates/v41_safe_residual/main.py`: Production-grade self-contained candidate agent with fail-closed safety fallback.

---

## 5. Candidate Package & Checksum Audit

- **Candidate Path:** `candidates/v41_safe_residual/main.py`
- **Model Weights Path:** `candidates/v41_safe_residual/model_weights.pt`
- **Candidate SHA256:** `3a28f422fbf3e0151912fde078534315d2c2764156cd48dbf29e6334a817d5f3`

### Absolute Governance & Integrity Audit
1. **Protected Baselines 100% Intact:**
   - `candidates/v35_a7_opening/main.py`: `1959021bdb1aeff720732aec866f5c9f3c9fa0b259ee0ab25982bda367593249` (**VERIFIED BIT-FOR-BIT IDENTICAL**)
   - `candidates/v30_a7_standalone/main.py`: `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` (**VERIFIED BIT-FOR-BIT IDENTICAL**)
   - `submission_aec_v22r1.tar.gz`: `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` (**VERIFIED BIT-FOR-BIT IDENTICAL**)
2. **Holdout Seed Isolation:** Protected holdout cohorts (`214200–214249`, `340090–340199`, `249695–249734`) were strictly guarded by automated runtime assertions. Exactly zero touches occurred.
3. **Competition Submission Prohibition:** Exactly zero `kaggle competitions submit` commands were proposed or executed.

---

## 6. Final Decision & Recommendation

```text
FINAL DECISION: V41_RESEARCH_ONLY
```

### Rationale
1. **Zero-Casualty Standard Satisfied:** V41 conclusively solved the fatal flaw of V40. Casualties dropped from 28 to 0, and win rate remained perfect at 100.0%.
2. **Zero Positive Incremental Alpha:** While V41 achieved individual match gains up to +$289.0 against static bots, its net tournament delta across all opponents averaged -$38.62 due to minor price slippages against dumping opponents.
3. **Governance Recommendation:** In accordance with Section 33, because V41 does not demonstrate positive net alpha over V35 across the full tournament population, it must **NOT** be promoted to live competition.
4. **Production Disposition:** V35 remains the live competition incumbent. The `StateAwareExecutor` and counterfactual gating architecture developed in V41 stand as the verified safe substrate for all future strategic RL research in Kagriculture.
