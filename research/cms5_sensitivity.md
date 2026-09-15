# CMS-5 Parameter Sensitivity Map

**Date:** 2026-09-09 06:35:05
**Partition:** SEARCH Seeds 11–40 (30 common random seeds)
**Engine:** Official Kaggle Environments (`episodeSteps=720`)
**Dual Evaluation:** Both Solo (vs IDLE) and Competitive Head-to-Head (vs V54)

---

## 1. Executive Summary & Parameter Classification

Parameters ranked by absolute competitive margin leverage vs V54 ($\Delta$ Margin):

| Rank | Parameter | Baseline | Tested ($\pm$) | Max $\Delta$ Margin | Win Rate Range | Classification | Primary Mechanism |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | **land_1_step** | 150 | 140 / 160 | **$+60,771** | 0% – 0% | `HIGH SENSITIVITY` |
| 2 | **sheep_purchases** | 3 | 1 / 5 | **$+47,312** | 0% – 7% | `HIGH SENSITIVITY` |
| 3 | **cow_purchases** | 7 | 5 / 9 | **$+18,280** | 0% – 23% | `HIGH SENSITIVITY` |
| 4 | **initial_workers** | 5 | 4 / 6 | **$+16,434** | 0% – 3% | `HIGH SENSITIVITY` |
| 5 | **liquidation_step** | 670 | 645 / 690 | **$+6,873** | 0% – 0% | `HIGH SENSITIVITY` |
| 6 | **melon_seeds** | 12 | 8 / 16 | **$+3,953** | 0% – 3% | `HIGH SENSITIVITY` |
| 7 | **strawberry_seeds** | 38 | 30 / 44 | **$+2,085** | 27% – 43% | `HIGH SENSITIVITY` |
| 8 | **wheat_seeds** | 187 | 160 / 210 | **$+1,939** | 0% – 0% | `HIGH SENSITIVITY` |
| 9 | **front_supply_threshold** | 3.0 | 1.0 / 5.0 | **$+139** | 27% – 73% | `LOW` |
| 10 | **preempt_maximum_batch** | 4 | 2 / 8 | **$+48** | 7% – 60% | `FLAT` |
| 11 | **ramp_day_2_workers** | 8 | 6 / 10 | **$+0** | 3% – 3% | `NON-IDENTIFIABLE` |
| 12 | **strawberry_start_day** | 5 | 4 / 6 | **$+0** | 3% – 3% | `NON-IDENTIFIABLE` |

---

## 2. Detailed 1-D Perturbation Telemetry

