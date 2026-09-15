# KAGGRICULTURE — AUDIT #2: FINAL MASTER FORENSIC VERDICT
## Auditing the Auditor: Rigorous Epistemic Ground-Truth Reconstruction

**Audit Scope:** Independent forensic verification of the First Forensic Research Audit (`FORENSIC_RESEARCH_AUDIT_FINAL.md`, `FINAL_EVIDENCE_MATRIX.md`, `CONTRADICTIONS.md`) against Layer 1 source code (`sim.hpp`, `kaggriculture.py`), executable minimal tests, official tournament replays, and raw dataset JSONs.  
**Audit Standard:** Zero-tolerance verification. Distinguish empirical observations from causal explanations ("Right Result, Wrong Reason").  
**Frozen Controls:** Submissions `56146971` and `56146947` remain strictly frozen and untouched.  
**Development Ban:** Strictly enforced. No V4 design, no strategy proposals, no tuning, no live submission actions.

---

## 1. WHAT AUDIT #1 GOT RIGHT

1. **R1 (Tomato Specialization Cherry-Picking)**:
   - Audit #1 correctly identified that the widely cited "+$3,942 Pizza-world cash gain" was a single cherry-picked seed (Seed 50042).
   - Across the 6 True Pizza seeds (`50003, 50011, 50021, 50026, 50030, 50042`), the ensemble average was **-$5,382.67** against V2.
   - All 18 parameter combinations in `scratch/true_pizza_sweep_results.json` produced net-negative average deltas vs V2.

2. **R2 (Fabricated Shop Demand Profiles)**:
   - Audit #1 correctly identified that `candidates/closed_loop_architecture/shop_transition_model.py` misstated product demand profiles for **6 out of 8 shops** compared to official Kaggle environment rules and C++ `sim.hpp`.
   - Pet Cafe demands strictly Carrot (not Milk); Pizza demands Milk, Tomato, and Wheat (not just Wheat + Tomato); Smoothie demands Strawberry and Milk (not Carrot, Strawberry, Melon); etc.
   - All downstream calculations based on this model (Markov transitions, Value of Information) were built on mathematically false rules.

3. **R3 (Slack Capacity Implementation Bugs)**:
   - Audit #1 correctly identified that the experiment claiming to prove "no resource slack exists anywhere in V2" (`scratch/run_additive_investigation.py`) was severely broken in code.
   - In `VACANT_TILES` mode, tomatoes were planted on vacant tiles without any watering or harvesting logic, causing all crops to rot into weeds.
   - In `SE_LAND` mode, `HIRE` was called on hour 1 of every single day from Day 12 to Day 29 (18 consecutive days).
   - The experiment tested software bugs, not economic viability.

4. **R5 & R6 (Statistical Overclaiming on V2 Superiority)**:
   - Audit #1 correctly downgraded the claim that `CLOSED_LOOP_V2` was "confirmed globally superior" to `Dmitrii-LB2800`.
   - Independent recalculation of all 150 paired CRN seeds in `scratch/v2_dmitrii_margin_scan.json` confirms:
     $$\text{Mean Combined Margin} = +\$24.61, \quad \text{Std} = 166.75, \quad \text{SE} = 13.61, \quad 95\%\text{ CI} = [-\$2.07, +\$51.30], \quad t = 1.8078, \quad p = 0.0726$$
   - Because the 95% confidence interval spans zero ($p > 0.05$), claiming established statistical superiority was invalid.
   - Audit #1 correctly exposed transcription errors in R14 Table 1 versus the underlying JSON data.

5. **S1 (Frozen Submissions Integrity)**:
   - Audit #1 correctly identified that active submissions `56146971` (`compiled_v54_plus_residual.py`) and `56146947` (`compiled_v54_plus_shop.py`) are cryptographically verified and active.

6. **S3 (MAX_ORDERS = 10 Enforcement)**:
   - Audit #1 correctly cited and interpreted the engine limit of 10 market orders per turn per player (`sim.hpp` line 554). Excess orders are silently dropped without error.

7. **S5 (19S/0T Static Strawberry Dominance)**:
   - Audit #1 correctly confirmed that pure 19S/0T Strawberry strictly dominates all 11 tested static hybrid allocations within `crop_portfolio_sweep_results.json`.

8. **S6 (Simulator Mechanics)**:
   - 720 steps, 24 steps/day, 8 shops sampled uniform at random with replacement, and crop rot kinetics (1 unit per 2 turns on even steps) were accurately cited.

