# V50 — Late-Game Capital Leakage & Elite-Loss Counterfactuals: Final Research Report

**Program:** Kagriculture V50 Research Program  
**Date:** 2026-09-26  
**Status:** COMPLETE  
**Final Governance Recommendation:** **`V49_RETAIN`** (Mandatory under Phase 10 Rules)  
**Quarantine Integrity:** 100% Verified (Holdouts `[214200..214249]`, `[340090..340199]`, `[249695..249734]` strictly untouched)  
**Kaggle Submissions:** Exactly 0 (Human-controlled governance strictly maintained)  

---

## Cryptographic Lineage & Candidate Manifest

| Entity | Role | Path | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| **V44** | Incumbent 1 | `candidates/v44_economic_portfolio/main.py` | `58FDE86583A64689994AE26CDA8DD050B0A05ACE769C173042FCD76FB9BA34DF` |
| **V47** | Incumbent 2 | `candidates/v47_elite_transfer/main.py` | `8872E991DCAF28BC833A8428350F9B515046A9066F623F9D7AFBA785E4CAD47F` |
| **V48** | Incumbent 3 | `candidates/v48_challenger/main.py` | `F8D13866C1204DA04D5B8E7B73477D714F031F00C637B5B557FE8E2A45299BA1` |
| **V49** | Verified Baseline | `candidates/v49_meta_fusion/main.py` | `8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11` |
| **V50** | Research Candidate | `candidates/v50_dead_action_guard/main.py` | `E3DC43B55EB0C7450CBE14A9EF212AE67B8E37E5C286B757834F259E66F1C80E` |

---

## Executive Summary

The V50 research program pursued a targeted hypothesis: that late-game terminal capital leakage—unplanted seeds, dead fertilizer purchases, and redundant market orders—could be counterfactually eliminated to reclaim lost margin and rescue losses suffered by the champion V49 candidate.

Through rigorous full-terminal paired simulations, closed-loop causal replays, and out-of-sample fresh validation across 9 opponents (6 elite and 3 adversarial), the program produced critical empirical discoveries:

1. **The Late Fertilizer "Leakage" Myth**:
   Static inspection suggested that Route 2's `BUY_PRODUCT FERTILIZER` orders at steps 649 and 697 were dead capital leakage because unit `FERTILIZE` actions cease by step 631. However, full-terminal counterfactual simulations revealed that suppressing these purchases causes a catastrophic **-$629.67 mean cash drop** and creates **4 casualties** across 64 legs. In the 2945 trading engine (Hayashi EXP239), step 649 executes `['SELL', 'FERTILIZER', 18]`, crashing market clearing prices; the subsequent buy order re-acquires inventory at the depressed price, which Route 2 re-sells at steps 650, 698, and 716-717 at higher prices. Suppressing buy orders starves the trading engine.
2. **Crop-Specific Demand Capping Failure (M5)**:
   V49's E402 mechanism pooled wheat and carrot demand. Attempting to enforce strict, unpooled individual crop caps caused a **-$94.56 mean cash drop** due to worker planting starvation. The 2945 unit choreography requires dynamic substitution between crop types depending on field accessibility.
3. **Dead Action Boundaries**:
   The 2945 chassis already switches to Route 2 at step 648 and issues 0 seed purchases after step 663. Universal blackout rules post-670 are completely inert (0 delta). Market wheat buy guards produce negative alpha (-$0.47) due to feed deficits.
4. **Governance Verdict**:
   Because no dead-action mechanism achieved a statistically significant positive cash delta without casualties, the program adheres strictly to Phase 10 Governance and formally recommends **`V49_RETAIN`**.

---

## 1. Phase 0: Independent Audit & Reconciliation

Before undertaking candidate development, an independent mathematical audit of V49 was conducted to resolve inconsistencies noted in previous reports.

### 1.1 Gate A Confidence Interval Reconciliation
In the V49 documentation, two conflicting confidence intervals were reported for the Gate A benchmark ($N=1,536$ paired legs against V44):
- Text claim: `+$76.81 (95% CI [+$72.83, +$80.79])`
- Table claim: `+$76.81 (95% CI [+$72.91, +$80.71])`

Re-simulation and statistical recalculation resolved this exactly:
- **Parametric Student's t-interval (95% CI):**
  $$\bar{\Delta} \pm t_{0.975, 1535} \times \frac{s}{\sqrt{n}} = 76.8125 \pm 1.9615 \times 1.9868 = [+\$72.911, +\$80.714]$$
