# V32 P4 DECISION REPORT

Date: 2026-09-23.
Phase: V32 P4 Critical Market Ordering & Joint-BC Stabilization.

---

## 1. Answers to Mandatory Decision Questions (§45)

### Question 1: Was P3's first divergence reproduced?
**YES.** In Arm 0, the baseline P3 BC checkpoints (`v32_p3_bc.npz` and `v32_p3_bc_lr3e3.npz`) were evaluated on step 0. Both checkpoints reproduced the exact reversed wash:
$$\text{Market} = [[\text{SELL}, \text{WHEAT}, 30], [\text{BUY\_PRODUCT}, \text{WHEAT}, 30]]$$
with 0/240 valid wash shape match, exactly replicating P3's first divergence report.

### Question 2: Did the model correctly reproduce the canonical step-0 market order?
**YES.** Under Arm 1 (Critical-Pattern Balanced BC), the model reproduced the exact canonical step-0 market order:
$$\text{Market} = [[\text{BUY\_PRODUCT}, \text{WHEAT}, 30], [\text{SELL}, \text{WHEAT}, 30]]$$
achieving **240/240 (100.0%) valid wash shape** on the dataset and **120/120 (100.0%) execution in closed-loop live matches**.

### Question 3: Did critical-pattern weighting help?
**YES, DECISIVELY.** Bounded critical-pattern weighting ($\lambda_{crit} = 50.0$) shifted Slot 0 $P(\text{BUY\_PRODUCT})$ from $0.18 \to 0.94$ and Slot 1 $P(\text{SELL})$ from $0.04 \to 0.84$. It recovered 100% of the opening wash without degrading global validation accuracy on any head (`val_full_exact`: 0.046 $\to$ 0.053, `mkt_nonnoop`: 0.801 $\to$ 0.810, `farmer`: 0.468 $\to$ 0.506).

### Question 4: Did market pretraining help?
**YES, IN ISOLATION; NO, UNDER JOINT TRAINING.**
- In Arm 2 (market-only pretraining), the market head learned the wash (240/240) and achieved 0.825 non-NOOP accuracy.
- However, when attached to the full policy in Arm 4 (unfrozen joint training without critical weighting), the pretrained market solution was destroyed within a single epoch (dropping from 240/240 to 0/240).

### Question 5: Did freezing vs unfreezing the market head reveal destructive joint optimization?
**YES, CONCLUSIVELY.**
- In Arm 4 (unfrozen), starting from a 100% accurate market head, joint unweighted training drove Slot 0 $P(\text{SELL})$ to 0.94 and completely flipped the wash into the reversed error mode `[SELL, BUY]`. This proves that the 51,526 non-step-0 `SELL` examples overpower the rare 192 step-0 opening wash examples under standard joint BC.
- In Arm 3 (frozen), freezing the market heads while training unit heads led to latent representation drift in the shared trunk, degrading market non-NOOP accuracy from 0.825 down to 0.486.

### Question 6: Do independent market heads appear insufficient to capture the ordered joint action?
**NO.** The independent market heads effortlessly captured the full ordered joint array in Arm 1 (79.51% full 10-slot array exact match on validation, 100% step-0 wash match). The failure in P3 was an optimization loss-dilution issue, not an architectural expressivity or marginal-independence bottleneck. Hypothesis H3 is not indicated.

### Question 7: Did the first meaningful divergence move later?
**YES.** Market slot-ordering divergence at step 0 was completely eliminated. Market action at step 0 matched A7 bit-identically (`[BUY30, SELL30]`). First divergence moved to subsequent turns (steps 1–10).

### Question 8: Did closed-loop economics materially improve?
**NO.** Although the opening wash executed 120/120 times and successfully injected $3,000 capital at step 0, downstream behavioral-cloning compounding drift across steps 1–719 caused terminal cash to average $108.39 (median $0.50, 0 wins).

### Question 9: What fraction of the P3 failure was explained?
**100% of the representation/optimization failure was explained.** The step-0 reversal was causally proven to arise from rare-sample loss dilution (192 vs 51,526) in the market head. However, the economic counterfactual proved that this step-0 reversal explains only the opening capital loss, not the entire $90k gap, which is governed by downstream compounding policy drift.

### Question 10: Is the bottleneck now:
The bottleneck is **downstream economic policy & compounding drift under unmasked behavioral cloning**. State representation, action schema, action codec, and joint critical market ordering optimization are all **SOLVED**.

### Question 11: Is the PPO gate:
```text
CLOSED
```
PPO gate remains strictly CLOSED.

---

## 2. Required Scientific Conclusion (§46)

```text
P4 PARTIAL — critical market behavior recovered, but economic compounding remains insufficient
```

```text
PPO 1M SLOPE GATE: CLOSED
```
