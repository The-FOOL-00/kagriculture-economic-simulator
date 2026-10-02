# AUDIT 2.1: FINAL MASTER FORENSIC VERDICT
## Definitive Decision Gate on Audit 2 Reliability and Research Base Readiness

**Audit Exercise**: Independent Forensic Audit 2.1 of the Audit 2 Report Suite  
**Scope**: Verification of all material claims, engine rules, retractions, statistical calculations, and causal attributions across `AUDIT2_SOURCE_MAP.md`, `AUDIT2_ENGINE_FACTS.md`, `AUDIT2_REPRODUCTIONS.md`, `AUDIT2_CORRECTION_LEDGER.md`, `CLEAN_EVIDENCE_BASE.md`, and `AUDIT2_FINAL_VERDICT.md`  
**Evidence Standard**: Layer 1 C++ simulator source (`sim.hpp`), official `kaggle_environments 1.32.7`, tournament replay JSONs, frozen single-file submission scripts, and raw experiment JSONs  
**Development Ban**: Strictly honored. Zero development work, zero strategy proposals, zero agent modifications, zero submissions  

---

## 1. Primary Decision Gate Verdict

### **DECISION: GO WITH CORRECTIONS**

### **Primary Question Answer**:
> **Can we safely treat the conclusions of Audit 2 as the current trusted evidence base for proceeding to development?**

**Answer**: **YES, AS QUALIFIED AND CORRECTED IN AUDIT 2.1 (OUTCOME B: PARTIALLY VERIFIED / GO WITH CORRECTIONS).**

Audit 2 represents an extraordinarily rigorous and factually sound re-audit of the inherited research literature. **Zero material findings of Audit 2 are false, fabricated, or methodologically broken.** All six major retractions asserted by Audit 2 (R1 through R6), all verified engine facts (shop demands, Fibonacci hiring costs, order truncation, rot kinetics, weed RNG coupling), the disproof of the "$800 hiring collapse" myth, and the disproof of "100% bit-for-bit physical agronomy" survived independent reproduction from primary source code, tournament replays, and raw data.

However, an unreserved "GO" cannot be granted because Audit 2 contained five technical refinements that require explicit correction before development:
1. **Confidence Interval Formula**: Audit 2 reported the 150-seed 95% CI as `[-$2.07, +$51.30]` using the standard normal approximation ($z = 1.96$), rather than Student's $t_{149}$ critical value ($t = 1.9760$), which yields **`[-$2.29, +$51.52]`** (both cross zero).
2. **P-Value Reporting**: Audit 2 contained an internal discrepancy between $p = 0.070$ in `AUDIT2_SOURCE_MAP.md` and $p = 0.0726$ elsewhere; the exact Student's $t$ p-value is **$p = 0.0727$**.
3. **Statistical Parity Phrasing**: Audit 2 asserted that "statistical parity is established" based on failure to reject $H_0$; formal Two One-Sided Tests (TOST) demonstrate that equivalence is established within **$\pm \$50.00$ coins ($p_{\text{TOST}} = 0.0321$)**, but is **not proven** within tighter margins ($\pm \$25.00$, $p = 0.4887$).
4. **Game-Theoretic Terminology**: Audit 2 described 19S/0T Strawberry as "strictly dominant across all static allocations"; this must be narrowed to **mean-dominant on the evaluated 50-seed Discovery partition**, as 19S/0T achieved a 59% win rate and was outearned by tomato allocations on specific Pizza seeds.
5. **Live Loss Causality**: Audit 2 stated that the "real cause" of live losses was crop-demand mismatch; this is an **economically compelling inference**, but not an experimentally isolated counterfactual proof.

With these five corrections codified in `AUDIT2_1_CORRECTION_LEDGER.md` and `AUDIT2_1_CLEAN_EVIDENCE_BASE.md`, the Audit 2 knowledge base is certified as the authoritative ground truth for subsequent engineering.

---

## 2. Rationale for Decision Gate Classification

### Why NOT "REJECT / NO-GO"?
A "NO-GO" verdict is mandated if any major foundational claim regarding simulator semantics, experimental validity, statistical results, live submission identity, shop behavior, or V2/Dmitrii comparison is materially wrong.
In Audit 2.1:
- **Simulator Semantics**: Authoritative shop table, Fibonacci hiring costs, `MAX_ORDERS = 10`, crop rot kinetics, and weed RNG coupling were verified bit-for-bit from C++ `sim.hpp`.
- **Experimental Validity**: Audit 2's exposure of bugs in `run_additive_investigation.py` (zero watering/harvesting, daily hiring) and `reconstruct_live_losses.py` (parsing `units` instead of `hands`) was 100% verified.
- **Statistical Results**: Recalculation across all 150 paired CRN seeds verified mean (+24.61), median (+58.00), std (166.75), SE (13.61), t-stat (1.8078), and win rate (54.67%) to the penny.
- **Submission Identity**: Standalone compiled scripts `compiled_v54_plus_shop.py` and `compiled_v54_plus_residual.py` matched frozen SHA256 records bit-exact.
- **Replay Verification**: Raw replay `episode_107543042.json` proved that cash was $9,847 (not < $800) and 9 hands were hired, completely destroying the developer myth of an "$800 hiring collapse".
- **Physical Divergence**: Turn-by-turn tracing of Seed 50081 verified that cash diverged at Step 164 ($+\$460$), a sheep purchase failed at Step 217 ($497 < $500), and Tile (1, 4) diverged for 460 turns, disproving Audit 1's claim of 100% agronomy identity.
Because none of Audit 2's foundational conclusions were materially wrong, "NO-GO" is flatly rejected.

