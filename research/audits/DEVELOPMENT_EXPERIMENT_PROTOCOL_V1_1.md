# DEVELOPMENT EXPERIMENT PROTOCOL V1.1 (PROSPECTIVE AMENDMENT)

## Authoritative Pre-Registration Amendment for `EXP-DEV-002` (Hedged Adaptive Crop Portfolio Research)

**Protocol Identifier**: `DEVELOPMENT-PROTOCOL-V1.1`  
**Governing Standard**: Prospective Scientific Pre-Registration & Anti-Publication Bias Covenant  
**Parent Protocol**: `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md` (SHA-256: `671e915eadd72adb710421b45e6a33ad533abd9d68ff67770b8dd412ff7381b3`, Commit `a1ba5acb0d04689874ce1333892825f014eea924`)  
**Date Established**: 2026-09-11  
**Status**: **FROZEN PROSPECTIVE SPECIFICATION — PRE-EXPERIMENTAL AMENDMENT**  

---

## 1. Epistemic Justification and Governance Lineage

Under Section 5 of `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md` and Directive 1 of the user instructions, this document provides a formal prospective protocol amendment for `EXP-DEV-002`.

### 1.1 Provenance & Motivation
- In `EXP-DEV-001`, the candidate `dev_001_dynamic_portfolio` failed the pre-registered tail-loss stop ceiling due to an unhedged 13-tile Tomato substitution on Day 11 based on only two early shop reveals. When subsequent town shops revealed Strawberry demand, the farm suffered a catastrophic opportunity cost (-$2,388.00 on Seed 50018).
- The parent protocol V1.0 had registered `EXP-DEV-002` as `RQ2: Rebuilt Shop Information Value Quantification` with candidate `dev_002_shop_voi_evaluator`. However, that candidate lacked concrete implementation code on disk, and the user research directive specifically prioritizes investigating **hedged adaptive portfolio behavior** that captures upside from revealed town demand while explicitly truncating irreversible downside exposure.
- In strict adherence to Directive 1 ("Do NOT invent a new treatment under the name EXP-DEV-002. If the frozen protocol does NOT contain enough specification for the intended hedged adaptation experiment, STOP and report: `EXP-DEV-002_PROTOCOL_AMBIGUITY.md`"), execution was halted, the ambiguity was formally reported, and this prospective amendment is frozen **prior to running any simulation code**.

---

## 2. Pre-Registered Experiment Specification: `EXP-DEV-002` (Hedged Adaptive Crop Portfolio)

### 2.1 Research Question
> **Can adaptive portfolio behavior capture useful economic surplus from revealed town shops while explicitly limiting irreversible downside exposure through structural hedging and bedrock crop floors?**

### 2.2 Formal Hypotheses
- **Alternative Hypothesis ($H_1$)**: A hedged adaptive crop policy that enforces a strict bedrock floor of at least 13 Strawberry plants and caps secondary Tomato substitution to at most 6 tiles achieves a mean paired margin $\Delta \mu > +\$50.00$ over `ClosedLoopAgentV2` on the 50 Discovery seeds, with non-inferior lower-tail downside risk ($p_{05} \ge -\$200.00$) and zero catastrophic tail breaches (worst single-seed loss $\ge -\$800.00$).
- **Null Hypothesis ($H_0$)**: Mean paired margin $\Delta \mu \le \$0.00$, or $p_{05} < -\$200.00$, or worst single-seed loss $< -\$800.00$.

