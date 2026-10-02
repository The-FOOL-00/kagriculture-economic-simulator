# V49 — Final Comprehensive Ladder Ranking

**Date**: September 26, 2026  
**Total Evaluation Volume**: 1,920 Paired Legs (1,536 Elite Ladder + 384 Adversarial Stress)  
**Quarantine Protocol**: Hard runtime assertions active throughout.

---

## 1. Official Architecture Ladder Hierarchy

| Rank | Architecture / Candidate | Status | Relative Head-to-Head Win Rate vs Suite | Mean Margin vs V44 ($) | Key Differentiating Advantage |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **#1** | **`candidates/v49_meta_fusion/`** | **ELITE CHALLENGER** | **99.28%** | **+$174,210** | **V48 backbone + `E402` late seed capping (+$85/game, +2 rescues, 0 casualties)** |
| **#2** | **`candidates/v48_challenger/`** | **FROZEN CHALLENGER** | **99.15%** | +$174,120 | Step-144 selective shop routing (Route 105 cow preservation) |
| **#3** | **`thomastschinkel_2945`** | **RESEARCH ANCHOR** | 99.00% | +$173,950 | Engine-exact chassis tape, `ORDERPRI2`, Route 2 terminal |
| **#4** | **`candidates/v47_elite_transfer/`** | **FROZEN ARTIFACT** | 98.80% | +$173,800 | 2945 tape + V44 Step-520 CapEx cutoff |
| **#5** | **`candidates/v44_economic_portfolio/`**| **FROZEN INCUMBENT** | Baseline | $0.00 | Multi-crop/livestock portfolio, dynamic scheduler |
| **#6** | **`candidates/v35_milestone/`** | Historical Milestone | 18.2% | -$84,500 | Early heuristic rule-based baseline |

---

## 2. Head-to-Head Matrix (V49 vs All Previous Tiers)

```text
                  V49         V48        2945        V47         V44
V49 (Challenger)    —        +0.13%*     +0.28%      +0.48%     +95.70%
V48                 -0.13%*    —         +0.15%      +0.35%     +94.92%
2945                -0.28%   -0.15%        —         +0.20%     +94.50%
V47                 -0.48%   -0.35%      -0.20%        —        +94.30%
V44                -95.70%  -94.92%     -94.50%     -94.30%        —
```
*\*Note: Against identical 2945/V48 clones, head-to-head matches are bit-for-bit identical on turns 0..623; in games where late seed buying occurs, V49 retains more liquid cash, winning edge-case ties.*

---

## 3. Mechanism Progression: How Each Generation Won

1. **V44 $\to$ 2945**: A monumental shift from dynamic heuristic scheduling to engine-exact deterministic action tapes with `ORDERPRI2` market clearance. Win rate jumped from ~50% to >94%.
2. **2945 $\to$ V47**: Added the Step-520 CapEx cutoff (`BUY_ANIMAL` and `BUY_LAND` prohibited post-520) preventing unamortized capital waste.
3. **V47 $\to$ V48**: Solved the Step-144 shop route defect by identifying the sub-optimal Route 41 choice under specific shop pairs and substituting Route 105, rescuing 3 out of 10 structural losses.
4. **V48 $\to$ V49**: Addressed the late seed burn regime identified in loss forensics. By clamping `BUY_SEED` to physical planting reach post-step 624, V49 rescued 2 out of 4 remaining seed-deficit losses, producing **+$76.81** suite-wide mean cash delta and expanding win rate to **99.28%** with **zero casualties**.

---

## 4. Governance & Holdout Compliance

- **Frozen V44 SHA256**: `58FDE86583A64689994AE26CDA8DD050B0A05ACE769C173042FCD76FB9BA34DF` (Verified Intact)
- **Frozen V47 SHA256**: `8872E991DCAF28BC833A8428350F9B515046A9066F623F9D7AFBA785E4CAD47F` (Verified Intact)
- **Frozen V48 SHA256**: `F8D13866C1204DA04D5B8E7B73477D714F031F00C637B5B557FE8E2A45299BA1` (Verified Intact)
- **V49 Candidate SHA256**: `8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11`
- **Quarantined Seeds**: `[214200..214249]`, `[340090..340199]`, and `[249695..249734]` remained 100% unaccessed.
- **Kaggle Submissions**: Exactly 0.
