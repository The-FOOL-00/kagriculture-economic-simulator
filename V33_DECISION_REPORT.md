# V33 Final Decision & Scientific Evaluation Report

**Program:** Kagriculture V33 Research Program  
**Author:** Lead Research Engineer, Competition Scientist, and Implementation Owner  
**Date:** 2026-09-24  
**Competition Deadline:** September 30, 2026 at 11:59 PM UTC  
**Primary Strategic Objective:** Materially improve competition win rate over protected incumbent A7 ($P(\text{final\_cash}(\text{candidate}) > \text{final\_cash}(\text{opponent}))$).  
**Protected Incumbents:**
- **Slot A:** `V22R1` (`submission_aec_v22r1.tar.gz`, SHA-256: `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5`)
- **Slot B:** `A7` (`candidates/v30_a7_standalone/main.py`, SHA-256: `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f`)

---

## 1. Executive Summary & Final Promotion Decision

### Promotion Gate Outcome: **PROMOTION REJECTED**
The V33 research program completed a rigorous, leak-free, empirical evaluation across 300 simulation legs in the 6-opponent league, testing route extraction, route clustering, pairwise tournaments, non-transitivity search, early information horizons, exact counterfactual oracles, selective prediction, midgame resets, and market timing overlays.

### Central Scientific Finding:
**A7 is a near-universal expert in the competitive population.**
1. **Zero Non-Transitivity:** The dominance graph over candidate routes is strictly transitive ($R0\_A7 \succ R1\_V22R1 \succ R5\_V25P3 \succ R2\_DMITRII \succ R4\_V54 \succ R3\_P3090$). No non-transitive "rock-paper-scissors" cycles exist.
2. **Zero Complementarity:** In pairwise round-robin matches, A7 achieved a **96.0% win rate** (48/50 wins). No alternative route consistently defeats opponents that beat A7.
3. **Severe Downside Tails on Forced Switching:** Unconditional switching to alternative routes drops league win rate from **88.3% down to 33.3%** and creates an catastrophic $-\$8,433.00$ downside tail.
4. **Market Overlay Degradation:** Reordering sell orders based on price impact starves intra-turn liquidity, dropping win rate from **88.3% down to 83.3%** (-5.0% absolute drop).
5. **The V33 Selective Meta-Controller:** Under strict confidence and tail-risk gating, the V33 selector correctly **abstains 100% of the time**, preserving A7's 88.3% win rate and avoiding all downside risk. However, because no complementary route exists to switch into safely, it generates **+0.0% incremental win rate**.

In accordance with **Mandate Section 43, 44, and 57**:
> *"If V33 demonstrates no complementary routes or no positive fresh win-rate improvement, then explicitly close the branch... A7 remains protected, V22R1 remains protected."*

**Final Recommendation:**
- **Slot A:** Maintain `V22R1` (Frozen Adaptive Portfolio Champion).
- **Slot B:** Maintain `A7` (Protected High-Efficiency Benchmark Champion).
- **V33 Meta-Strategy Branch:** Closed. All artifacts, models, datasets, and tests preserved in `candidates/v33_meta_strategy/` for reproducibility.

---

## 2. Definitive Answers to the 25 Mandated Questions (Section 52)

### Q1: Does an elite route portfolio actually exist?
**Answer:** Yes, a portfolio of 6 structurally and economically distinct expert routes was constructed and validated in `RouteBank` (`R0_A7`, `R1_V22R1`, `R2_DMITRII`, `R3_P3090`, `R4_V54`, `R5_V25P3`).

### Q2: How many routes are genuinely distinct?
**Answer:** Four routes are genuinely distinct in their production regimes:
1. `R0_A7` (Open-loop single-quadrant crop monoculture)
2. `R1_V22R1` / `R5_V25P3` (Adaptive multi-quadrant balanced farming)
3. `R2_DMITRII` (Pure livestock specialist)
4. `R4_V54` (Commercial multi-land high-volume crop flood)

### Q3: How many are genuinely complementary?
**Answer:** **Zero.** No route in the portfolio provides complementary coverage against A7's failure modes. In the full round-robin tournament, A7 defeated every single alternative expert across almost all seeds and seats.

### Q4: Is matchup structure transitive or non-transitive?
**Answer:** **Strictly transitive.** Cycle-detection algorithms across directed graphs of length $k \in \{3, 4, 5, 6\}$ found **0 cycles**. A7 strictly dominates all other routes.

### Q5: Which routes complement A7?
**Answer:** None. While $R2\_DMITRII$ demonstrated a localized $+\$4,613$ advantage on Seed 249677, this advantage is isolated to a single seed and is heavily outweighed by an $-\$8,433$ collapse on Seed 249675.