- **Non-Parametric Bootstrap Interval (10,000 resamples):**
  $$[+\$72.831, +\$80.792]$$

Both intervals are mathematically valid representations of the identical underlying data distribution. The text reported the bootstrap interval while the table reported the parametric interval.

### 1.2 Verification of the Golden Property
Step-by-step state verification between V48 and V49 across 10 distinct seeds confirmed **zero state divergence** across turns 0..623. V49 preserves the entire 2945/V48 chassis with 100% bit-level fidelity until step 624.

---

## 2. Phase 1 & 2: Forensic Analysis of V49 Loss Corpus

Out of 1,536 paired benchmark legs, V49 won 1,525 games and lost exactly 11 games (**99.28% win rate**). Every single loss occurred against V44 on Route 0 (R42 Opening $\rightarrow$ EXP240 Non-Yarn Branch).

### 2.1 Complete Catalog of the 11 Losses

| Loss ID | Seed | Seat | Route | V49 Cash | V44 Cash | Margin | Regime Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **L01** | 250416 | 0 | 0 | $89,122 | $89,838 | -$716 | Regime 3: Harvest Trajectory Collision |
| **L02** | 250416 | 1 | 0 | $89,122 | $89,838 | -$716 | Regime 3: Harvest Trajectory Collision |
| **L03** | 250428 | 0 | 0 | $94,869 | $94,900 | -$31 | Regime 1: Land Cap Bottleneck |
| **L04** | 250428 | 1 | 0 | $94,740 | $94,900 | -$160 | Regime 1: Land Cap Bottleneck |
| **L05** | 250433 | 0 | 0 | $92,028 | $92,498 | -$470 | Regime 2: Animal Herd Delay |
| **L06** | 250433 | 1 | 0 | $92,028 | $92,498 | -$470 | Regime 2: Animal Herd Delay |
| **L07** | 250436 | 0 | 0 | $93,420 | $94,825 | -$1,405 | Regime 4: Early Egg Arbitrage |
| **L08** | 250436 | 1 | 0 | $93,420 | $94,825 | -$1,405 | Regime 4: Early Egg Arbitrage |
| **L09** | 250439 | 0 | 0 | $93,418 | $94,825 | -$1,407 | Regime 4: Early Egg Arbitrage |
| **L10** | 250439 | 1 | 0 | $93,418 | $94,825 | -$1,407 | Regime 4: Early Egg Arbitrage |
| **L11** | 250497 | 1 | 0 | $92,899 | $93,800 | -$901 | Regime 2: Animal Herd Delay |

### 2.2 The Four Causal Loss Regimes
1. **Regime 1: Land Cap Bottleneck (Seeds 250428, Margins -$31 to -$160)**:
   Near-parity matches where V49 lagged by 1-2 deliveries. V44 completed a final late animal product delivery while V49 held unharvested crops.
2. **Regime 2: Animal Herd Delay (Seeds 250433, 250497, Margins -$470 to -$901)**:
   Delayed cow acquisition in Route 0 caused milk yields to lag behind V44's mature herd.
3. **Regime 3: Harvest Trajectory Collision (Seed 250416, Margin -$716)**:
   Tile congestion between worker units delayed carrot deliveries to the shop by 3 turns, missing closing shop demand.
4. **Regime 4: Early Egg Arbitrage (Seeds 250436, 250439, Margins -$1,405 to -$1,407)**:
   V44 opened with a Goose acquisition at Step 36 that captured high early egg shop prices ($18-$22/egg), establishing an insurmountable macro-economic lead that tactical overlays cannot bridge.

---

## 3. Phase 3 & 4: Dead Action Mechanisms & Causal Discoveries

### 3.1 The Fertilizer Pump-and-Dump Discovery
Static inspection of action tapes identified that Route 2 issues `['BUY_PRODUCT', 'FERTILIZER', 2]` at step 649 and 697, even though all unit `FERTILIZE` actions terminate at step 631.

However, counterfactual execution revealed why this purchase exists:
- At Step 649, Route 2 executes:
  `['SELL', 'FERTILIZER', 18], ['BUY_PRODUCT', 'FERTILIZER', 2], ['SELL', 'FERTILIZER', 1], ['BUY_PRODUCT', 'FERTILIZER', 8]`