### 2.3 Candidate Treatment: `dev_002_hedged_portfolio`
- **Identifier**: `dev_002_hedged_portfolio`
- **Module**: `candidates.closed_loop_architecture.dev_002_hedged_portfolio`
- **Class**: `Dev002HedgedPortfolioAgent`
- **Mechanistic Specification**:
  1. **Mode Conditioning**: Evaluates unlocked town shops at Day 3 (Step 72) and Day 6 (Step 144). Priority order:
     - Priority 1 (`YARN`): If any shop is `YARN_STORE`, execute Dmitrii's calibrated Yarn route (bit-exact V2).
     - Priority 2 (`STRAWBERRY`): If any shop is `SMOOTHIE_SHOP`, `ICE_CREAM_SHOP`, `BRUNCH_SPOT`, or `FARMERS_MARKET`, lock in Strawberry Bedrock (bit-exact V2).
     - Priority 3 (`CARROT`): If `PET_CAFE` is unlocked, enable secondary carrot planting on Day 18+ strictly when wheat inventory $\ge \text{feed\_reserve} + 10$.
     - Priority 4 (`WHEAT`): If `BAKERY` is unlocked, sell surplus wheat above feed reserve on Day 12+.
     - Priority 5 (`TOMATO`): If `PIZZA_SHOP` is unlocked (and no strawberry/yarn shop), enter **Hedged Tomato Mode**.
  2. **Bedrock Strawberry Floor & Substitution Cap**:
     - Unlike `dev_001_dynamic_portfolio` (which substituted all 13 strawberry seed purchases and plantings on Day 11), `dev_002_hedged_portfolio` enforces a strict **Bedrock Strawberry Floor** of 13 tiles and caps secondary Tomato substitution to **strictly $\le 6$ tiles**.
     - Exactly 6 strawberry seed purchases on Day 11 are converted to Tomato; the remaining 7 Day-11 strawberry purchases and all 12 initial strawberry plants remain 100% untouched.
     - This guarantees that even under a complete subsequent shop demand reversal to strawberries, the farm retains 13 mature strawberry plants yielding 52 total harvests, preventing the catastrophic -$2,388.00 collapse observed in EXP-DEV-001.
  3. **Liquidity Buffer**: Maintains a $500 cash floor to protect dawn labor hiring.
  4. **Post-Pull Market Sales**: Executes sales on `step % 4 == 1` batches.

### 2.4 Baseline Controls
1. **Control A (Primary Baseline)**: `ClosedLoopAgentV2` (Static 19S/0T Strawberry Bedrock with JIT headroom 96).
2. **Control B (Static Comparator)**: Static 19S/0T Baseline (Plan 0).
3. **Reference Benchmark**: `Dmitrii-LB2800` ([`extracted_agents/dmitrii_lb2800/main.py`](file:///c:/Users/Sundareswaran/Kagriculture/extracted_agents/dmitrii_lb2800/main.py)).

### 2.5 Common Random Number (CRN) Design & Seed Partitions
- **Evaluation Format**: Common Random Number (CRN) paired comparison with seat balancing:
  $$\text{Margin}(s) = (\text{Cand}_0(s) - \text{Ctrl}_1(s)) + (\text{Cand}_1(s) - \text{Ctrl}_0(s))$$
- **Discovery Partition**: Seeds `50000` to `50049` ($N=50$ seeds, 100 matches per pair).
- **Qualification Partition**: Seeds `50050` to `50099` ($N=50$ seeds, 100 matches per pair).
- **Certified Virgin Holdout**: Seeds `214200` to `214249` ($N=50$ seeds) — **STRICTLY PROHIBITED & QUARANTINED**.

### 2.6 Primary and Secondary Success Metrics
- **Primary Success Metric**: Mean Paired Margin vs `ClosedLoopAgentV2` in coins ($\Delta \mu$).
- **Secondary Metrics**:
  - $p_{05}$ lower-tail quantile margin ($)
  - Worst single-seed paired loss ($)
  - $p_{01}$ lower-tail quantile margin ($)
  - Downside frequency (fraction of seeds where margin $< \$0.00$)
  - 10% Trimmed mean margin ($)
  - Median paired margin ($)
  - Paired win rate (%)
  - Gross farm cash ($)
  - Paired margin vs `Dmitrii-LB2800`

### 2.7 Tiered Advancement and Stop Criteria
1. **Stage 1 (Discovery Gating)**:
   - **ADVANCE TO QUALIFICATION IF AND ONLY IF**:
     $$\Delta \mu > +\$50.00 \quad \text{AND} \quad p_{05} \ge -\$200.00 \quad \text{AND} \quad \min_{s}(\text{Margin}(s)) \ge -\$800.00$$
   - **STOP & MARK FAILED IF**:
     $$\Delta \mu \le \$0.00 \quad \text{OR} \quad \min_{s}(\text{Margin}(s)) < -\$800.00$$
2. **Stage 2 (Qualification Confirmation)**:
   - Evaluated on Seeds 50050–50099 with frozen code.
   - Must achieve $t > 1.96$ ($p < 0.05$) and worst loss $\ge -\$800.00$.

### 2.8 Information & Security Constraints
- All candidate agent turns must execute within the `ActiveContainmentSandbox`.
- Information available is strictly limited to legal contemporaneous observations (`obs`).
- Zero access to future town shops, future RNG, simulator internals, or holdout partitions.