---

## 2. WHAT AUDIT #1 GOT WRONG

1. **S2 (The Day-12 Dawn Hiring Collapse Myth)**:
   - Audit #1 declared as **Grade A Verified** that our live submissions collapsed because:
     *"entering Day 10–12 with < $800 cash failed the dawn hiring step (4 x $200 = $800). Hands dropped from 7 to 4, leaving unharvested crops to rot and causing losses of -$40k to -$55k."*
   - **AUDIT #2 DISPROVES THIS COMPLETELY**:
     - In the primary cited replay (`replays/live_tournament/episode_107543042.json`), on Day 12 dawn, Eldritch had **$9,847.0 cash** (nowhere near < $800).
     - Eldritch hired **9 hands** on Day 12 (hands did not drop from 7 to 4).
     - Engine hiring costs follow the Fibonacci sequence: $\text{Cost} = \text{fib}(\text{hires\_today})$. Hiring 4 hands costs **$7.00**, NOT $800. Hiring 11 hands costs $232.00, NOT $2,200.
     - The "$200 per hand" formula was an agent heuristic invented in `closed_loop_v2.py` (`hiring_obligation = (len(hands) + 1) * 200.0`), which Audit #1 mistook for an engine rule.
     - Audit #1 relied on `scratch/reconstructed_live_losses_forensics.json`, which had a software bug parsing `f.get("units", [])` instead of `f.get("hands", [])`, recording `hands: 0` for all checkpoints.
     - **The real cause of the live loss** in episode 107543042 was a crop-demand mismatch: town revealed Double Pizza Shop, Triple Pet Cafe, and Zero Brunch / Zero Ice Cream. The opponent (ORiginators) specialized in Tomato and Carrot ($126k), while Eldritch produced pure Strawberry without town shop demand ($71k).

