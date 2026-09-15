# AUDIT 2.1: AUDIT 2 INTERNAL CONTRADICTION ANALYSIS
## Forensic Cross-Document Consistency Audit Across the Audit 2 Deliverables

This document analyzes internal consistency, terminological tensions, and reporting discrepancies across the six documents comprising Audit 2:
1. `AUDIT2_SOURCE_MAP.md`
2. `AUDIT2_ENGINE_FACTS.md`
3. `AUDIT2_REPRODUCTIONS.md`
4. `AUDIT2_CORRECTION_LEDGER.md`
5. `CLEAN_EVIDENCE_BASE.md`
6. `AUDIT2_FINAL_VERDICT.md`

---

## 1. Itemized Internal Contradictions & Tensions

### Contradiction 1: P-Value Citation Divergence ($p = 0.070$ vs $p = 0.0726$)
- **Text in `AUDIT2_SOURCE_MAP.md` Line 25 (Row R5)**:
  > *"Asserting 'confirmed global superiority' with CI crossing zero... Mean = +$24.61, 95% CI = [-$2.07, +$51.30], p = 0.070."*
- **Text in `AUDIT2_SOURCE_MAP.md` Line 26 (Row R6)**:
  > *"True 150-Seed Sample Size: Exactly 150 unique seeds, 300 paired matches... Mean = +$24.61, CI = [-$2.07, +$51.30], Win Rate = 54.7% (82W-68L)."*
- **Text in `AUDIT2_REPRODUCTIONS.md` Line 21, 114 & `AUDIT2_FINAL_VERDICT.md` Line 32**:
  > *"t = 1.8078, p = 0.0726"*
- **Forensic Diagnosis**:
  Audit 2 has an internal contradiction within its own files: Row R5 cites $p = 0.070$, while Section 2 and Final Verdict cite $p = 0.0726$.
  - $p = 0.0706$ is the two-sided p-value from the standard normal approximation: $2(1 - \Phi(1.8078))$.
  - $p = 0.0727$ is the exact two-sided p-value from Student's $t$-distribution with $df = 149$: $2(1 - F_t(1.8078, 149))$.
- **Resolution**: Both values exceed $\alpha = 0.05$ and lead to the identical inferential conclusion (failure to reject $H_0$). However, Audit 2.1 standardizes on the exact Student's $t$ value: **$p = 0.0727$**.

---

### Contradiction 2: "Statistical Parity Established" vs Formal Equivalence
- **Text in `AUDIT2_REPRODUCTIONS.md` Line 125**:
  > *"Parity with a positive point estimate (+24.61 coins) is established; superiority is unproven."*
- **Text in `CLEAN_EVIDENCE_BASE.md` Line 75**:
  > *"Because the 95% confidence interval spans zero ($p > 0.05$), global statistical superiority cannot be claimed. The two agents are at statistical parity with a small positive point estimate."*
- **Forensic Diagnosis**:
  This statement borders on the classical statistical fallacy of *affirming the null hypothesis*. Failure to reject $H_0$ ($p = 0.0727 > 0.05$) means we lack sufficient evidence to claim superiority. It does NOT prove that the strategies are equal or equivalent.
  As proven by Audit 2.1's formal Two One-Sided Tests (TOST):
  - At an equivalence margin of $\pm \$25$, equivalence is **REJECTED** ($p_{\text{TOST}} = 0.4887$).
  - At an equivalence margin of $\pm \$50$, equivalence is **CONFIRMED** ($p_{\text{TOST}} = 0.0321$).
- **Resolution**:
  Audit 2 was correct to retract the claim of "proven superiority", but overstated the reverse by asserting that "parity is established". The scientifically accurate statement is: *"Failure to reject zero difference ($p = 0.0727$), with statistical equivalence established within an equivalence margin of $\pm \$50$ coins."*

---

### Contradiction 3: "Strict Dominance" vs Empirical Win Rate for 19S / 0T
- **Text in `AUDIT2_CORRECTION_LEDGER.md` Row C17**:
  > *"Pure 19S/0T Strawberry Bedrock strictly dominates all static hybrid allocations."*
- **Text in `CLEAN_EVIDENCE_BASE.md` Line 94**:
  > *"Within the space of tested static crop mixtures (100 CRN discovery matches), pure 19S/0T Strawberry strictly dominated all 11 hybrid Tomato allocations..."*
- **Text in `crop_portfolio_sweep_results.json`**:
  - Win rate of 19S/0T against Dmitrii: **59.0%** (41 losses / ties).
  - On Seed 50042: Tomato specialized agent earned +$3,942 over baseline V2.
  - On Seed 50026: Tomato specialized agent earned +$4,568 over baseline V2.
