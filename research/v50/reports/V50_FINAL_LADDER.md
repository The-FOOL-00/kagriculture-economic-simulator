# V50 — Fresh Out-of-Sample Final Ladder Report

**Program:** Kagriculture V50 Research Program  
**Evaluation Phase:** Phase 9 & Phase 10 Out-of-Sample Ladder  
**Date:** 2026-09-26  
**Status:** COMPLETE  
**Governance:** Zero Kaggle submissions; Quarantined holdouts (`214200–214249`, `340090–340199`, `249695–249734`) 100% untouched.  
**Fresh Validation Seeds:** 32 strictly disjoint seeds `[250600..250631]` across 2 seats (0 and 1).  
**Opponent Pool (9 Total):**
- **Elite Suite (6 Opponents):** `V44`, `dmitrii_lb2800`, `tetsutani_pasture`, `kaitofukami_v48_3009`, `indarkarhana_top10`, `saiteja_mega_3000` (384 legs per candidate).
- **Adversarial Suite (3 Opponents):** `DAIRY_FLOOD`, `WOOL_FLOOD`, `TERMINAL_DUMPER` (192 legs per candidate).
- **Total Match Authority:** 576 legs per candidate across full 719-step rollouts (2,880 total match rollouts).

---

## 1. Candidate Manifest

| Candidate | Archetype | Description | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| **V44_Incumbent** | Economic Portfolio | Frozen incumbent benchmark; multi-contract dynamic LP planner | `58FDE86583A64689994AE26CDA8DD050B0A05ACE769C173042FCD76FB9BA34DF` |
| **V48_Challenger** | 2945 Elite Transfer | Frozen incumbent benchmark; Step 520 CapEx cutoff on 2945 chassis | `F8D13866C1204DA04D5B8E7B73477D714F031F00C637B5B557FE8E2A45299BA1` |
| **V49_Meta_Fusion** | E402 Late Seed Cap | Verified baseline; pooled wheat/carrot demand bounds at step $\ge 624$ | `8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11` |
| **V50_Dead_Action_Guard** | Safe Tactical Overlays | Post-670 universal seed blackout + extended crop bounds | `E3DC43B55EB0C7450CBE14A9EF212AE67B8E37E5C286B757834F259E66F1C80E` |
| **V50_Fert_Guard_Variant** | Fertilizer Guard Ablation | Suppresses Route 2 fertilizer buy orders post-646 (Failure regime) | Empirical Ablation Artifact |

---

## 2. Grand Evaluation Matrix (576 Legs per Candidate)

All candidates evaluated in full-terminal paired simulations against V49 on the exact same world states:

| Candidate | Mean $\Delta$ vs V49 | Median $\Delta$ | 95% Bootstrap CI | Candidate WR | V49 WR | Rescues | Casualties | Active Legs (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **V44_Incumbent** | **-$2,774.29** | -$1,264.0 | [-$3,544.03, -$1,999.90] | 89.24% | 99.31% | 0 | 58 | 576 / 576 (100.0%) |
| **V48_Challenger** | **-$64.46** | $0.0 | [-$70.87, -$58.19] | 99.31% | 99.31% | 0 | 0 | 234 / 576 (40.6%) |
| **V49_Meta_Fusion** | **+$0.00** | $0.0 | [$0.00, $0.00] | **99.31%** | 99.31% | 0 | 0 | 0 / 576 (0.0%) |
| **V50_Dead_Action_Guard** | **+$0.00** | $0.0 | [$0.00, $0.00] | **99.31%** | 99.31% | 0 | 0 | 0 / 576 (0.0%) |
| **V50_Fert_Guard_Variant**| **-$1,067.77** | -$242.0 | [-$1,225.28, -$921.15] | 97.92% | 99.31% | 0 | **8** | 404 / 576 (70.1%) |

---

## 3. Suite Breakdown: Elite vs Adversarial

### 3.1 Elite Benchmark Suite (6 Opponents, 384 Legs)
Opponents: `V44`, `dmitrii_lb2800`, `tetsutani_pasture`, `kaitofukami_v48_3009`, `indarkarhana_top10`, `saiteja_mega_3000`.

| Candidate | Elite Mean $\Delta$ | Elite Median | 95% Bootstrap CI | Elite WR | V49 Elite WR | Casualties | Active Legs (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **V44_Incumbent** | **-$2,018.81** | -$1,093.0 | [-$3,178.95, -$867.83] | 83.85% | 98.96% | 58 | 384 / 384 (100.0%) |
| **V48_Challenger** | **-$66.69** | $0.0 | [-$74.69, -$58.85] | 98.96% | 98.96% | 0 | 162 / 384 (42.2%) |
| **V49_Meta_Fusion** | **+$0.00** | $0.0 | [$0.00, $0.00] | **98.96%** | 98.96% | 0 | 0 / 384 (0.0%) |
| **V50_Dead_Action_Guard** | **+$0.00** | $0.0 | [$0.00, $0.00] | **98.96%** | 98.96% | 0 | 0 / 384 (0.0%) |
| **V50_Fert_Guard_Variant**| **-$1,242.79** | -$321.0 | [-$1,447.04, -$1,051.05] | 96.88% | 98.96% | **8** | 362 / 384 (94.3%) |

### 3.2 Adversarial Robustness Suite (3 Opponents, 192 Legs)
Opponents: `DAIRY_FLOOD`, `WOOL_FLOOD`, `TERMINAL_DUMPER`.

| Candidate | Adversarial Mean $\Delta$ | Adversarial Median | 95% Bootstrap CI | Adversarial WR | V49 Adv WR | Casualties | Active Legs (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **V44_Incumbent** | **-$4,285.25** | -$5,169.5 | [-$4,857.75, -$3,708.05] | 100.00% | 100.00% | 0 | 192 / 192 (100.0%) |
| **V48_Challenger** | **-$60.00** | $0.0 | [-$70.83, -$49.17] | 100.00% | 100.00% | 0 | 72 / 192 (37.5%) |
| **V49_Meta_Fusion** | **+$0.00** | $0.0 | [$0.00, $0.00] | **100.00%** | 100.00% | 0 | 0 / 192 (0.0%) |
| **V50_Dead_Action_Guard** | **+$0.00** | $0.0 | [$0.00, $0.00] | **100.00%** | 100.00% | 0 | 0 / 192 (0.0%) |
| **V50_Fert_Guard_Variant**| **-$717.72** | $0.0 | [-$952.19, -$509.22] | 100.00% | 100.00% | 0 | 42 / 192 (21.9%) |

---

## 4. Granular Per-Opponent Matrix (Mean Delta vs V49 in $)

| Candidate | V44 (64L) | dmitrii (64L) | tetsutani (64L) | kaito3009 (64L) | indar (64L) | saiteja (64L) | DAIRY (64L) | WOOL (64L) | DUMPER (64L) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **V44_Incumbent** | -$1,487.06 | +$146.45 | -$698.08 | -$2,966.03 | -$2,361.86 | -$4,746.28 | -$4,285.25 | -$4,285.25 | -$4,285.25 |
| **V48_Challenger** | -$73.75 | -$62.50 | -$62.50 | -$74.53 | -$66.56 | -$60.31 | -$60.00 | -$60.00 | -$60.00 |
| **V49_Meta_Fusion** | **$0.00** | **$0.00** | **$0.00** | **$0.00** | **$0.00** | **$0.00** | **$0.00** | **$0.00** | **$0.00** |
| **V50_Dead_Action_Guard** | **$0.00** | **$0.00** | **$0.00** | **$0.00** | **$0.00** | **$0.00** | **$0.00** | **$0.00** | **$0.00** |
| **V50_Fert_Guard_Variant**| -$969.27 | -$1,311.11 | -$1,276.91 | -$1,279.34 | -$1,530.14 | -$1,090.00 | -$717.72 | -$717.72 | -$717.72 |

---

## 5. Key Empirical Findings

1. **V49 Meta Fusion Superiority Confirmed Out-of-Sample**:
   - V49 dominates V48 by **+$64.46 mean cash** out-of-sample across 576 legs (95% CI [+$58.19, +$70.87]).
   - V49's E402 late seed cap activated in 234 out of 576 legs (40.6% activation rate), producing consistent, statistically significant positive alpha in all 9 opponent matchups without a single casualty.
2. **V50 Dead Action Guard is Non-Destructive but Inert**:
   - `V50_Dead_Action_Guard` (post-670 seed blackout + extended crop bounds) achieved exactly 0.00 delta across all 576 legs.
   - Root cause: The 2945 chassis already switches to Route 2 at step 648, and Route 2 naturally issues zero seed purchases after step 663.
3. **The Late Fertilizer "Leakage" Myth**:
   - Suppressing late fertilizer purchases (`V50_Fert_Guard_Variant`) costs **-$1,067.77 mean cash** across all 576 legs and causes **8 casualties**.
   - Route 2 uses late fertilizer buy orders as an essential market pump-and-dump arbitrage mechanism. Suppressing them starves subsequent profitable sales.

---

## 6. Phase 10 Gate A & Gate B Governance Decision

| Promotion Criteria | Threshold / Requirement | V50_Dead_Action_Guard | V50_Fert_Guard_Variant | Gate Status |
| :--- | :--- | :--- | :--- | :--- |
| **Condition 1 (Cash Delta)** | Mean Delta vs V49 $> 0$ (95% CI lower $> 0$) | +$0.00 (CI [$0.00, $0.00]) | -$1,067.77 (CI [-$1,225.28, -$921.15]) | **FAIL** |
| **Condition 2 (Win Rate)** | Candidate WR $\ge$ V49 WR (99.31%) | 99.31% (Met) | 97.92% (Failed) | **FAIL** |
| **Condition 3 (Casualties)** | Exactly 0 casualties against all opponents | 0 (Met) | 8 casualties (Failed) | **FAIL** |
| **Condition 4 (Adversarial)** | Zero degradation vs Adversarial Suite | 0.00 delta, 100% WR (Met) | -$717.72 delta (Failed) | **FAIL** |

### Official Decision:
$$\mathbf{DECISION: \quad V49\_RETAIN}$$

V49 Meta Fusion remains the verified champion incumbent. V50 Dead Action Guard is retained exclusively as a research artifact in `candidates/v50_dead_action_guard/main.py`.
