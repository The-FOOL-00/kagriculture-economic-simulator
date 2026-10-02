# FINAL DECISION

## Incumbent
V49 (`candidates/v49_meta_fusion/main.py`)
SHA256: `8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11`

## Best teammate
Vj_kc_v24 (`team_submissions/submission_Vj_kc_v24.tar.gz`)
Archive SHA256: `4C9EF1DC189DE6185AFADE682CB8A758139390E4BAA8B6A010500443C75BD5CE`
(Proved superior to Vj_kc_v27 by +500 cash margin and 7/8 head-to-head wins due to `room_guard`, `dead_stock`, PET_CAFE tilt, and stranded wheat pickup fix).

## Best synthesized candidate
Final_Meta_Synthesis (`research/final_synthesis/final_candidate/main.py`)
SHA256: `076AB4447A198C972C6F5415A48FB6DDF7B1E3E1B8AA306783D3F2B8BD29177D`
(Integrates V24 core with de-instrumented production code, outer exception-safe wrapper, and removal of prohibited debug prints).

## Main mechanisms retained
1. Protected Incumbent Architecture: The 2945 Base Chassis + Yusuke Hayashi EXP240 shop routing.
2. V44 CapEx Safeguard: Step >= 520 capital expenditure cutoff.
3. V48 Selective Shop-Route Overrides: Route 105 for Brunch/Farmers, Bakery/Brunch, PetCafe/Farmers.
4. V49 E402 Late Seed-Cap Overlay: Strict remaining-plant upper bound on BUY_SEED after step 624.
5. In Candidate Prototype (Evaluated): Dmitrii Gluzdov HybridOpening + wheat maturation; Tetsutani room_guard & dead_stock; PET_CAFE margin tilt; S793 fixed sell reordering.

## Mechanisms rejected
1. Candidate Synthesis for Production: REJECTED due to catastrophic panel generalization failure (48.91% panel WR vs V49's 92.19%).
2. Teammate V27 Unchecked Wheat Pickup: REJECTED (stalls sheep feeding worker when shed wheat reaches 0).
3. Teammate V27 Guard Disabling: REJECTED (disabling room_guard and dead_stock cost 55.2 cash per game).
4. Prohibited Debug Stdout Hook: REJECTED (print('HP_TELEMETRY', ...) removed).
5. V50 Fertilizer Suppression: REJECTED (starves late crop yields).
6. V51 Weed Repair Replay Buffer: REJECTED (0 firings across 92,000 turns; inert on 2945).
7. V55 Dynamic Midgame Route Switching: REJECTED (causes shed saturation and crop deletion).
8. V57 Structural Market Queue Padding: REJECTED (0/4 rescues, induced casualties).

## Evidence
- 640-leg tournament gauntlet across 10 opponents on 32 fresh seeds [250600..250631] on both seats.
- Detailed step-level divergence traces (turn 0 through turn 718).
- Full ablation suite decomposing opening, guards, rescues, and demand margins.
- Bit-exact replication of V49's four historical loss worlds (seeds 250617 & 250621).

## Benchmark summary
- **V49 Incumbent across Broad Panel**:
  - Panel Win Rate: **92.19%** (413 Wins, 5 Losses, 30 Ties / 448 legs)
  - Mean Delta: **+25,028.0**
  - vs `dmitrii_lb2800`: 100.0% WR (64W / 0L, +11,809.5)
  - vs `tetsutani_pasture`: 100.0% WR (64W / 0L, +18,113.2)
  - vs `indarkarhana_top10`: 100.0% WR (64W / 0L, +25,245.3)
  - vs `kaitofukami_v48_3009`: 100.0% WR (64W / 0L, +23,399.0)
  - vs `saiteja_mega_3000`: 100.0% WR (64W / 0L, +92,921.3)
  - vs `V44`: 93.75% WR (60W / 4L, +3,624.6)
- **Final Synthesized Candidate across Broad Panel**:
  - Panel Win Rate: **48.91%** (313 Wins, 327 Losses, 0 Ties / 640 legs)
  - vs `dmitrii_lb2800`: 20.31% WR (13W / 51L, **-28,760.5**)
  - vs `tetsutani_pasture`: 34.38% WR (22W / 42L, **-16,740.8**)
  - vs `indarkarhana_top10`: 45.31% WR (29W / 35L, **-11,047.6**)
  - vs `V49`: 54.69% WR (35W / 29L, **-3,251.0**)
  - vs `V24`: 39.06% WR (25W / 39L, **-6,446.9**)
  - vs `V27`: 37.50% WR (24W / 40L, **-6,560.0**)

## Casualty summary
- Casualties on V49: Exactly 0.
- Casualties on Final Synthesized Candidate: Exactly 0.
- Unforced errors / disqualifications: Exactly 0.

## Known failure modes
- **Candidate Failure Mode**: Narrow micro-overfitting to slow opponents. The teammate's forward-selling reordering pulls sales forward and floods market bins prematurely. When matched against aggressive high-volume auction opponents (`dmitrii_lb2800`, `tetsutani_pasture`), it sells at depressed prices, surrenders late town order bonuses, and suffers massive 28k-cash deficits.
- **V49 Failure Mode**: Step 697 lockstep market queue collision against V44 on exactly 2 seeds (250617 and 250621).

## Confidence
Extremely High (Empirically verified across 1,000+ simulation matches on canonical `kaggle-environments 1.32.7` engine).

## Submission artifact
`submissions/v49_meta_fusion_submission/main.py`
and frozen control:
`research/final_synthesis/baselines/V49_FROZEN/main.py`

## SHA256
`8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11`