- The sale of 18 units depresses the clearing price. The buy orders immediately acquire fertilizer at the depressed clearing price.
- Route 2 subsequently sells this fertilizer at steps 650, 698, and 716-717 at higher market prices.
- Suppressing these buy orders breaks the trading engine, eliminating the subsequent sales and costing -$629.67 in cash!

### 3.2 Crop-Specific Demand Capping Failure (M5)
In V49, E402 enforced a pooled cap:
$$\text{Remaining} = \sum_{t > \text{step}} (\text{PLANT WHEAT} + \text{PLANT CARROT})$$
In candidate mechanism M5, this was partitioned into independent per-crop caps:
$$\text{Remaining}_{\text{wheat}} = \sum_{t > \text{step}} (\text{PLANT WHEAT}), \quad \text{Remaining}_{\text{carrot}} = \sum_{t > \text{step}} (\text{PLANT CARROT})$$
When evaluated across 64 paired legs against V44, M5 produced a **-$94.56 mean cash drop**. The 2945 worker choreography dynamically switches between planting wheat and carrot based on field tile proximity. Strict individual caps starved workers of seed inventory when path obstructions forced a switch, idling units for multiple turns.

---

## 4. Phase 5 & 6: Full-Terminal Paired Counterfactuals

Evaluated across 64 paired legs (32 discovery seeds $\times$ 2 seats) against V44 under full 719-step authority:

| Mechanism | Configuration | Mean $\Delta$ vs V49 | 95% Bootstrap CI | Active Legs | V49 WR | Cand WR | Casualties | Rescues |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **V49 Parity Check** | Baseline | **+$0.00** | [$0.00, $0.00] | 0 / 64 (0%) | 93.75% | 93.75% | 0 | 0 |
| **M1 Extended Seeds** | Step $\ge 624$ (Tomato/Straw/Melon) | **+$0.00** | [$0.00, $0.00] | 0 / 64 (0%) | 93.75% | 93.75% | 0 | 0 |
| **M2 Fert Guard 646** | Step $\ge 646$ Fert Buy Guard | **-$629.67** | [-$837.02, -$452.98] | 64 / 64 (100%) | 93.75% | 87.50% | **4** | 0 |
| **M2 Fert Guard 624** | Step $\ge 624$ Fert Buy Guard | **-$632.33** | [-$839.29, -$456.17] | 64 / 64 (100%) | 93.75% | 87.50% | **4** | 0 |
| **M2 Fert Guard 631** | Step $\ge 631$ Fert Buy Guard | **-$629.67** | [-$837.02, -$452.98] | 64 / 64 (100%) | 93.75% | 87.50% | **4** | 0 |
| **M3 Post-670 Blackout**| Universal Seed Blackout $\ge 670$ | **+$0.00** | [$0.00, $0.00] | 0 / 64 (0%) | 93.75% | 93.75% | 0 | 0 |
| **M4 Market Wheat Guard**| Wheat Buy Guard $\ge 648$ | **-$0.47** | [-$0.89, -$0.14] | 6 / 64 (9.4%) | 93.75% | 93.75% | 0 | 0 |
| **Composite M1+M2+M3** | Combined Guards | **-$629.67** | [-$837.02, -$452.98] | 64 / 64 (100%) | 93.75% | 87.50% | **4** | 0 |

---

## 5. Phase 9: Fresh Out-of-Sample Validation Benchmark

The fresh validation benchmark evaluated all 5 candidates across 32 strictly disjoint fresh seeds (`[250600..250631]`) against **9 opponents** (6 elite and 3 adversarial) under full 719-step rollouts (576 legs per candidate, 2,880 total match rollouts):

### 5.1 Grand Evaluation Summary (576 Legs per Candidate)

