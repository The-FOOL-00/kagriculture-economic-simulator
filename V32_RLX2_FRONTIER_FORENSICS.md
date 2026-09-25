# V32 RL-X2 — COMPETITION FRONTIER FORENSICS & TOP-3000 FEASIBILITY
**Phase:** V32 RL-X2  
**Date:** 2026-09-23  
**Status:** COMPLETE — EMPIRICAL RECONCILIATION & OPPORTUNITY MAPPING  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. The Frontier Dilemma (§54, §80)

Across internal round-robin benchmarks, our protected incumbent `A7` exhibits overwhelming local dominance:
- **vs `E0_V3`:** 100.0% Win Rate (+$1,286.00 mean margin).
- **vs `E1_V22R1` (Live Slot A):** 100.0% Win Rate (+$1,265.15 mean margin).
- **vs `V54`:** 100.0% Win Rate (+$19,916.20 mean margin).
- **vs `SYN_AGG`:** 100.0% Win Rate (+$160,700.05 mean margin).
- **vs `E8_DMITRII`:** 90.0% Win Rate (+$3,731.50 mean margin).

Yet on the live Kaggle leaderboard, A7 sits in the ~1800 rating band, while the top frontier entries push into the 2800–3000+ range.

### Core Scientific Question:
Why does an agent with a 98% internal win rate against public champions plateau at ~1800 on the live leaderboard, and what mechanisms separate A7 from the 3000-class frontier?

---

## 2. Forensic Dissection of High-Scoring Archetypes (§55)

### 2.1 The Dmitrii Gluzdov Mechanism (2800+ LB Lineage)
Through exact source inspection of `extracted_agents/dmitrii_lb2800/main.py` and turn-by-turn ledger tracing on Seed 249677 (where Dmitrii defeated A7 by -$1,167.00):
1. **Continuous Mid-Game Micro-Monetization:**
   - A7 relies on rigid 72-step budget guards and scheduled lot releases. If market conditions change between block boundaries, A7 holds inventory in the shed.
   - Dmitrii continuously liquidates fractional inventory whenever spot prices exceed marginal cost.
2. **Impending Shock Preemption (Steps 614, 697, 709):**
   - At Step 614, Dmitrii liquidated 48 Melons right before a town consumption tick, extracting a +$1,905 cash surge.
   - At Step 697, Dmitrii dumped 24 Milk units right before A7's milk wagon returned to the shed, causing a $703 price depression.
   - At Step 709, Dmitrii sold carrots at peak spot price ($128/unit) for +$511, while A7 held carrots for its Step 712 terminal batch.
3. **P11 Disproof of Physical Terminal Headroom:**
   - Phase P11 conclusively disproved the myth that Dmitrii wins by "terminal physical sweeping." At Step 712, A7 was already behind -$1,351 due to mid-game price events; in the terminal window itself (Steps 712–719), A7 actually out-earned Dmitrii by +$184.

### 2.2 The Ahmed Berat Özer / V43–V56 Lineage
- Public Kaggle notebooks from Ahmed Berat Özer (`Kaggriculture V43: Recovering Lost Harvests`, `V45`, `V56`) emphasize **front-loaded liquidity**.
- A7 captures the earliest part of this via the Step-0 30/30 wheat wash ($30 \times 25$ round trip).
- However, upstream tapes fail to dynamically re-allocate arable land when high-tier shops (e.g. Dairy or Textile) are revealed on Days 3 and 6.

---

## 3. What A7 Cannot Currently Do (The Open Economic Gap)

| Mechanism | A7 Current Behavior | Frontier Ideal Behavior | Est. Cash Headroom |
| :--- | :--- | :--- | :---: |
| **Mid-Game Selling** | Batched schedule; sells lots on pre-planned ticks | Opportunistic liquidation when spot price spikes | +$500 to +$1,500 |
| **Opponent Preemption** | Reactive front_run only on next step's planned SELL | Detects opponent inventory accumulation and front-runs before dump | +$800 to +$2,000 |
| **Feed Buffer Balancing** | Fixed wheat allocation; risk of feed stockout | Dynamic wheat expansion when livestock feed $< 2.5$ days | +$300 to +$800 |
| **Cash Runway Preservation**| Fixed Fibonacci hiring tape regardless of market crashes | Throttles hiring when runway $< 1.5$ days | +$400 to +$1,000 |

---

## 4. Top-3000 Plausibility Evaluation (§80)

### What evidence would make a 3000-class result plausible?
1. **Statistically Significant Paired Delta vs A7:** A candidate policy must achieve $\Delta \mu \ge +\$1,000.00$ paired delta across $\ge 20$ held-out development seeds without negative tail explosion ($worst \ge -\$200.00$).
2. **Dominance Over Dmitrii-Class Front-Runners:** Eradication of the Seed 249677 mid-game deficit (turning -$1,167 into positive delta).
3. **Robustness to Unseen Opponents:** Consistent positive alpha against diverse synthetic and declarative agents without regression against passive benchmarks.

### Honest Assessment as of 2026-09-23:
- Does A7 contain enough latent physical slack to reach 3000? **NO.** (P11 proved physical headroom is 0).
- Can pure low-level behavioral cloning reach 3000? **NO.** (P2–P7 proved imitation collapses on step 2).
- Can strategic macroeconomic learning (PPO + exact counterfactual search) reach 3000?
  - **Plausible:** If and only if the strategic policy successfully discovers the mid-game liquidation and preemption timing that exact search uncovers.
  - If empirical evaluation does not demonstrate this delta, we will state that fact honestly and lock A7 as the permanent live submission.
