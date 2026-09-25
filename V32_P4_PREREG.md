# V32 P4 PREREGISTRATION — CRITICAL MARKET ORDERING & JOINT-BC STABILIZATION

Date: 2026-09-23.
Status: ACTIVE PREREGISTRATION (Gate entry).
Phase: V32 P4 (Research-only branch).

---

## 1. Scientific Objective

Determine why a native factorized action representation that can individually learn the critical market behavior fails to reproduce that behavior when optimized jointly with the full policy, and determine whether that failure can be repaired without introducing a broad new architecture or resorting to PPO.

P4 is a **joint behavioral-cloning stabilization experiment**.

P4 is NOT:
- PPO / RL
- A router
- An expert selection mechanism
- A new temporal encoder / Transformer / GRU / LSTM
- A broad architecture search or size sweep
- A competition submission
- A reason to reopen protected holdouts

**The PPO gate remains: CLOSED.**

---

## 2. Core Hypotheses

### H1 — Loss-Dilution Hypothesis
The critical opening market pattern is so rare (192 train samples = 0.139% of dataset) that standard joint BC minimizes the dominant global distribution (where Slot 0 is overwhelmingly SELL, 51,526 counts) and sacrifices the economically critical opening wash configuration (`[BUY_PRODUCT, SELL]`).
*Prediction*: Targeted critical-pattern preservation / principled bounded reweighting ($\lambda_{crit} \approx 50 - 100$) will recover step-0 market fidelity without degrading global unit or market accuracy, and without changing the neural architecture.

### H2 — Joint-Optimization Interference Hypothesis
The market heads can learn the correct behavior independently, but simultaneous backpropagation of unit losses ($L_{u\_op}, L_{u\_arg}, L_{u\_qty}$) and market losses creates optimization interference in the shared trunk parameters.
*Prediction*: Initializing the policy from a market-pretrained checkpoint and freezing the market parameters (or careful unfreezing) will isolate the causal impact of joint training on market behavior.

### H3 — Marginal-Mode / Slot-Dependence Hypothesis (Conditional Fallback Only)
Independent market-slot heads learn correct marginal distributions but fail to model the joint conditional dependency between Slot 0 and Slot 1 under ambiguous states.
*Condition*: H3 is **PROHIBITED** unless both H1 and H2 fail to restore the correct joint market configuration.

---

## 3. Frozen Components (No Modifications Permitted)

1. **Architecture**: Frozen `P3Policy` (157-dim input, shared 3×256 Tanh trunk, linear heads: $U\_OP(18), U\_ARG(12), U\_QTY(17), M\_OP(7), M\_ITEM(12), M\_QTY(77)$, 10 market slots with 16-dim slot embeddings). Total params: 277,092.
2. **Action Schema & Codec**: `V32_P3_ACTION_SCHEMA.json` and `v32/p3/codec.py` (passed G1 with 0 unexplained mismatches over 172,560 steps).
3. **Dataset**: `results/v32_p2_bc_legs.jsonl` (120 legs, 172,560 steps, SHA16 `55c907db955b1210`).
4. **Features & Normalizer**: `results/v32_p2_norm.json` (157 dims, `v32p2feat-v1`).
5. **Evaluator**: `scripts/v32_p3_evaluate.py` and `scripts/v32_p3_divergence.py`.
6. **Simulator**: `kaggriculture` 1.32.7.

---

## 4. Seed Registry & Partition Governance

- **Train Set**: Seeds `249635–249646` (12 seeds × 8 matches × 2 seats = 192 trajectories, 138,048 steps).
- **Val Set**: Seeds `249647–249649` (3 seeds × 8 matches × 2 seats = 48 trajectories, 34,512 steps).
- **Screen Evaluation Set**: Seeds `249675–249684` (10 seeds × 6 opponents × 2 seats = 120 legs).
- **Quarantine Refusal**: Protected holdouts GATE0 (`214200–214249`), V29 remainder (`340090–340199`), and V32-CONFIRM (`249695–249734`) remain strictly quarantined.

---

## 5. Preregistered Experimental Arms

| Arm | Description | Init | Market Trainable? | Loss Objective | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Arm 0** | Frozen P3 Baseline | P3 Checkpoint | N/A (Eval only) | Standard Joint BC | Control baseline |
| **Arm 1** | Critical-Pattern Balanced BC | Random | Yes | $L_{joint} + \lambda_{crit} L_{crit}$ | Tests H1 (Loss dilution) |
| **Arm 2** | Market Pretraining | Random | Yes | $L_{mkt}$ only | Pretrains market on full data |
| **Arm 3** | Market-Frozen Joint BC | Pretrained Market | **No (Frozen)** | $L_{unit}$ only | Tests H2 (Causal isolation) |
| **Arm 4** | Market-Init Joint Unfrozen | Pretrained Market | Yes (Unfrozen) | $L_{joint}$ | Tests H2 (Interference test) |
| **Arm 5 (H3)** | Conditional Slot Decoding | Random | Yes | Autoregressive slot | Conditional fallback only |

---

## 6. Gates and Decision Criteria

1. **Gate G1 (Codec Regression)**: Must retain 0 unexplained mismatches over 172,560 steps. [PASSED]
2. **Gate G2 (Step-0 Wash Recovery)**: Checkpoint must achieve $\ge 80\%$ valid wash shape (`[BUY_PRODUCT, SELL]`) on the 240 step-0 sample population.
3. **Gate G3 (Global BC Integrity)**:
   - Val `market_op_nonnoop` $\ge 0.80$
   - Val `unit_op` $\ge 0.45$
   - Val `farmer` $\ge 0.45$
   - No catastrophic collapse on any individual head.
4. **Gate G4 (Closed-Loop Economic Recovery)**:
   - First divergence step must advance beyond step 0.
   - Mean terminal cash across 120 screen legs must improve significantly over P3 ($>$ $1,000 mean, positive median).
5. **PPO Reopening Gate**:
   - Strictly **CLOSED** throughout P4.

---

## 7. Stop Conditions

- **P4-STOP-A**: If critical weighting (H1) and market pretraining/freezing (H2) both fail to recover step-0 wash without destroying global policy accuracy, trigger H3 diagnostic.
- **P4-STOP-B**: If step-0 wash is 100% recovered but closed-loop cash remains $\approx \$0$ across all arms, classify as downstream compounding economic failure. PPO remains closed.
- **P4-PASS**: Checkpoint achieves step-0 wash recovery ($\ge 80\%$), maintains global BC fidelity, and demonstrates reproducible closed-loop economic recovery ($>\$5,000$ mean, non-zero win rate).
