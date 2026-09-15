# SLACK-CAPACITY REAL-OPTION HARVESTING: FINAL CAUSAL INVESTIGATION REPORT

**Date:** 2026-09-11
**Status:** COMPLETE (Discovery + Qualification + Fresh Holdout)
**Champion:** CLOSED_LOOP_V2 (submissions 56146971 and 56146947) -- FROZEN, UNTOUCHED

---

## EXECUTIVE SUMMARY

The slack-capacity real-option harvesting experiment has been completed across all three
statistical phases (Discovery N=100 games, Qualification N=100 games, Fresh Holdout N=100 games).

**FINAL VERDICT: Hypothesis REJECTED on all three datasets with zero exceptions.**

No additive tomato policy produces a positive paired margin versus CLOSED_LOOP_V2.
The CLOSED_LOOP_V2 production architecture is tight and load-bearing -- there is no
genuinely idle capacity available for late, information-conditioned tomato production.

---

## SECTION 1: V2 FORENSIC AUDIT (CAPACITY GROUND TRUTH)

### Tile Census (50-seed mean at Day 12)
- Strawberry: ~33 tiles (V2 backbone -- 19+ productive)
- Wheat: ~25 tiles (feeds livestock)
- Pasture: ~17 tiles (cow/sheep infrastructure)
- Empty: ~2.5 tiles (TRANSIENT REPLANTING GAPS, not slack)

All 75 NW+NE+SW tiles are load-bearing. The Day-11 spike (mean 14.75 empty) is a
synchronized strawberry-harvest + wheat-replanting gap that resolves within 1 day.

### Worker and Cash Profile (key days)
- Day 10: mean cash ,767 | shed_free 54.4 | empty tiles 4.6
- Day 11: mean cash ,068 | shed_free 43.9 | empty tiles 14.75
- Day 12: mean cash ,714 | shed_free 50.9 | empty tiles 2.5

Worker pass rate falls to 8.3-9.2 free orders/step by Day 10+ -- approaching capacity.

---

## SECTION 2: STRUCTURAL ECONOMICS OF TOMATO FAILURE

Primary killer: SE land acquisition = ,000 + ~,000 hired hand (6-8 days) = ,000 committed
Tomato revenue ceiling: 4 tiles x 3 tomatoes x  (Pizza price) x 1 harvest = ,200 max
Net best-case: ,200 - ,000 = -,800 BEFORE market impact and worker collision losses

Vacant-tile alternative: Replaces wheat (load-bearing livestock feed) -> livestock yield drop
exceeds any tomato revenue even at k=1.

---

## SECTION 3: MARGINAL VALUE CURVE V(k)

### SE Land Mode (Deploy Day 12, Discovery Seeds 50000-50049)
k=0  POLICY_A:   margin = +0.0    CI=11   WR=5.0%   (baseline -- V2 pure)
k=1  SWEEP_K_1:  margin = -5,749  CI=62   WR=0.0%
k=2  SWEEP_K_2:  margin = -5,472  CI=77   WR=0.0%
k=3  SWEEP_K_3:  margin = -5,225  CI=86   WR=0.0%
k=4  SWEEP_K_4:  margin = -4,966  CI=100  WR=0.0%
k=6  SWEEP_K_6:  margin = -5,359  CI=87   WR=0.0%
k=8  SWEEP_K_8:  margin = -6,415  CI=--   WR=0.0%
k=10 SWEEP_K_10: margin = -6,516  CI=--   WR=0.0%
VERDICT: No profitable k exists. Non-convex, deep losses throughout.

### Vacant Tiles Mode (Deploy Day 12, Discovery Seeds 50000-50049)
k=0: margin = +0.0   WR=5.0%  (baseline)
k=1: margin = -910   WR=1.0%
k=2: margin = -1,699 WR=0.0%
k=3: margin = -1,964 WR=0.0%
k=4: margin = -2,473 WR=0.0%
VERDICT: Monotonically worse with k. No profitable configuration.

---

## SECTION 4: INFORMATION-CONDITIONED POLICIES

All tested on SE Land, Deploy Day 12, N=100 games per dataset.

Policy | Logic                              | Discovery  | Qual       | Holdout
-------|------------------------------------|-----------:|----------:|--------:
POL_A  | Never deploy (baseline)            | +0.0       | (baseline) | (baseline)
POL_B  | Always k=2                         | -5,472     | --         | --
POL_C  | Always k=4                         | -4,966     | --         | --
POL_D  | Always k=6                         | -5,359     | --         | --
POL_E  | k=4 if Pizza shop                  | -1,884     | -1,587     | -2,316
POL_F  | k=4 if Pizza AND NOT Straw shops   | -350       | -229       | -118
POL_G  | k=4/2/0 Pizza + shed_free gating   | -403       | -625       | -977
POL_H  | k=2 if Pizza + tight gating        | +0.0 (NOP) | -549       | -124
vk_v1  | k=1 vacant if SWEEP                | -910       | -980       | -869

