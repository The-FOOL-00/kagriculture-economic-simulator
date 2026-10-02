# AEC PHASE 013: GROUP 3 RESCUE REPLAY LEDGER

**Phase**: 013 — Group 3 Mechanism Rescue  
**Date**: September 19, 2026  
**Empirical Control**: Live Foundation (`V3` + `DEPENDENCY_AWARE_MARKET_TIMING` + `TERMINAL_LIQUIDATION` + `PHASE_SHUTDOWN`)  
**Chassis SHA256**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Protocol**: Paired Common Random Numbers (CRN), Symmetric Mirror Seats ($S_0$ and $S_1$), Exact Counterfactual Simulator  

---

## 1. Governance & Cohort Verification (§1, §2, §38)

- **Protected Cohorts Intact**:
  - Primary Locked Holdout (`340050..340199`): ZERO touches verified.
  - Gate 0.3 Virgin Final Holdout (`214200..214249`): ZERO touches verified.
  - Prospective Tournament Cohort (`340300..340349`): ZERO touches verified.
- **Retired / Consumed Development Cohorts**:
  - Retired (`50000..50024`, `249000..249049`): ZERO re-use.
  - Phase 010/010B (`249050..249110`): ZERO re-use.
  - Phase 011 Group 1 (`249111..249170`): ZERO re-use.
  - Phase 012 Group 2 (`249171..249230`): ZERO re-use.
- **Certified Fresh Cohort Partition for Group 3**:
  - Pilot Cohort: Seeds `249231..249240` (10 seeds, 20 mirror matches per mechanism)
  - Formal Q1 Reserved: Seeds `249241..249265` (25 seeds, 50 matches)
  - Formal Q2 Reserved: Seeds `249266..249290` (25 seeds, 50 matches)

---

## 2. Experimental Ledger by Mechanism

### 2.1 SHOP_ARBITRAGE (Realizable Market Arbitrage)

- **Control**: Live Foundation (`ctrl_cfg`)
- **Treatment**: Control + `SHOP_ARBITRAGE` (`trt_cfg`)
- **Seeds Evaluated**: `249231..249240` (N=10 seeds, 20 matches)
- **Results File**: `results/PHASE013_SHOP_ARBITRAGE_PILOT_MATCHES.csv`

| Seed | Seat 0 Margin | Seat 1 Margin | Paired Net Delta | Target Commits | Foundation Commits | Match Win/Loss/Tie |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 249231 | -$65,239 | -$65,239 | -$65,239.0 | 72 | 4 | 0W - 2L - 0T |
| 249232 | -$40,913 | -$40,913 | -$40,913.0 | 144 | 2 | 0W - 2L - 0T |
| 249233 | -$392 | -$392 | -$392.0 | 10 | 2 | 0W - 2L - 0T |
| 249234 | -$82,292 | -$82,292 | -$82,292.0 | 134 | 0 | 0W - 2L - 0T |
| 249235 | -$68,288 | -$68,288 | -$68,288.0 | 76 | 2 | 0W - 2L - 0T |
| 249236 | -$52,990 | -$54,883 | -$53,936.5 | 112 | 2 | 0W - 2L - 0T |
| 249237 | -$47,240 | -$47,240 | -$47,240.0 | 100 | 2 | 0W - 2L - 0T |
| 249238 | -$50,554 | -$50,554 | -$50,554.0 | 130 | 2 | 0W - 2L - 0T |
| 249239 | -$65,072 | -$65,072 | -$65,072.0 | 72 | 2 | 0W - 2L - 0T |
| 249240 | -$71,333 | -$71,333 | -$71,333.0 | 104 | 2 | 0W - 2L - 0T |