| Candidate | Mean $\Delta$ vs V49 | Median $\Delta$ | 95% Bootstrap CI | Candidate WR | V49 WR | Rescues | Casualties | Active Legs (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **V44_Incumbent** | **-$2,774.29** | -$1,264.0 | [-$3,544.03, -$1,999.90] | 89.24% | 99.31% | 0 | 58 | 576 / 576 (100.0%) |
| **V48_Challenger** | **-$64.46** | $0.0 | [-$70.87, -$58.19] | 99.31% | 99.31% | 0 | 0 | 234 / 576 (40.6%) |
| **V49_Meta_Fusion** | **+$0.00** | $0.0 | [$0.00, $0.00] | **99.31%** | 99.31% | 0 | 0 | 0 / 576 (0.0%) |
| **V50_Dead_Action_Guard** | **+$0.00** | $0.0 | [$0.00, $0.00] | **99.31%** | 99.31% | 0 | 0 | 0 / 576 (0.0%) |
| **V50_Fert_Guard_Variant**| **-$1,067.77** | -$242.0 | [-$1,225.28, -$921.15] | 97.92% | 99.31% | 0 | **8** | 404 / 576 (70.1%) |

### 5.2 Elite Suite (384 Legs) vs Adversarial Suite (192 Legs)

| Candidate | Elite Mean $\Delta$ | Elite WR | Elite Casualties | Adversarial Mean $\Delta$ | Adv WR | Adv Casualties |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **V44_Incumbent** | -$2,018.81 | 83.85% | 58 | -$4,285.25 | 100.00% | 0 |
| **V48_Challenger** | -$66.69 | 98.96% | 0 | -$60.00 | 100.00% | 0 |
| **V49_Meta_Fusion** | **+$0.00** | **98.96%** | 0 | **+$0.00** | **100.00%** | 0 |
| **V50_Dead_Action_Guard** | **+$0.00** | **98.96%** | 0 | **+$0.00** | **100.00%** | 0 |
| **V50_Fert_Guard_Variant**| -$1,242.79 | 96.88% | **8** | -$717.72 | 100.00% | 0 |

### 5.3 Key Empirical Revelations from Fresh Validation
1. **Confirmation of V49 Meta Fusion Dominance**:
   V49 maintains a statistically robust **+$64.46 mean cash superiority** over V48 out-of-sample (95% CI [+$58.19, +$70.87]). The E402 mechanism activated in 234 of 576 legs (40.6%) and achieved positive alpha against every single elite and adversarial opponent without a single casualty.
2. **Inertia of Safe Dead Action Boundaries**:
   `V50_Dead_Action_Guard` is 100% non-destructive and perfectly preserves V49's 99.31% win rate, but produces identically +$0.00 delta across all 576 legs. The 2945 chassis already switches to Route 2 at step 648 and naturally executes 0 seed purchases after step 663.
3. **Severe Downside of Fertilizer Buy Suppression**:
   `V50_Fert_Guard_Variant` drops terminal cash by **-$1,067.77** and causes **8 casualties**, confirming out-of-sample that late fertilizer purchases are vital arbitrage orders for Route 2's pump-and-dump market engine.

---

## 6. Phase 10: Promotion Rule Evaluation & Final Decision

### 6.1 Formal Governance Criteria Audit

| Promotion Criteria | Requirement | V50_Dead_Action_Guard | V50_Fert_Guard_Variant | Gate Status |
| :--- | :--- | :--- | :--- | :--- |
| **Condition 1 (Cash Delta)** | Mean Delta vs V49 $> 0$ (95% CI lower $> 0$) | +$0.00 (CI [$0.00, $0.00]) | -$1,067.77 (CI [-$1,225.28, -$921.15]) | **FAIL** |
| **Condition 2 (Win Rate)** | Candidate WR $\ge$ V49 WR (99.31%) | 99.31% (Met) | 97.92% (Failed) | **FAIL** |
| **Condition 3 (Zero Casualties)**| Exactly 0 casualties across all opponents | 0 casualties (Met) | 8 casualties (Failed) | **FAIL** |
| **Condition 4 (Adversarial)** | Zero degradation vs Adversarial Suite | 0.00 delta, 100% WR (Met) | -$717.72 delta (Failed) | **FAIL** |

### 6.2 Definitive Governance Recommendation

Under Phase 10 Governance, promotion requires strict positive alpha ($\text{lower 95% CI} > 0$) with zero casualties. Because no tested dead-action mechanism achieved a statistically significant positive cash delta over V49:

$$\mathbf{OFFICIAL \quad DECISION: \quad V49\_RETAIN}$$

1. **Incumbent Retention:** `candidates/v49_meta_fusion/main.py` (`8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11`) remains the verified champion model.
2. **Candidate Archival:** `candidates/v50_dead_action_guard/main.py` (`E3DC43B55EB0C7450CBE14A9EF212AE67B8E37E5C286B757834F259E66F1C80E`) is archived as a research artifact documenting the causal boundaries of terminal inventory and market operations.
3. **Quarantine Integrity:** Protected virgin holdouts (`214200–214249`, `340090–340199`, `249695–249734`) remain 100% uncompromised.
4. **Submission Protocol:** Exactly zero automatic Kaggle submissions were executed. Human-controlled submission protocol is preserved.
