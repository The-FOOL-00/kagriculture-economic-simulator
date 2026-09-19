# PHASE 014: ORACLE REPLAY LEDGER

**Phase**: 014 — AEC Economic Headroom Audit  
**Date**: September 19, 2026  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Protocol**: Paired Common Random Numbers (CRN), Symmetric Mirror Seats ($S_0, S_1$), Exact Counterfactual Simulator  
**Empirical Control**: Live Foundation (`V3` + `DEPENDENCY_AWARE_MARKET_TIMING` + `TERMINAL_LIQUIDATION` + `PHASE_SHUTDOWN`)  
**Baseline Reference**: Frozen Raw V3  

---

## 1. Governance & Cohort Verification (§1, §2, §27)

- **Protected Cohorts Intact**:
  - Primary Locked Holdout (`340050..340199`): ZERO touches verified.
  - Gate 0.3 Virgin Final Holdout (`214200..214249`): ZERO touches verified.
  - Prospective Tournament Cohort (`340300..340349`): ZERO touches verified.
- **Retired / Consumed Development Cohorts**:
  - Retired (`50000..50024`, `249000..249049`): ZERO re-use.
  - Phase 010/010B (`249050..249110`): ZERO re-use.
  - Phase 011 Group 1 (`249111..249170`): ZERO re-use.
  - Phase 012 Group 2 (`249171..249230`): ZERO re-use.
  - Phase 013 Group 3 Pilot (`249231..249240`): ZERO re-use.
- **Certified Fresh Cohort Partition for Phase 014**:
  - **Diagnostic Block 1**: Seeds `249241..249250` (N=10 seeds, 20 mirror matches)
  - **Expanded Audit Block**: Seeds `249251..249275` (N=25 seeds, 50 mirror matches)
  - Total Census: 35 unique seeds, 70 mirror matches, 50,330 turns.

---

## 2. Seed-by-Seed Replay Ledger

### 2.1 Diagnostic Block 1 (Seeds 249241..249250, N=10 seeds)
Results File: `results/PHASE014_AUDIT_MATCHES.csv`

| Seed | Seat 0 Margin | Seat 1 Margin | Paired Delta | Match W/L/T | States Probed | Positive States | Mean Headroom |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 249241 | +$186.0 | +$186.0 | +$186.0 | 2W - 0L - 0T | 364 | 291 | $215.40 |
| 249242 | +$206.0 | +$206.0 | +$206.0 | 2W - 0L - 0T | 364 | 298 | $230.12 |
| 249243 | -$18.0 | -$18.0 | -$18.0 | 0W - 2L - 0T | 364 | 284 | $185.20 |
| 249244 | +$109.0 | +$109.0 | +$109.0 | 2W - 0L - 0T | 364 | 295 | $221.80 |
| 249245 | -$7.0 | -$7.0 | -$7.0 | 0W - 2L - 0T | 364 | 279 | $179.60 |
| 249246 | +$180.0 | +$180.0 | +$180.0 | 2W - 0L - 0T | 364 | 292 | $218.40 |
| 249247 | +$12.0 | +$12.0 | +$12.0 | 2W - 0L - 0T | 364 | 288 | $192.10 |
| 249248 | +$0.0 | +$0.0 | +$0.0 | 0W - 0L - 2T | 364 | 285 | $188.70 |
| 249249 | +$24.0 | +$24.0 | +$24.0 | 2W - 0L - 0T | 364 | 294 | $210.30 |
| 249250 | +$32.0 | +$32.0 | +$32.0 | 2W - 0L - 0T | 364 | 298 | $289.00 |

#### Diagnostic Block 1 Summary:
- **Mean Paired Delta**: **+$72.40 USD**
- **Median Paired Delta**: **+$28.00 USD**
- **Standard Deviation**: $88.83 USD
- **Seed Record**: 7 Wins - 2 Losses - 1 Tie (70.0% Win Rate)
- **Match Record**: 14 Wins - 4 Losses - 2 Ties (70.0% Win Rate)
- **Probed States**: 3,640 states | **Positive Headroom States**: 2,904 (79.78%)
- **Mean Oracle Headroom**: **$213.06 USD** | **Max**: $17,613.00 USD

---

### 2.2 Expanded Audit Block (Seeds 249251..249275, N=25 seeds)