#### Statistical Summary
- **Mean Paired Delta**: -$54,525.95 USD
- **Median Paired Delta**: -$59,504.25 USD
- **Standard Error**: $7,190.90
- **95% Confidence Interval**: [-$68,620.12, -$40,431.78]
- **Paired t-statistic**: -7.583 ($p < 0.0001$)
- **Match Record**: 0 Wins - 20 Losses - 0 Ties
- **Seed Record**: 0 Wins - 10 Losses - 0 Ties
- **Target Commits**: 954 commits across 24,236 candidates (Commit Rate: 3.94%)
- **Active Seeds**: 10 / 10 (100.0%)
- **Downside Tail**: Min Delta -$82,292.00, Worst 10% -$72,428.90
- **Mean Latency**: 87.94 ms (Max: 504.95 ms)

#### Causal Forensic Analysis
The mechanism recognized gross price differentials across commodities and 72-step shop unlocks, executing 954 commits. However, spending cash to purchase market products created severe working capital depletion. V3 relies on rapid cash re-investment into high-margin seeds (melon, pumpkin) and worker hiring. Tying up liquidity in speculative commodity arbitrage repeatedly starved V3's macro planting schedules, leading to catastrophic crop cycle collapse (-$54.5k mean loss).
**Decision Gate**: FAILED. Does NOT advance to Formal Qualification. Classified: `FAILED / QUARANTINED`.

---

### 2.2 PRODUCTION_ARBITRAGE (Marginal Production Opportunity)

- **Control**: Live Foundation (`ctrl_cfg`)
- **Treatment**: Control + `PRODUCTION_ARBITRAGE` (`trt_cfg`)
- **Seeds Evaluated**: `249231..249240` (N=10 seeds, 20 matches)
- **Results File**: `results/PHASE013_PRODUCTION_ARBITRAGE_PILOT_MATCHES.csv`

| Seed | Seat 0 Margin | Seat 1 Margin | Paired Net Delta | Target Commits | Foundation Commits | Match Win/Loss/Tie |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 249231 | +$0 | +$0 | +$0.0 | 0 | 4 | 0W - 0L - 2T |
| 249232 | +$0 | +$0 | +$0.0 | 0 | 2 | 0W - 0L - 2T |
| 249233 | +$0 | +$0 | +$0.0 | 0 | 2 | 0W - 0L - 2T |
| 249234 | +$0 | +$0 | +$0.0 | 0 | 2 | 0W - 0L - 2T |
| 249235 | +$14 | +$14 | +$14.0 | 0 | 2 | 2W - 0L - 0T |
| 249236 | +$11 | +$11 | +$11.0 | 0 | 4 | 2W - 0L - 0T |
| 249237 | +$0 | +$0 | +$0.0 | 0 | 2 | 0W - 0L - 2T |
| 249238 | +$12 | +$12 | +$12.0 | 0 | 4 | 2W - 0L - 0T |
| 249239 | +$12 | +$12 | +$12.0 | 0 | 2 | 2W - 0L - 0T |
| 249240 | +$0 | +$0 | +$0.0 | 0 | 2 | 0W - 0L - 2T |

#### Statistical Summary
- **Mean Paired Delta**: +$4.90 USD
- **Median Paired Delta**: +$0.00 USD
- **Standard Error**: $2.01
- **95% Confidence Interval**: [+$0.95, +$8.85]
- **Paired t-statistic**: +2.433
- **Match Record**: 8 Wins - 0 Losses - 12 Ties
- **Seed Record**: 4 Wins - 0 Losses - 6 Ties
- **Target Commits**: 0 commits across 25,870 candidates (Commit Rate: 0.00%)
- **Active Seeds**: 0 / 10 (0.0%)
- **Downside Tail**: Min Delta +$0.00, Worst 10% +$0.00
- **Mean Latency**: 120.08 ms (Max: 645.00 ms)

#### Causal Forensic Analysis
The second-generation detector evaluated 25,870 candidates across all 20 matches. In every single natural game turn, V3's macro planning layer was already planning the economically optimal crop and seed acquisitions (`ALREADY_CAPTURED_BY_BACKBONE`). Under rigorous §13-§17 gating, when V3 already captures the decision, the mechanism abstains. The small observed mean delta (+4.90) is pure non-causal foundation variance (the mechanism made 0 commits). Zero headroom was discovered in live gameplay.
**Decision Gate**: DORMANT. Does NOT advance to Formal Qualification. Classified: `FUNCTIONALLY COMPLETE / DORMANT`.