### Why NOT Pure "GO"?
A pure "GO" verdict requires that no claim requires narrower wording or corrected metrics.
Because Audit 2:
- Used a normal approximation z-score for its primary confidence interval without stating the approximation;
- Stated that "statistical parity is established" without bounding equivalence;
- Used the term "strictly dominant" for an empirical sweep with a 59% win rate;
- Conflated strong economic inference with counterfactually proven causality for live tournament losses;
a pure "GO" would fail our zero-tolerance forensic standard. "GO WITH CORRECTIONS" is the only epistemically defensible judgment.

---

## 3. Authoritative Summary of Knowledge Tiers

| Evidence Tier | Description | Key Findings Included | Reliability Level |
|:---|:---|:---|:---:|
| **Tier A** | Source-Proven Engine Facts | 720 steps, 30 days, 10x10 board, 8 shops sampled with replacement, authoritative shop demands, Fibonacci hiring costs ($1, 1, 2...$), `MAX_ORDERS = 10`, crop rot kinetics (1 unit/2 turns on even steps), shed capacity 100, weed RNG stream coupling. | **100% (Mathematical Ground Truth)** |
| **Tier B** | Reproduced Empirical Facts | Frozen submissions SHA256 integrity, V2 vs Dmitrii macro baseline (+24.61 coins, 54.7% WR, 95% CI `[-$2.29, +$51.52]`), TOST equivalence established within $\pm \$50$, shed threshold 88 defect, Closed-Loop V3 holdout collapse. | **100% (Independently Verified)** |
| **Tier C** | Bounded Empirical Findings | Static 19S/0T Strawberry dominance on 50-seed Discovery set (mean cash $97,026, margin +24.98, downside 56.72), runtime cash feedback divergence on Seed 50081 (missed sheep at step 217), open-loop replay mirror scores ($90k–$115k). | **High (Bounded by Tested Scope)** |
| **Tier D** | Strong Inferences | Live tournament loss attribution to static Strawberry production into Double Pizza / Triple Pet Cafe shop worlds. | **Strong Mechanistic Inference** |
| **Tier E** | Open Hypotheses | Profitable exploitation of spatial slack on Days 11–12; eliminating Seed 50081 divergence via Step 217 cash buffer. | **Unproven / Requires Empirical Test** |
| **Tier F** | Permanently Retracted | Tomato +$3,942 alpha (cherry-picked outlier), `shop_transition_model.py` (6 of 8 shops wrong), "no slack exists" theorem (bugged code), Step 696 root causality (observational symptom), V2 global superiority ($p > 0.05$), $800 hiring collapse myth (parser bug), 100% bit-for-bit physical agronomy (refuted). | **0% (Permanently Discarded)** |

---

## 4. Mandatory Final Synthesis Paragraph

**After independently auditing Audit 2 from primary C++ simulator source code (`sim.hpp`), official `kaggle_environments 1.32.7`, raw tournament replays, standalone submission binaries, and statistical recomputations across all 150 paired seeds, we can now treat as established fact the core simulator mechanics (8 town shops sampled with replacement, authoritative shop demand profiles, Fibonacci hiring costs, `MAX_ORDERS = 10` execution limits, crop rot kinetics, and weed RNG stream coupling), the cryptographic integrity of frozen submissions 56146971 and 56146947, the complete factual disproof of the "$800 dawn hiring collapse" myth from raw replay data ($9,847 cash, 9 hands hired), the disproof of "100% bit-for-bit agronomy identity" via verified Day 9 sheep purchase divergence on Seed 50081, the disproof of Step 696 order truncation as root causality, and the retraction of the +$3,942 Tomato alpha claim as a cherry-picked single-seed anomaly from a net-negative ensemble (-$5,382.67); we treat as bounded empirical findings the macro performance of `CLOSED_LOOP_V2` vs `Dmitrii-LB2800` (which achieves a statistically insignificant positive point estimate of +$24.61 coins with 54.7% win rate across 150 paired seeds, where Student's $t$ 95% CI `[-$2.29, +$51.52]` spans zero but TOST proves equivalence within a $\pm \$50$ margin), the mean performance dominance of static 19S/0T Strawberry Bedrock on the 50-seed Discovery partition, and open-loop replay mirror scores against past tournament opponents; we treat as open hypotheses the existence of profitably exploitable spatial slack on Days 11–12 and the counterfactual isolation of live tournament loss mechanisms; and it is SAFELY PERMISSIBLE TO PROCEED TO DEVELOPMENT under the GO WITH CORRECTIONS decision gate, provided that development strictly relies upon `AUDIT2_1_CLEAN_EVIDENCE_BASE.md` and treats V2 as a robust parity anchor rather than a proven superior champion.**