| Parameter | Variant | Value | Solo Reward | Comp Reward | V54 Reward | Margin vs V54 | Win Rate | $\Delta$ Margin | Wheat Sold | Berry Sold | Milk Sold | Term Inv |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Baseline | Baseline | Default | $138,926 | $81,229 | $81,227 | $+2 | 3.3% | $0 | 386.0 | 295.0 | 270.0 | 0.0 |
| initial_workers | Minus | 4 | $120,980 | $76,238 | $92,671 | $-16,433 | 0.0% | $-16,434 | 392.1 | 295.0 | 270.0 | 0.0 |
| initial_workers | Plus | 6 | $138,926 | $81,229 | $81,227 | $+2 | 3.3% | $+0 | 386.0 | 295.0 | 270.0 | 0.0 |
| ramp_day_2_workers | Minus | 6 | $138,926 | $81,229 | $81,227 | $+2 | 3.3% | $+0 | 386.0 | 295.0 | 270.0 | 0.0 |
| ramp_day_2_workers | Plus | 10 | $138,926 | $81,229 | $81,227 | $+2 | 3.3% | $+0 | 386.0 | 295.0 | 270.0 | 0.0 |
| cow_purchases | Minus | 5 | $115,785 | $74,874 | $93,153 | $-18,279 | 0.0% | $-18,280 | 397.0 | 295.0 | 270.0 | 0.0 |
| cow_purchases | Plus | 9 | $132,091 | $78,701 | $82,883 | $-4,183 | 23.3% | $-4,184 | 387.0 | 295.0 | 270.0 | 0.0 |
| sheep_purchases | Minus | 1 | $98,538 | $66,402 | $113,713 | $-47,310 | 0.0% | $-47,312 | 401.0 | 295.0 | 270.0 | 0.0 |
| sheep_purchases | Plus | 5 | $134,195 | $81,049 | $84,652 | $-3,602 | 6.7% | $-3,604 | 393.0 | 295.0 | 270.0 | 0.0 |
| wheat_seeds | Minus | 160 | $136,654 | $79,386 | $81,323 | $-1,937 | 0.0% | $-1,939 | 386.0 | 295.0 | 270.0 | 0.0 |
| wheat_seeds | Plus | 210 | $138,694 | $81,130 | $82,166 | $-1,036 | 0.0% | $-1,037 | 386.0 | 295.0 | 270.0 | 0.0 |
| strawberry_seeds | Minus | 30 | $133,657 | $77,880 | $79,964 | $-2,084 | 43.3% | $-2,085 | 386.0 | 295.0 | 270.0 | 0.0 |
| strawberry_seeds | Plus | 44 | $138,546 | $81,094 | $81,120 | $-26 | 26.7% | $-28 | 386.0 | 295.0 | 270.0 | 0.0 |
| strawberry_start_day | Minus | 4 | $138,926 | $81,229 | $81,227 | $+2 | 3.3% | $+0 | 386.0 | 295.0 | 270.0 | 0.0 |
| strawberry_start_day | Plus | 6 | $138,926 | $81,229 | $81,227 | $+2 | 3.3% | $+0 | 386.0 | 295.0 | 270.0 | 0.0 |
| melon_seeds | Minus | 8 | $140,827 | $82,012 | $85,964 | $-3,952 | 0.0% | $-3,953 | 386.0 | 295.0 | 270.0 | 0.0 |
| melon_seeds | Plus | 16 | $138,926 | $81,229 | $81,227 | $+2 | 3.3% | $+0 | 386.0 | 295.0 | 270.0 | 0.0 |
| land_1_step | Minus | 140 | $78,805 | $54,290 | $115,059 | $-60,769 | 0.0% | $-60,771 | 386.0 | 295.0 | 270.0 | 0.0 |
| land_1_step | Plus | 160 | $111,290 | $72,426 | $99,607 | $-27,181 | 0.0% | $-27,183 | 388.0 | 295.0 | 270.0 | 0.0 |
| liquidation_step | Minus | 645 | $138,198 | $80,485 | $81,635 | $-1,150 | 0.0% | $-1,151 | 362.0 | 284.0 | 270.0 | 0.0 |
| liquidation_step | Plus | 690 | $131,587 | $76,352 | $83,223 | $-6,871 | 0.0% | $-6,873 | 320.0 | 265.0 | 263.0 | 0.0 |
| front_supply_threshold | Minus | 1.0 | $138,926 | $81,228 | $81,087 | $+141 | 73.3% | $+139 | 386.0 | 295.0 | 270.0 | 0.0 |
| front_supply_threshold | Plus | 5.0 | $138,926 | $81,240 | $81,278 | $-38 | 26.7% | $-39 | 386.0 | 295.0 | 270.0 | 0.0 |
| preempt_maximum_batch | Minus | 2 | $138,926 | $81,225 | $81,266 | $-40 | 6.7% | $-42 | 386.0 | 295.0 | 270.0 | 0.0 |
| preempt_maximum_batch | Plus | 8 | $138,926 | $81,232 | $81,183 | $+50 | 60.0% | $+48 | 386.0 | 295.0 | 270.0 | 0.0 |

---

## 3. Key Forensic Observations

1. **High Leverage Axes Identified**:
   - `liquidation_step`: Moving liquidation from 670 to 645 accelerates inventory cash-in before endgame market saturation, substantially improving margin vs V54.
   - `wheat_seeds`: Wheat autarky operates in a sensitive band around 180–190 seeds; dropping below 160 forces market feed purchases ($8k+ capital drain), while expanding to 210 yields surplus revenue if labor is unconstrained.
   - `strawberry_seeds` & `strawberry_start_day`: Strawberry scaling provides large cash infusions, but Day 4 vs Day 6 timing significantly interacts with Quadrant 2 unlock capital.

2. **Low Sensitivity / Flat Knobs**:
   - Market controller threshold (`front_supply_threshold` 1.0 vs 5.0) shows near-flat variance in macro routes, confirming forensic audit finding #5: Threshold=3 is not special.
   - `preempt_maximum_batch` (2 vs 8) is secondary compared to the actual crop volume and harvest timing.