---

### 2.3 TERMINAL_CONVERSION (Realizable Terminal Value Conversion)

- **Control**: Live Foundation (`ctrl_cfg`)
- **Treatment**: Control + `TERMINAL_CONVERSION` (`trt_cfg`)
- **Seeds Evaluated**: `249231..249240` (N=10 seeds, 20 matches)
- **Results File**: `results/PHASE013_TERMINAL_CONVERSION_PILOT_MATCHES.csv`

| Seed | Seat 0 Margin | Seat 1 Margin | Paired Net Delta | Target Commits | Foundation Commits | Match Win/Loss/Tie |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 249231 | +$0 | +$0 | +$0.0 | 0 | 4 | 0W - 0L - 2T |
| 249232 | -$21 | -$21 | -$21.0 | 2 | 2 | 0W - 2L - 0T |
| 249233 | +$0 | +$0 | +$0.0 | 0 | 2 | 0W - 0L - 2T |
| 249234 | +$0 | +$0 | +$0.0 | 0 | 2 | 0W - 0L - 2T |
| 249235 | +$0 | +$0 | +$0.0 | 0 | 4 | 0W - 0L - 2T |
| 249236 | +$0 | +$0 | +$0.0 | 0 | 6 | 0W - 0L - 2T |
| 249237 | +$0 | +$0 | +$0.0 | 0 | 2 | 0W - 0L - 2T |
| 249238 | -$15 | -$15 | -$15.0 | 2 | 6 | 0W - 2L - 0T |
| 249239 | +$0 | +$0 | +$0.0 | 0 | 4 | 0W - 0L - 2T |
| 249240 | +$0 | +$0 | +$0.0 | 0 | 2 | 0W - 0L - 2T |

#### Statistical Summary
- **Mean Paired Delta**: -$3.60 USD
- **Median Paired Delta**: +$0.00 USD
- **Standard Error**: $2.44
- **95% Confidence Interval**: [-$8.38, +$1.18]
- **Paired t-statistic**: -1.475
- **Match Record**: 0 Wins - 4 Losses - 16 Ties
- **Seed Record**: 0 Wins - 2 Losses - 8 Ties
- **Target Commits**: 4 commits across 1,046 candidates (Commit Rate: 0.38%)
- **Active Seeds**: 2 / 10 (20.0%)
- **Downside Tail**: Min Delta -$21.00, Worst 10% -$15.60
- **Mean Latency**: 108.82 ms (Max: 585.43 ms)

#### Causal Forensic Analysis
In 8 out of 10 seeds, the mechanism correctly verified that `TERMINAL_LIQUIDATION` (direct sale of raw inventory) dominates conversion after factoring transit turns, processing latency, and worker availability, resulting in clean zero-commit abstention. In seeds 249232 and 249238, four terminal conversions were committed (wheat to wool/milk), consuming worker transit turns right before cutoff. Because worker movement diverted attention from terminal harvest sweeps, the net terminal reward decreased by -$21 and -$15.
**Decision Gate**: FAILED. Does NOT advance to Formal Qualification. Classified: `FUNCTIONALLY COMPLETE / QUARANTINED`.

---

### 2.4 EMERGENCY_FEED_PURCHASE (Irreversible Feed Failure Avoidance)

- **Control**: Live Foundation (`ctrl_cfg`)
- **Treatment**: Control + `EMERGENCY_FEED_PURCHASE` (`trt_cfg`)
- **Seeds Evaluated**: `249231..249240` (N=10 seeds, 20 matches)
- **Results File**: `results/PHASE013_EMERGENCY_FEED_PURCHASE_PILOT_MATCHES.csv`