- **Forensic Diagnosis**:
  In game theory and formal economics, strategy $A$ "strictly dominates" strategy $B$ if and only if $u(A, s) > u(B, s)$ for **all** states of the world $s \in S$.
  Because Tomato outperformed Strawberry on individual seeds where Pizza shops unlocked, 19S/0T does NOT strictly dominate on a per-state basis.
  19S/0T achieved the **highest sample mean payoff** and the **lowest downside risk** across the tested static sweep, but calling it "strictly dominant" is an imprecise misuse of formal terminology.
- **Resolution**:
  Rephrase to: *"19S/0T achieved the highest mean payoff and lowest downside risk among all evaluated static allocations on the 50-seed Discovery set."*

---

### Contradiction 4: Open-Loop Mirror Performance Scope
- **Text in `AUDIT2_CORRECTION_LEDGER.md` Row C13**:
  > *"Dmitrii Base defeats live opponents on the exact seeds where live submissions lost... Verified in replay mirror mode ($90k–$115k vs $75k–$92k). Open-loop replay caution applies."*
- **Text in `AUDIT2_FINAL_VERDICT.md` Line 103**:
  > *"In counterfactual tests against recorded live opponent action streams (`test_live_opponents.py`), Dmitrii scored $90k–$115k vs opponent's $75k–$92k."*
- **Forensic Diagnosis**:
  Audit 2 noted "Open-loop replay caution applies", but placed this finding in Tier B ("Verified") in some tables and Tier C in others.
  In an interactive two-player economy, playing against a frozen recorded opponent action tape is open-loop. When Dmitrii executes different market orders, market inventory and prices would change in live play, potentially altering the opponent's subsequent choices.
- **Resolution**:
  The open-loop replay test demonstrates that Dmitrii's autonomous production engine generated higher internal value than the opponent under baseline conditions. However, it cannot prove live closed-loop victory against an adaptive opponent. It must be classified strictly as **Tier C (Bounded Empirical Finding)**.

---

### Contradiction 5: Causal Attribution of Live Tournament Losses
- **Text in `AUDIT2_FINAL_VERDICT.md` Line 61**:
  > *"The real cause of the live loss in episode 107543042 was a crop-demand mismatch: town revealed Double Pizza Shop, Triple Pet Cafe, and Zero Brunch / Zero Ice Cream. The opponent (ORiginators) specialized in Tomato and Carrot ($126k), while Eldritch produced Strawberry without town shop demand ($71k)."*
- **Forensic Diagnosis**:
  Audit 2 completely and brilliantly disproved Audit 1's "$800 hiring collapse" myth from the raw replay data.
  However, Audit 2's assertion that "the real cause was crop-demand mismatch" is an **economically compelling inference**, not an experimentally isolated counterfactual proof.
  To prove causal attribution under scientific standards:
  - We would need to run a counterfactual agent on that exact seed that dynamically adapted to Tomato/Carrot while holding all else constant, and demonstrate that score increased to parity.
  - While observed shop demands ($2\times \text{Pizza}, 3\times \text{Pet Cafe}$) and ORiginators' revenue ($126k$) strongly support this explanation, labeling it an established causal fact conflates strong inference with direct proof.
- **Resolution**:
  Audit 2.1 explicitly separates:
  - **Directly Observed**: Replay cash was $9,847; 9 workers were hired; shops were Double Pizza / Triple Pet Cafe; opponent made $126k on Tomato/Carrot; Eldritch made $71k on Strawberry.
  - **Mechanistic Reality**: Strawberry had zero boosted shop demand; Carrot had 2.0x multiplier at Pet Cafe; Tomato was demanded at Pizza and Farmers Market.
  - **Inferred Cause**: Specialization mismatch between static strawberry production and town shop demand was the primary driver of the score gap.

---

## 2. Synthesis of Audit 2 Consistency

Audit 2 is remarkably consistent internally. Unlike the accumulated research reports which contained dozens of wild contradictions (e.g. claiming $800 hiring costs while the code has Fibonacci; claiming 100% agronomy identity while tiles diverged by 460 turns), Audit 2's internal tensions are confined to:
1. Rounding and distribution choice nuances ($z$ vs $t$)
2. Imprecise use of formal terms ("parity established" and "strictly dominant")
3. Conflating strong economic inferences with experimentally proven counterfactuals

None of these minor tensions undermine the factual integrity of Audit 2's core retractions or engine discoveries.