Key finding: POLICY_H was a no-op in Discovery (never fired).
In Qualification and Holdout it begins to fire, revealing negative margins
as the condition is met in some seeds.

POLICY_F showed the smallest loss magnitude (- discovery, - qual, - holdout)
but CI95 always spans zero from the negative side -- never statistically positive.

---

## SECTION 5: QUALIFICATION + HOLDOUT RESULTS (FINAL)

### Qualification (Seeds 50050-50099, N=100 games)
POLICY_F:  margin=-228.9  CI=287.7  WR=4.0%  WorstLoss=-6406  CatRate=14.0%
POLICY_G:  margin=-624.8  CI=396.9  WR=3.0%  WorstLoss=-6406  CatRate=14.0%
POLICY_E:  margin=-1586.5 CI=495.2  WR=2.0%  WorstLoss=-6406  CatRate=14.0%
POLICY_H:  margin=-549.1  CI=391.1  WR=4.0%  WorstLoss=-6406  CatRate=10.0%
vk_vac_1:  margin=-979.6  CI=185.0  WR=2.0%  WorstLoss=-7066  CatRate=12.0%

### Fresh Holdout (Seeds 50100-50149, N=100 games)
POLICY_F:  margin=-117.7  CI=166.8  WR=4.0%  WorstLoss=-5883  CatRate=12.0%
POLICY_G:  margin=-977.3  CI=436.9  WR=4.0%  WorstLoss=-6525  CatRate=12.0%
POLICY_E:  margin=-2315.8 CI=482.6  WR=1.0%  WorstLoss=-5971  CatRate=12.0%
POLICY_H:  margin=-124.0  CI=175.2  WR=4.0%  WorstLoss=-6198  CatRate=12.0%
vk_vac_1:  margin=-868.9  CI=69.2   WR=1.0%  WorstLoss=-2275  CatRate=4.0%

All negative across all three datasets. No exception. No policy achieves positive
mean margin OR positive CI95 lower bound on any dataset.

---

## SECTION 6: ROOT CAUSE ANALYSIS

1. SE LAND CAPITAL SINK (Primary): ,000 land + ,000 hired hand =  committed.
   Maximum tomato revenue in 1 harvest cycle = ~,200. Structurally unprofitable.
   Observed mean margin (-,966 for k=4) matches model prediction closely.

2. PIZZA SHOP SCARCITY (Secondary): Pizza appears in ~40% of games. Even conditional
   deployment (POLICY_E/F) cannot overcome the capital cost in 40% of games.

3. WHEAT IS LOAD-BEARING (Tertiary for vacant tiles): Vacant-tile displacement of wheat
   reduces livestock output. The livestock revenue loss exceeds tomato revenue at k=1.

4. POLICY_H WAKES UP IN QUAL/HOLDOUT: The tight-gated POLICY_H (never fires in Discovery)
   begins to fire in Qualification seeds, revealing - loss. The firing condition
   is met in some Qualification/Holdout seeds but the economics remain negative.

5. POLICY_F TRENDING TOWARD ZERO (but not crossing):
   Discovery: - | Qualification: - | Holdout: -
   This decreasing trend is NOT evidence of a positive effect -- it reflects
   different shop-world compositions across seed ranges. The holdout CI95 =
   [-284, +] -- still mostly negative.

---

## SECTION 7: FINAL DECISIONS

1. HYPOTHESIS REJECTED: No slack-capacity real-option exists for tomato production.

2. CLOSED_LOOP_V2 CONFIRMED AS CHAMPION: No modification or augmentation is warranted.

3. LIVE SUBMISSIONS FROZEN: 56146971 and 56146947 remain untouched.

4. NO FURTHER TOMATO RESEARCH AUTHORIZED under current mandate.

5. The V2 architecture is operating at near-optimal resource utilization.
   Apparent slack (Day-11 tiles, shed headroom) is structurally committed.

---

## APPENDIX: ALL RAW RESULTS

Discovery results: scratch/additive_discovery_results.json
Qualification + Holdout: scratch/qualification_and_holdout_results.json
Slack budget audit: scratch/slack_budget_summary.json
Investigation script: scratch/run_additive_investigation.py
Qualification script: scratch/run_slack_qualification.py