2. **S4 (Physical Agronomy Bit-for-Bit Identity)**:
   - Audit #1 claimed: *"CLOSED_LOOP_V2 and Dmitrii-LB2800 execute 100.0% bit-for-bit identical physical agronomy across all 30 days (identical tile assignments, planting schedules, watering cycles, fertilizations, animal purchases, and hand movements)."*
   - **AUDIT #2 DISPROVES THIS**:
     - While V2 and Dmitrii share the same base agronomy tape, runtime cash dynamics cause physical actions to diverge.
     - On Seed 50081 (V2's worst paired loss of -$730), V2 entered Step 217 with $950.0 cash versus Dmitrii's $954.0 (a $4 deficit caused by early wool sales).
     - At Step 217, both agents attempted to buy 2 Sheep (`['BUY_ANIMAL', 'SHEEP', 2]`, cost $1,000) and hire a worker. Dmitrii could afford both; V2 had only $497 left after the first sheep, falling $3 short.
     - At Step 259, Hand 6 attempted `['PLACE', 'SHEEP']`. Dmitrii placed the sheep on Tile (1, 4). V2 had no sheep in Hand 6's inventory, so the placement failed.
     - Tile (1, 4) remained an empty pasture on V2's farm for the next **460 turns** while Dmitrii harvested wool!
     - Furthermore, at steps 712–717, Dmitrii executes a 64-sim Monte Carlo terminal planner (`ShopClosure`) that moves hands and collects fertilizer, whereas V2 executes static tape actions (`PASS`).
     - Physical agronomy is **NOT** 100.0% bit-for-bit identical.

---

## 3. WHAT AUDIT #1 OVERSTATED

1. **Step 696 Counterfactual Testing (R4)**:
   - Audit #1 correctly concluded that Step 696 order truncation is not the causal root of V2 losses.
   - However, Audit #1's counterfactual script (`scratch/test_step696_causal.py`) was overly aggressive: in line 25, it set `action["market"] = [['SELL', 'WHEAT', 36]] + hires`, which unintentionally stripped V2's legitimate JIT strawberry sales.
   - Audit #2 proved from turn-by-turn cash tracing that V2 had already diverged at step 164 ($+\$460$) and step 217 (missed sheep purchase), long before Step 696. Step 696 was an observational symptom, not the cause.

2. **Theoretical Generalization on Slack (R3)**:
   - Audit #1 correctly retracted the earlier claim that "it is proven that no resource slack exists anywhere in V2."
   - However, Audit #1 occasionally drifted toward suggesting that slack *cannot* exist. As proven by the spatial audit, physical idle tiles exist on Days 11–12. Whether a correctly scheduled, properly watered crop can exploit them remains an open hypothesis.

3. **Scope of Strawberry Bedrock Dominance (S5)**:
   - Audit #1 stated that 19S/0T "strictly dominates all crop portfolios."
   - To be scientifically accurate: 19S/0T strictly dominates all **tested static hybrid crop allocations**. Dynamic closed-loop crop adaptation conditioned on early shop reveals (such as ORiginators planting Tomato into Double Pizza) has not been tested against 19S/0T under a bug-free controller.

---

## 4. WHICH RETRACTIONS ARE THEMSELVES VERIFIED

| Retraction | Underlying Fact | Audit #2 Status |
|---|---|:---:|
| **R1 (Tomato $3,942 Outlier)** | Seed 50042 gained +$3,942, but 6-seed ensemble lost -$5,382.67. All 18 parameter sweeps negative. | **FULLY VERIFIED** |
| **R2 (Shop Demand Model Errors)** | 6 of 8 shops in `shop_transition_model.py` contradicted both C++ simulator and official Kaggle rules. | **FULLY VERIFIED** |
| **R3 (Slack Capacity Experiment Invalidity)**| Test script failed to water/harvest vacant crops and hired workers daily for 18 days. | **FULLY VERIFIED** |
| **R4 (Step 696 Causality Rejection)** | Cash and physical divergence occurred at steps 164 and 217; Step 696 was an observational symptom. | **FULLY VERIFIED** |
| **R5 (V2 Superiority Claim Retraction)** | 95% CI spans `[-$2.07, +$51.30]` ($p = 0.0726$); statistical superiority is unproven. | **FULLY VERIFIED** |
| **R6 (Corrected V2-vs-Dmitrii Statistics)** | Mean +$24.61, 54.7% WR, worst loss -$730 across 150 paired seeds. Table 1 transcription error confirmed. | **FULLY VERIFIED** |

---

## 5. WHICH RETRACTIONS ARE NOT VERIFIED

- **None of the six major retractions are rejected.** Every retraction asserted by Audit #1 was directionally justified and scientifically necessary:
  - R1, R2, R3, R5, and R6 are 100% verified without reservation.
  - R4 is verified in its conclusion (Step 696 is indeed not the causal root), but clarified by Audit #2's discovery of the true causal root (the Step 217 sheep purchase failure).

---

## 6. WHICH SURVIVING FINDINGS ARE ACTUALLY SAFE

| Finding | True Safe Scope | Safety Level |
|---|---|:---:|
| **S1: Frozen Submissions** | Submissions `56146971` and `56146947` are cryptographically verified, untracked, and active. | **ABSOLUTELY SAFE** |
| **S3: MAX_ORDERS = 10** | Engine limit is 10 orders/turn. Excess orders are silently dropped. Array order determines priority. | **ABSOLUTELY SAFE** |
| **S5: 19S/0T Strawberry Dominance** | Strictly dominates all tested static crop mixtures. Adding unhedged static tomatoes monotonically destroys cash. | **SAFE (STATIC SCOPE)** |
| **S6: Simulator Mechanics** | 720 turns, uniform replacement shop sampling, weed RNG coupling, rot kinetics (1 unit/2 turns on even steps). | **ABSOLUTELY SAFE** |
| **S2: Live Loss Mechanism** | **NOT SAFE AS STATED BY AUDIT #1**. The "$800 hiring collapse" is false. The safe finding is: live losses were driven by open-loop Strawberry specialization into non-Strawberry shop draws. | **REVISED / CONDITIONAL** |
| **S4: Physical Agronomy Identity** | **NOT SAFE AS STATED BY AUDIT #1**. V2 and Dmitrii share the same base tapes, but cash shortfalls can trigger physical divergence (e.g. missing sheep for 460 turns). | **REVISED / CONDITIONAL** |

---

## 7. WHICH PREVIOUS RESULTS MUST REMAIN DISCARDED

1. **DISCARD**: The Day-11 Tomato specialization pizza gain (+3,942 coins).
2. **DISCARD**: `shop_transition_model.py` and its Markov transition matrices / Value of Information tables.
3. **DISCARD**: `research/slack_capacity_real_option_report.md` and the "impossibility theorem" asserting that no slack exists.
4. **DISCARD**: The narrative that Step 696 36-wheat truncation is the root cause of V2's losses against Dmitrii.
5. **DISCARD**: The claim that `CLOSED_LOOP_V2` is "confirmed globally superior" to Dmitrii-LB2800.
6. **DISCARD**: The narrative that live submissions suffered a "Day-12 hiring collapse ($4 \times \$200 = \$800)$".
7. **DISCARD**: The assertion that `CLOSED_LOOP_V2` and `Dmitrii-LB2800` execute 100.0% bit-for-bit identical physical agronomy.

---

## 8. CURRENT TRUSTED EVIDENCE BASE

1. **Engine Invariants**: 720 steps, 10x10 board, $3,000 starting cash, 8 shops sampled uniform with replacement from the authoritative 8-shop table, Fibonacci hiring costs (`fib(n)`), `MAX_ORDERS = 10` with zero engine priority sorting, 100-unit shed limit, crop rot kinetics (1 unit/2 turns on even steps after 4 yields), and weed RNG coupling in unpinned play.
2. **Frozen Anchors**: Submissions 56146971 and 56146947 are active and frozen with verified SHA256 checksums.
3. **V2 Performance Baseline**: V2 achieves statistical parity with Dmitrii-LB2800 (+24.61 coins, 54.7% WR, 95% CI `[-$2.07, +$51.30]`) across 150 paired CRN seeds with zero catastrophic paired losses (worst paired loss -$730).
4. **Agronomic Coupling**: Minor cash variations from early market sales can cascade into animal purchase failures (e.g. falling $3 short on Day 9), causing long-term physical tile divergence.
5. **Static Crop Landscape**: Pure 19S/0T Strawberry Bedrock strictly dominates all tested static crop mixtures.

---

## 9. OPEN QUESTIONS

1. **Closed-Loop Dynamic Slack Harvesting**: Can an adaptive policy that monitors town shop reveals on Days 3, 6, and 9 safely exploit the physical vacancies on Days 11–12 with properly watered and harvested crops without cannibalizing core strawberry revenue?
2. **Eliminating the Step 217 Cash Deficit**: If V2 adjusts its early market selling schedule to ensure cash never drops below $1,000 on Day 9, can it guarantee 100% animal purchase parity with Dmitrii and eliminate the -$730 loss on Seed 50081?
3. **True Tournament Matchmaking Rating**: What is the stable Elo rating of V2 when facing top human agents that actively manipulate market prices?

---

## 10. THE CENTRAL QUESTION ANSWERED

> **AFTER AUDITING THE AUDITOR, WHAT DO WE NOW KNOW WITH HIGH CONFIDENCE ABOUT KAGGRICULTURE AND OUR V2/DMITRII RESEARCH?**

1. **We know the exact, bit-precise rules of the game engine**: 8 shops sampled with replacement; exactly 4 demand Strawberry; 3 demand Milk; 2 demand Tomato; 2 demand Carrot; 2 demand Egg; 1 demands Wool; hiring costs are Fibonacci ($1, 1, 2, 3, 5, 8...$); market execution is strictly capped at 10 orders per turn with array-order priority; crops rot at 1 unit per 2 turns on even steps after 4 harvests; unpinned weed generation shifts town shop draws.
2. **We know that earlier claims of easy Tomato alpha were completely illusory**: Day-11 Tomato specialization on Pizza worlds was a cherry-picked single-seed anomaly (+3,942) drawn from an ensemble distribution that lost -$5,382 on average.
3. **We know that `CLOSED_LOOP_V2` achieves statistical parity with Dmitrii-LB2800 (+24.61 coins, 54.7% WR) with bounded downside (worst paired loss -$730)**, but is NOT "globally superior" as the 95% confidence interval crosses zero (`[-$2.07, +$51.30]`).
4. **We know that V2 and Dmitrii do NOT execute 100.0% identical physical agronomy**: early market sales can alter cash by just $4, causing a $500 animal purchase to fail on Day 9, which leaves an empty pasture tile for 460 turns and produces V2's worst loss.
5. **We know that live tournament losses were NOT caused by an "$800 dawn hiring collapse"**: that was a fictional narrative based on an agent heuristic and a bugged replay parser. Real live losses occurred because our submissions statically produced Strawberry on seeds where town shops demanded Tomato and Carrot.
6. **We know that our frozen live submissions (`56146971` and `56146947`) are intact, cryptographically verified, and unchanged.**
