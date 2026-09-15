# AUDIT 2.1: MASTER CORRECTION LEDGER
## Exhaustive Record of Corrections, Scope Narrowings, and Refinements Applied to Audit 2 Findings

This ledger details every statement, formula, metric, or inferential claim in Audit 2 that required modification, narrowing, or correction during the independent Audit 2.1 re-audit.

---

## 1. Itemized Correction Table

| Correction ID | Original Audit 2 Statement | Audit 2.1 Verification Result | Specific Flaw, Mismatch, or Overstatement | Corrected & Authoritative Wording | Final Audit 2.1 Status |
|:---:|:---|:---|:---|:---|:---:|
| **CORR-01** | *"95% CI = [-$2.07, +$51.30]"* across 150 paired CRN seeds. | Verified as normal approximation ($z = 1.96$). | Used standard normal critical value ($1.96$) instead of Student's $t$ critical value with $df = 149$ ($t = 1.9760$). Discrepancy of $\pm 0.22$ coins. | **"95% CI (Student's t, df=149) = [-$2.29, +$51.52]; (Normal z=1.96) = [-$2.07, +$51.30]; (Bootstrap 100k) = [-$2.56, +$50.57]."** | **CORRECTED (FORMULA REFINED)** |
| **CORR-02** | *"p = 0.070"* in `AUDIT2_SOURCE_MAP.md:25` vs *"p = 0.0726"* elsewhere. | Verified as normal approximation vs Student's $t$. | Internal document inconsistency between normal approximation ($p = 0.0706$) and Student's $t$ ($p = 0.0727$). | **"Two-sided paired t-test: t = 1.8078, df = 149, p = 0.0727."** | **CORRECTED (UNIFIED)** |
| **CORR-03** | *"The two agents are at statistical parity with a small positive point estimate."* | Partially verified; failure to reject $H_0$ is not proof of parity. | Affirming the null hypothesis. Parity/equivalence is only scientifically established when an equivalence bound is specified and tested via TOST. | **"V2 achieves a positive point estimate (+24.61 coins, 54.7% win rate) that is not statistically significant at the 5% level (p = 0.0727). Formal TOST establishes statistical equivalence within an equivalence margin of ±$50 coins (p = 0.0321), but equivalence is not established at ±$25 (p = 0.4887)."** | **NARROWED (STATISTICALLY QUALIFIED)** |
| **CORR-04** | *"Pure 19S/0T Strawberry Bedrock strictly dominates all static hybrid crop portfolios across discovery and qualification partitions."* | Verified for mean margin on Discovery set; not strictly dominant on a per-seed basis, nor evaluated on qualification set. | In decision theory, strict dominance requires outperforming on every state (seed); here WR is 59%. Furthermore, the 12-allocation grid was run only on the 50 Discovery seeds (50000–50049). | **"Pure 19S/0T Strawberry Bedrock achieves the highest mean margin (+24.98), highest win rate (59.0%), and lowest downside risk (56.72) among all 12 evaluated static crop allocations on the 50-seed Discovery partition. It does not strictly dominate on every individual seed."** | **NARROWED (SCOPE RESTRICTED)** |
| **CORR-05** | *"The real cause of the live loss in episode 107543042 was a crop-demand mismatch: town revealed Double Pizza Shop, Triple Pet Cafe, and Zero Brunch / Zero Ice Cream."* | Verified as an economic inference, but not an experimentally isolated counterfactual proof. | Conflating strongly supported economic inference with counterfactually proven causality. | **"Directly Observed: Episode 107543042 revealed Double Pizza, Triple Pet Cafe, Zero Brunch, Zero Ice Cream. Eldritch produced pure Strawberry ($71k) while ORiginators produced Tomato and Carrot ($126k). Mechanistic Reality: Strawberry had zero shop multipliers while Carrot had 2.0x. Inferred Cause: Economic specialization mismatch between static strawberry production and town shop demand was the primary driver of the score gap."** | **NARROWED (EPISTEMICALLY SEPARATED)** |
| **CORR-06** | *"Dmitrii Base defeats live opponents on the exact seeds where live submissions lost... ($90k–$115k vs $75k–$92k)."* | Verified in replay mirror mode, but subject to open-loop limitations. | Overstating open-loop playback against frozen opponent action tapes as proof of live interactive victory. | **"In open-loop replay mirror evaluations against recorded opponent action tapes, Dmitrii Base achieved $90k–$115k vs opponent's $75k–$92k. This proves the economic strength of Dmitrii's autonomous engine, but does not simulate dynamic closed-loop live market price interactions."** | **NARROWED (OPEN-LOOP QUALIFIED)** |

---

## 2. Re-Affirmation of Confirmed Retractions

For the avoidance of doubt, Audit 2.1 **re-affirms and upholds all six major retractions** established by Audit 2:

1. **R1 (Tomato Alpha Retraction)**: Upheld without reservation. The +$3,942 result was an outlier on Seed 50042; the 6-seed True Pizza ensemble delta was -$5,382.67; all 18 tested parameter sweeps had negative mean deltas.
2. **R2 (Shop Demand Retraction)**: Upheld without reservation. `shop_transition_model.py` misstated demand for 6 of 8 shops. All downstream VoI models remain discarded.
3. **R3 (Slack Experiment Retraction)**: Upheld without reservation. `run_additive_investigation.py` never scheduled watering or harvesting for vacant crops and hired daily for 18 days. The experiment tested software bugs.
4. **R4 (Step 696 Causality Retraction)**: Upheld without reservation. Step 696 was an observational symptom; V2 had diverged in cash at step 164 and suffered sheep purchase failure at step 217.
5. **R5 (V2 Superiority Retraction)**: Upheld without reservation. The 95% confidence interval spans zero ($p = 0.0727 > 0.05$); global statistical superiority is not proven.
6. **R6 (V2 Statistics Transcription Retraction)**: Upheld without reservation. R14 Table 1 contained reporting transcription errors; raw JSON numbers are the authoritative record.
7. **S2 ($800 Hiring Collapse Disproof)**: Upheld without reservation. Raw replay `episode_107543042.json` had $9,847 cash and hired 9 hands. Hiring costs are Fibonacci ($7 for 4 hands), not $200 per hand. Parser bug in JSON.
8. **S4 (Physical Agronomy Identity Disproof)**: Upheld without reservation. V2 and Dmitrii diverged physically for 460 turns on Seed 50081, and Dmitrii runs terminal Monte Carlo planning at 712-717.