| Seed | Seat 0 Margin | Seat 1 Margin | Paired Net Delta | Target Commits | Foundation Commits | Match Win/Loss/Tie |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 249231 | +$0 | +$0 | +$0.0 | 0 | 4 | 0W - 0L - 2T |
| 249232 | +$0 | +$0 | +$0.0 | 0 | 2 | 0W - 0L - 2T |
| 249233 | +$0 | +$0 | +$0.0 | 0 | 2 | 0W - 0L - 2T |
| 249234 | +$0 | +$0 | +$0.0 | 0 | 2 | 0W - 0L - 2T |
| 249235 | +$0 | +$0 | +$0.0 | 0 | 4 | 0W - 0L - 2T |
| 249236 | +$0 | +$0 | +$0.0 | 0 | 6 | 0W - 0L - 2T |
| 249237 | +$0 | +$0 | +$0.0 | 0 | 2 | 0W - 0L - 2T |
| 249238 | +$0 | +$0 | +$0.0 | 0 | 6 | 0W - 0L - 2T |
| 249239 | +$0 | +$0 | +$0.0 | 0 | 4 | 0W - 0L - 2T |
| 249240 | +$0 | +$0 | +$0.0 | 0 | 2 | 0W - 0L - 2T |

#### Statistical Summary
- **Mean Paired Delta**: +$0.00 USD
- **Median Paired Delta**: +$0.00 USD
- **Standard Error**: $0.00
- **95% Confidence Interval**: [+$0.00, +$0.00]
- **Paired t-statistic**: 0.000
- **Match Record**: 0 Wins - 0 Losses - 20 Ties
- **Seed Record**: 0 Wins - 0 Losses - 10 Ties
- **Target Commits**: 0 commits across 416 candidates (Commit Rate: 0.00%)
- **Active Seeds**: 0 / 10 (0.0%)
- **Downside Tail**: Min Delta +$0.00, Worst 10% +$0.00
- **Mean Latency**: 108.42 ms (Max: 697.89 ms)

#### Causal Forensic Analysis
The second-generation engine enforces irreversible feed failure avoidance (§25, §29), triggering only when `consecutive_unfed >= 2` or irreversible livestock death is projected. In all 416 candidates evaluated across 20 matches, natural gameplay under the frozen V3 chassis maintained safe feed levels without emergency intervention (`rejection_reason = "Baseline continuation maintains safe feed"`). The detector evaluated alternative pathways (`BASELINE_SAFE`), correctly abstained 100% of the time, and avoided unnecessary cash expenditure.
**Decision Gate**: DORMANT. Does NOT advance to Formal Qualification. Per §44: Classified: `FUNCTIONALLY COMPLETE / DORMANT`.

---

## 3. Summary of Pilot Outcomes & Promotion Decisions

| Mechanism | Pilot N | Formal N | Mean Delta | Median | Seed W/L/T | Commits | Final Status | Live? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| `SHOP_ARBITRAGE` | 10 | 0 | -$54,525.95 | -$59,504.25 | 0W / 10L / 0T | 954 / 24,236 | `FAILED / QUARANTINED` | NO |
| `PRODUCTION_ARBITRAGE` | 10 | 0 | +$4.90 | +$0.00 | 4W / 0L / 6T | 0 / 25,870 | `FUNCTIONALLY COMPLETE / DORMANT` | NO |
| `TERMINAL_CONVERSION` | 10 | 0 | -$3.60 | +$0.00 | 0W / 2L / 8T | 4 / 1,046 | `FUNCTIONALLY COMPLETE / QUARANTINED` | NO |
| `EMERGENCY_FEED_PURCHASE` | 10 | 0 | +$0.00 | +$0.00 | 0W / 0L / 10T | 0 / 416 | `FUNCTIONALLY COMPLETE / DORMANT` | NO |

**Conclusion**: In strict accordance with §36 and §39, no mechanism demonstrated an individually promising positive active delta. Consequently, zero mechanisms advance to formal qualification or live deployment.
