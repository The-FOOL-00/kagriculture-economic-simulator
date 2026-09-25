# V32 P5 PREREGISTRATION — CLOSED-LOOP BC RECOVERY & COVARIATE-SHIFT DIAGNOSIS

Date: 2026-09-23.
Status: ACTIVE PREREGISTRATION.
Phase: V32 P5 (Research-only branch).

---

## 1. Scientific Objective

Determine why the P4 policy, after correctly executing the economically critical step-0 opening action, begins diverging at approximately steps 1–10 and then catastrophically compounds error over the remaining horizon — and determine whether closed-loop training can recover stable behavior without changing the already-validated state/action architecture.

P5 is a **closed-loop imitation / covariate-shift diagnosis and recovery phase**.

PPO remains:
**CLOSED.**

---

## 2. Core Hypotheses

### H1 — Covariate Shift / Closed-Loop Drift
The BC model is trained exclusively on states drawn from the expert state distribution $s_t \sim d^{\pi^*}$. In autonomous deployment, early prediction errors cause the environment to transition into states $s_t \sim d^{\pi_\theta}$ not well-represented in the training data, leading to higher prediction errors and rapid error compounding.
*Prediction*: Supervised teacher-forced validation accuracy remains substantially higher than free-running closed-loop action match; state distance from the training distribution explodes following early action divergence.

### H2 — Error Compounding Concentrated in Specific Early Decisions
The downstream divergence is driven disproportionately by specific decision categories in steps 1–10 (e.g. invalid unit actions such as unexecutable `PLACE COW`, ungrounded market purchasing of non-vital goods, or improper cash depletion) rather than uniform gradual degradation.
*Prediction*: The first economically meaningful divergence occurs within steps 1–10; counterfactually preventing or correcting early post-wash divergence significantly alters the downstream trajectory.

### H3 — Off-Distribution Expert Relabeling / Aggregation (DAgger-Style)
If an expert oracle can be queried on policy-generated states $s \in d^{\pi_\theta}$, augmenting the training distribution with expert labels on the policy's own state visitations will mitigate covariate shift and stabilize closed-loop rollouts.
*Prerequisite*: A formal audit of the expert oracle must verify whether the expert policy is executable and semantically valid on arbitrary policy-generated states without private historical state.

---

## 3. Frozen Components

1. **Architecture**: Frozen `P3Policy` (157-dim input, shared 3×256 Tanh trunk, linear factorized action heads: $U\_OP(18), U\_ARG(12), U\_QTY(17), M\_OP(7), M\_ITEM(12), M\_QTY(77)$, 10 market slots with 16-dim embeddings; 277,092 params).
2. **Action Schema & Codec**: `V32_P3_ACTION_SCHEMA.json` and `v32/p3/codec.py`.
3. **Observation & Feature Representation**: 157-dim structured-temporal features (`v32p2feat-v1`), `results/v32_p2_norm.json`.
4. **Simulator**: `kaggriculture` 1.32.7.
5. **P4 Opening Wash Stabilization**: $\lambda_{crit} = 50.0$ on step 0 retained as baseline.
6. **Production Agents**: V3, A7, V22R1, Slot A, Slot B unchanged.

---

## 4. Seed Registry & Partition Governance

- **Train Set**: Seeds `249635–249646` (138,048 steps).
- **Val Set**: Seeds `249647–249649` (34,512 steps).
- **Screen Evaluation Set**: Seeds `249675–249684` (120 legs).
- **Quarantined**: GATE0 (`214200–214249`), V29 remainder (`340090–340199`), V32-CONFIRM (`249695–249734`), P3-CONFIRM (`249685–249694`).

---

## 5. Preregistered Experimental Arms

| Arm | Name | Training Treatment | Purpose |
| :--- | :--- | :--- | :--- |
| **Arm 0** | P4 Arm 1 Baseline | Frozen checkpoint (`results/v32_p4_arm1_balanced.npz`) | Control baseline |
| **Arm 1** | Diagnostic Rollout | No training; paired teacher-forced vs free-run rollouts | Quantify covariate shift & divergence timeline |
| **Arm 2** | Early-Horizon Weighting | Bounded loss weighting on steps 1–10 transitions | Test whether early post-wash steps are signal-starved |
| **Arm 3** | Valid State-Aggregation | Aggregate policy-visited states labeled by verified expert oracle | Direct covariate shift mitigation (DAgger-style) |
| **Arm 4** | Mixed Roll-In | Policy roll-in with probability $p$, expert target supervision | Train on states closer to deployment distribution |

*Note: Arms 3 and 4 are strictly conditional on the outcome of the Expert Oracle Availability Audit.*

---

## 6. Gates and Decision Criteria

1. **Gate G1 (P4 Baseline Replication)**: Checkpoint must verify 120/120 opening wash execution and mean terminal cash consistent with P4 ($108.39).
2. **Gate G2 (Covariate-Shift Demonstration)**: Diagnostic rollout must measure state distance divergence $\|s_t^{policy} - s_t^{teacher}\|$ and quantify degradation between teacher-forced and free-running action accuracy.
3. **Gate G3 (First Divergence Advancement)**: Any candidate intervention must delay first meaningful divergence beyond step 10 without degrading step-0 wash.
4. **Gate G4 (Closed-Loop Economic Recovery)**: Mean terminal cash on the 120-leg screen must improve significantly over P4 Arm 1 ($> \$1,000$ mean, non-zero win rate).
5. **PPO Gate**: Strictly **CLOSED**.

---

## 7. Stop Conditions

- **P5-STOP-A**: If diagnostics demonstrate that policy states do NOT leave the training manifold and action accuracy is not degraded by closed-loop rollouts, covariate shift is rejected.
- **P5-STOP-B**: If the expert oracle cannot produce semantically valid actions on arbitrary policy-generated states, pure DAgger aggregation is prohibited.
- **P5-STOP-C**: If bounded closed-loop BC interventions delay divergence but fail to achieve economic viability, classify as P5 PARTIAL / STOP and do not launch PPO.
