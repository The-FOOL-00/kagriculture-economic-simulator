# V33 Route Counterfactual Oracle: Exact Payoff & Regret Analysis

**Program:** Kagriculture V33 Research Program  
**Date:** 2026-09-24  
**Question:** *What is the theoretical headroom of switching from R0_A7 to candidate expert routes at strategic boundaries, and what is the economic regret distribution?*  
**Artifact Generated:** `route_counterfactuals.jsonl` (45 evaluated transition legs)

---

## 1. Executive Summary & Core Scientific Findings

1. **Theoretical Headroom is Highly Asymmetric and Rare:**
   - In 30 out of 45 counterfactual legs evaluated against baseline $R0\_A7$, switching routes produced a **negative cash delta** ($\Delta < 0$).
   - For targets $R1\_V22R1$ and $R5\_V25P3$, counterfactual switching resulted in **100% negative deltas** across all seeds and all evaluation steps (Mean $\Delta = -\$328.1$ and $-\$309.7$ respectively).
   - Only $R2\_DMITRII$ produced positive counterfactual deltas, and only on specific seeds (249676 and 249677) during early phases ($t \le 144$).

2. **Severe Downside Tails on Mispredicted Switches:**
   - On Seed 249675, switching to $R2\_DMITRII$ at any step between $t=24$ and $t=144$ produced a catastrophic **$-\$8,433$ economic loss** ($A7=\$66,903 \to \text{Switch}=\$58,470$).
   - On Seed 249677, switching to $R2\_DMITRII$ at early steps ($t \le 144$) produced a **+$4,613$ gain** ($A7=\$92,592 \to \text{Switch}=\$97,205$), converting a loss into a match win against Dmitrii.

3. **Horizon Inflexibility ($t \ge 288$):**
   - By step 288, any switch to $R2\_DMITRII$ resulted in negative deltas across all seeds (Mean $\Delta = -\$3,292.3$), because the physical infrastructure (crops sown vs pastures built) diverged beyond repair.

---

## 2. Quantitative Summary by Target Route

| Target Route | Total Legs ($N$) | Mean Delta ($\Delta$) | Median Delta | Min Delta | Max Delta | Positive Delta Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`R1_V22R1`** | 15 | **-$328.1** | -$402.0 | -$490.0 | -$85.0 | **0 / 15 (0.0%)** |
| **`R2_DMITRII`** | 15 | **-$1,608.6** | +$257.0 | **-$8,433.0** | **+$4,613.0** | **8 / 15 (53.3%)** |
| **`R5_V25P3`** | 15 | **-$309.7** | -$372.0 | -$465.0 | -$85.0 | **0 / 15 (0.0%)** |

---

## 3. Breakdown by Step Horizon ($t \in \{24, 48, 72, 144, 288\}$)

### For `R2_DMITRII`:
- **$t=24$:** Mean $\Delta = -\$1,187.7$ (Min: $-\$8,433.0$, Max: $+\$4,613.0$, Pos: 2/3)
- **$t=48$:** Mean $\Delta = -\$1,187.7$ (Min: $-\$8,433.0$, Max: $+\$4,613.0$, Pos: 2/3)
- **$t=72$:** Mean $\Delta = -\$1,187.7$ (Min: $-\$8,433.0$, Max: $+\$4,613.0$, Pos: 2/3)
- **$t=144$:** Mean $\Delta = -\$1,187.7$ (Min: $-\$8,433.0$, Max: $+\$4,613.0$, Pos: 2/3)
- **$t=288$:** Mean $\Delta = -\$3,292.3$ (Min: $-\$8,130.0$, Max: $-\$432.0$, Pos: **0/3**)

### For `R1_V22R1`:
- **$t \in [24, 144]$:** Constant $\Delta \approx -\$325.0$ (Slight drag from switching execution logic without reallocating capital)
- **$t=288$:** $\Delta = -\$340.3$

### For `R5_V25P3`:
- **$t \in [24, 144]$:** Constant $\Delta \approx -\$306.7$
- **$t=288$:** $\Delta = -\$322.0$

---

## 4. Economic Regret Metrics

Defining:
$$\text{Regret} = \max_{r \in \mathcal{R}} \text{Cash}(r) - \text{Cash}(\text{Chosen})$$

Under the Default Baseline Policy ($R0\_A7$):
- **Mean Regret vs Counterfactual Oracle:** **$1,623.33** per episode across DEV seeds.
- **Max Regret:** **$4,613.00** (Seed 249677, where staying on A7 yielded $92,592 vs optimal switch $97,205).
- **P90 Regret:** $3,741.80.

Under an Uncontrolled / Naive Switch Policy (switching unconditionally to Dmitrii):
- **Mean Regret vs A7:** **$1,608.60** average loss.
- **Catastrophic Tail Risk:** **-$8,433.00** downside tail.

---

## 5. Architectural Implications for V33

1. **Mandatory Selective Abstention:**
   - Any selector that does not have a strict confidence and tail-risk gating threshold will degrade A7's performance. The default action MUST be `STAY_R0` (abstain).
2. **Commitment Deadline ($t \le 72$):**
   - No route switch may ever be initiated after Step 144. Late-game switching incurs irreversible capital destruction.
3. **Target Restriction:**
   - $R1\_V22R1$ and $R5\_V25P3$ provide zero counterfactual value when initialized from an A7 prefix. They are eliminated from the midgame switch candidate set.
   - Only $R2\_DMITRII$ represents a viable counter-strategy branch, specifically triggered when opponent livestock/market saturation signatures are confirmed.