### Q6: Which routes dominate or lose against which opponent classes?
**Answer:**
- `R0_A7`: Dominates `E0_V3` (100%), `E1_V22R1` (100%), `SYN_AGG` (100%), `V54` (100%); achieves 80% against `E8_DMITRII`; ties self-mirrors (50%).
- `R1_V22R1`: Wins 100% vs `E0_V3`, `SYN_AGG`, `V54`; but scores only 20% vs `E8_DMITRII` and 0% vs `E2_A7`.
- `R2_DMITRII`: Wins 100% vs `V54` and `R3`; but loses to `R0_A7` (20%), `R1_V22R1` (20%), and `R5_V25P3` (20%).
- `R3_P3090`: Loses 100% (0/50 wins) against all interactive closed-loop agents.

### Q7: How early can observable information distinguish the useful route?
**Answer:** Observable information peaks in variance between **$t=4$ and $t=16$** (visible opponent hires and early tool purchases). However, seed-specific market conditions are completely indistinguishable at $t=0$ and remain noisy through $t=16$.

### Q8: What is the economic cost of waiting for information?
**Answer:** Catastrophic. By $t=4$, farms commit $>70\%$ of starting capital ($\$2,146 / \$3,000$). Delaying route selection beyond $t=16$ costs $\approx \$325$ in coordination friction, escalating to $\approx \$3,292$ by $t=288$.

### Q9: Can route switching be done safely?
**Answer:** Only conditionally at early steps ($t \le 48$) between compatible crop routes ($A7 \to V22R1$). Splicing into livestock routes ($A7 \to DMITRII$) after $t \ge 72$ causes physical desynchronization between crop land and animal pens.

### Q10: Does one-switch beat zero-switch?
**Answer:** **No.** One-switch achieves at best an identical 88.3% win rate (when gated to abstain) and drops to 33.3% if forced. Zero-switch (pure A7) is superior.

### Q11: Does midgame reset beat one-switch?
**Answer:** **No.** Re-evaluating alternatives at $t=48$ and $t=144$ yields 0 additional switches under confidence gating and generates 0 incremental win rate.

### Q12: Does market timing add independent value?
**Answer:** **No.** Reordering sell orders based on price impact degrades win rate from **88.3% to 83.3%** (-5.0%) and produces an average economic drag of **$-\$161.60$**. It was permanently disqualified under Mandate Section 48.

### Q13: Does supervised selection outperform simple rules?
**Answer:** No. Because observable signals are highly noisy and the underlying headroom is near-zero, complex supervised models overfit to development seeds. A simple confidence-gated rule that defaults to A7 is the only policy that avoids negative delta.

### Q14: Does PPO add anything beyond supervised selection?
**Answer:** **No.** As observed in V32 RL-X2 and public research, PPO meta-selectors suffer from policy drift, destroy A7's choreographed execution, and plateau below the supervised/incumbent baseline. PPO was ruled out under Mandate Section 32 & 48.

### Q15: Does route selection improve actual win rate?
**Answer:** **No.** League win rate remained 88.3% (53/60 wins), exactly identical to pure A7.

### Q16: Does it improve fresh-seed win rate?
**Answer:** No. On unseen development seeds, the selector abstains, yielding zero net improvement over A7.

### Q17: Does it improve both seats?
**Answer:** Performance is symmetric across both Seat 0 and Seat 1, but identically equal to A7 in both seats.

### Q18: What is the worst failure case?
**Answer:** **Unconditional switching on Seed 249675**, which produced a **$-\$8,433.00$ economic collapse** ($A7=\$66,903 \to \text{Switch}=\$58,470$) due to asset misallocation.

### Q19: What is the most common failure case?
**Answer:** **F1 / F11 (Route Redundancy & Transitive Dominance).** Candidate routes are sub-dominant to A7 across standard market regimes.

### Q20: Is V33 actually better than A7?
**Answer:** **NO.** V33 matches A7's win rate (88.3%) only by abstaining. It does not outperform A7.

### Q21: If yes, under what conditions?
**Answer:** N/A (Not better).

### Q22: If no, why not?
**Answer:** A7's single-quadrant, 4-worker open-loop monoculture achieves near-optimal capital velocity. Alternative routes spend too much capital on land or livestock that cannot amortize within 720 turns, and market prices are not depressed enough by opponents to make crop farming unviable.

### Q23: Which branch should be frozen?
**Answer:** The `v33_meta_strategy` branch is completed, documented, and frozen. No further route-meta variants should be pursued without a fundamentally new economic mechanism.

### Q24: What should Slot A be?
**Answer:** **`V22R1`** (`submission_aec_v22r1.tar.gz`, SHA-256: `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5`).

### Q25: What should Slot B be?
**Answer:** **`A7`** (`candidates/v30_a7_standalone/main.py`, SHA-256: `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f`).

---

## 3. Preservation of Protected Incumbents & Hash Verification

1. **A7 Standalone Incumbent:**
   - Path: `candidates/v30_a7_standalone/main.py`
   - Verified SHA-256: `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` (EXACT MATCH, 100% UNTOUCHED).
2. **V22R1 Archive Incumbent:**
   - Path: `submission_aec_v22r1.tar.gz`
   - Verified SHA-256: `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` (EXACT MATCH, 100% UNTOUCHED).
3. **Virgin Holdouts:**
   - Protected cohorts `214200..214249`, `249695..249734`, and `340090..340199` remain 100% untouched and unaccessed.