| Seed | Seat 0 Margin | Seat 1 Margin | Paired Delta | Match W/L/T | States Probed | Positive States | Mean Headroom |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 249251 | -$24.0 | -$24.0 | -$24.0 | 0W - 2L - 0T | 364 | 288 | $175.40 |
| 249252 | -$2.0 | -$2.0 | -$2.0 | 0W - 2L - 0T | 364 | 282 | $180.10 |
| 249253 | +$74.0 | +$74.0 | +$74.0 | 2W - 0L - 0T | 364 | 296 | $194.20 |
| 249254 | -$58.0 | -$58.0 | -$58.0 | 0W - 2L - 0T | 364 | 275 | $162.80 |
| 249255 | +$110.0 | +$110.0 | +$110.0 | 2W - 0L - 0T | 364 | 301 | $215.60 |
| 249256 | +$112.0 | +$112.0 | +$112.0 | 2W - 0L - 0T | 364 | 299 | $210.40 |
| 249257 | +$280.0 | +$1,142.0 | +$711.0 | 2W - 0L - 0T | 364 | 312 | $345.80 |
| 249258 | +$411.0 | +$411.0 | +$411.0 | 2W - 0L - 0T | 364 | 308 | $285.40 |
| 249259 | -$22.0 | -$22.0 | -$22.0 | 0W - 2L - 0T | 364 | 280 | $171.20 |
| 249260 | +$116.0 | +$116.0 | +$116.0 | 2W - 0L - 0T | 364 | 295 | $198.50 |
| 249261 | +$25.0 | +$25.0 | +$25.0 | 2W - 0L - 0T | 364 | 290 | $188.40 |
| 249262 | +$135.0 | +$135.0 | +$135.0 | 2W - 0L - 0T | 364 | 302 | $205.10 |
| 249263 | +$16.0 | +$250.0 | +$133.0 | 2W - 0L - 0T | 364 | 298 | $202.80 |
| 249264 | -$9.0 | -$9.0 | -$9.0 | 0W - 2L - 0T | 364 | 284 | $179.30 |
| 249265 | +$125.0 | +$125.0 | +$125.0 | 2W - 0L - 0T | 364 | 300 | $204.60 |
| 249266 | +$103.0 | +$103.0 | +$103.0 | 2W - 0L - 0T | 364 | 296 | $196.70 |
| 249267 | +$131.0 | +$131.0 | +$131.0 | 2W - 0L - 0T | 364 | 299 | $208.20 |
| 249268 | +$119.0 | +$119.0 | +$119.0 | 2W - 0L - 0T | 364 | 297 | $201.50 |
| 249269 | -$24.0 | +$196.0 | +$86.0 | 1W - 1L - 0T | 364 | 292 | $193.40 |
| 249270 | +$20.0 | +$20.0 | +$20.0 | 2W - 0L - 0T | 364 | 289 | $185.90 |
| 249271 | -$26.0 | -$26.0 | -$26.0 | 0W - 2L - 0T | 364 | 281 | $174.60 |
| 249272 | +$14.0 | +$14.0 | +$14.0 | 2W - 0L - 0T | 364 | 288 | $184.20 |
| 249273 | +$11.0 | +$11.0 | +$11.0 | 2W - 0L - 0T | 364 | 287 | $182.10 |
| 249274 | +$58.0 | +$58.0 | +$58.0 | 2W - 0L - 0T | 364 | 294 | $191.80 |
| 249275 | -$2,446.0 | +$2,306.0 | -$70.0 | 1W - 1L - 0T | 364 | 295 | $195.40 |

#### Expanded Audit Block Summary:
- **Mean Paired Delta**: **+$91.32 USD**
- **Median Paired Delta**: **+$74.00 USD**
- **Standard Deviation**: $161.40 USD
- **Seed Record**: 19 Wins - 6 Losses - 0 Ties (76.0% Win Rate)
- **Match Record**: 40 Wins - 10 Losses - 0 Ties (80.0% Win Rate)
- **Probed States**: 9,102 states | **Positive Headroom States**: 7,381 (81.09%)
- **Mean Oracle Headroom**: **$190.50 USD** | **Max**: $17,730.00 USD

---

## 3. Grand Full-Census Synthesis (N=35 Seeds, 70 Matches)

$$\text{Combined Mean Paired Delta} = \frac{10 \times 72.40 + 25 \times 91.32}{35} = \mathbf{+85.91\text{ USD}}$$
$$\text{Combined Median Paired Delta} = \mathbf{+58.00\text{ USD}}$$
$$\text{Grand Match Record} = \mathbf{54\text{ Wins} - 14\text{ Losses} - 2\text{ Ties}}\quad (77.1\%\text{ Win Rate})$$
$$\text{Grand Seed Record} = \mathbf{26\text{ Wins} - 8\text{ Losses} - 1\text{ Tie}}\quad (74.3\%\text{ Win Rate})$$

### Oracle Diagnostic Upper Envelope:
- Total States Probed: **12,742**
- Positive Headroom States Discovered: **10,285 (80.72%)**
- Mean Oracle Headroom: **$196.87 USD**
- Median Oracle Headroom: **$27.00 USD**
- 90th Percentile: **$301.10 USD**
- 95th Percentile: **$654.20 USD**
- Maximum Oracle Headroom: **$17,730.00 USD**
