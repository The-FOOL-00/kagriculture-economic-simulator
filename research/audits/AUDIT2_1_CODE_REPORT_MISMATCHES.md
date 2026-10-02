# AUDIT 2.1: CODE VS. REPORT MISMATCH AUDIT
## Forensic Examination of Script Implementations, Parsers, Execution Paths, and Reporting Discrepancies

This document details all discovered discrepancies between written report narratives and the actual executing code across both the inherited research base (Audit 1) and the Audit 2 re-audit suite.

---

## 1. Master Code / Report Mismatch Summary

| Mismatch ID | Target Component | Nature of Discrepancy | Severity | Originating Audit | Verified Impact |
|:---:|:---|:---|:---:|:---:|:---|
| **MIS-01** | `scratch/reconstruct_live_losses.py` | Parser bug: `f.get("units", [])` evaluated to `[]` instead of `f.get("hands", [])`. | **CRITICAL** | Audit 1 (Inherited & Exposed by Audit 2) | Caused Audit 1 to believe hands dropped to 0, inventing the false "$800 hiring collapse" narrative. |
| **MIS-02** | `scratch/run_additive_investigation.py` | Action generator omission: `_plan_dedicated_worker` never called in `VACANT_TILES`; `HIRE` called daily in `SE_LAND`. | **CRITICAL** | Pre-Audit 1 (Exposed by Audit 2) | Caused crops to rot unwatered/unharvested and hired workers daily, invalidating the "no slack" experiment. |
| **MIS-03** | `scratch/test_step696_causal.py` | Counterfactual intervention defect: Line 25 stripped JIT Strawberry sells while inserting wheat sells. | **MODERATE** | Audit 1 (Clarified by Audit 2) | Artificially worsened losses on 3 seeds, obscuring the true root cause (Step 217 sheep failure). |
| **MIS-04** | `research/v2_dmitrii_residual_profit_map.md` (R14 Table 1) | Transcription error: Published mean margins (+28.8, +0.5, +46.4) did not match underlying JSON (+39.12, +11.40, +23.32). | **MODERATE** | Pre-Audit 1 (Exposed by Audit 2) | Distorted the partition profile, though overall mean (+24.61) remained consistent. |
| **MIS-05** | Audit 2 Confidence Interval Formula | Formula approximation: Audit 2 reported `[-$2.07, +$51.30]` using $z = 1.96$ rather than Student's $t_{149} = 1.9760$ (`[-$2.29, +$51.52]`). | **LOW** | Audit 2 | Minor mathematical discrepancy of ~0.22 coins; both intervals cross zero. |
| **MIS-06** | Audit 2 P-Value Citation | Inconsistency: `AUDIT2_SOURCE_MAP.md:25` cites $p = 0.070$, while `AUDIT2_REPRODUCTIONS.md:21, 114` cites $p = 0.0726$. | **LOW** | Audit 2 | Reporting inconsistency between normal approximation ($p = 0.0706$) and Student's $t$ ($p = 0.0727$). |
| **MIS-07** | 19S / 0T "Strictly Dominates" Narrative | Game-theoretic terminology misuse: Audit 2 described 19S/0T as "strictly dominant", while raw sweep has a 59% win rate on 50 seeds. | **LOW** | Audit 2 | Overstates empirical mean superiority as game-theoretic strict dominance. |

---

## 2. Detailed Technical Forensic Analysis of Mismatches

### MIS-01: The Replay Parser Key Mismatch (`units` vs `hands`)
- **Code Location**: `scratch/reconstruct_live_losses.py`, line 66:
  ```python
  def parse_farm(f):
      if not f: return {}
      money = f.get("money", 0)
      hands = len(f.get("units", []))  # <--- CRITICAL BUG
  ```
- **Engine Ground Truth**:
  In `sim.hpp:813` and `kaggriculture.py:168`, worker positions are serialized into the observation dictionary under the key `"hands"`:
  ```python
  "farms": [{"hands": [[x1, y1], [x2, y2], ...], "money": ..., ...}]
  ```
- **Consequence**:
  `f.get("units", [])` looked for a non-existent key, returning `[]` for every farm at every step.
  The script recorded `hands: 0` for all checkpoints across all 161 replays.
  Audit 1 accepted this corrupted JSON output and spun the narrative that "hands collapsed from 7 to 4 due to liquidity starvation (< $800)".
- **Audit 2 Resolution**:
  Audit 2 inspected the raw replay `episode_107543042.json`, proved that cash was $9,847 (not < $800), and that 9 hands were hired. Audit 2.1 independently verified this finding.

---

### MIS-02: The Additive Slack Action Generator Defect
- **Code Location**: `scratch/run_additive_investigation.py`, lines 143–184:
  ```python
  # SE_LAND mode:
  if day >= self.deploy_day and hour == 1 and len(market) < 10:
      market.append(["HIRE"])  # <--- HIRES DAILY FOR 18 CONSECUTIVE DAYS
  
  # VACANT_TILES mode:
  if day == 12 and 297 <= step <= 305:
      action["hands"][i] = ["PLANT", "TOMATO"]
      # ZERO WATERING AND ZERO HARVESTING LOGIC EMITTED
  ```
- **Consequence**:
  The function `_plan_dedicated_worker` (which generates watering and harvesting moves) was indented inside `if self.land_mode == "SE_LAND"` and was never invoked for `VACANT_TILES`. The planted tomatoes never received water and were never harvested. Under `sim.hpp:725`, unharvested crops rot into weeds.
- **Audit 2 Resolution**:
  Audit 2 exposed this defect and correctly retracted the "no slack exists" conclusion.

---

### MIS-03: The Step 696 Counterfactual Sell Dropping Defect
- **Code Location**: `scratch/test_step696_causal.py`, lines 23–25:
  ```python
  m = action.get("market", [])
  action["market"] = [['SELL', 'WHEAT', 36]] + [o for o in m if o[0] == 'HIRE'][:9]
  ```
- **Consequence**:
  In V2, Step 696 had 11 orders: 9 HIREs, 1 SELL STRAWBERRY 4, and 1 SELL WHEAT 36.
  The counterfactual script placed SELL WHEAT 36 at index 0 and kept 9 HIREs, completely stripping the SELL STRAWBERRY 4 order.
  This caused loss on Seed 50081 to worsen from -$730 to -$818 not because Step 696 wheat selling was bad, but because the script discarded legitimate strawberry revenue.
- **Audit 2 Resolution**:
  Audit 2 noted this script defect, and conducted turn-by-turn cash tracing to prove that divergence had already occurred 479 steps earlier at Step 217.

---

### MIS-04: R14 Table 1 Reporting Transcription Error
- **Code Location**: `research/v2_dmitrii_residual_profit_map.md` Table 1 vs `scratch/v2_dmitrii_margin_scan.json`.
- **Comparison Table**:
  | Metric | Published in R14 Table 1 | Raw Value in JSON | Discrepancy |
  |:---|:---:|:---:|:---:|
  | Discovery Mean Margin | +$28.8 | **+$39.12** | -10.32 |
  | Qualification Mean Margin | +$0.5 | **+$11.40** | -10.90 |
  | Holdout Mean Margin | +$46.4 | **+$23.32** | +23.08 |
  | Max Win | +$454.0 | **+$326.0** | +128.0 |
  | Combined Total Mean | **+$24.61** | **+$24.61** | **0.00** |
- **Finding**:
  The partition means in Table 1 were erroneously transcribed from an earlier exploratory run, even though the combined mean (+24.61) matched the raw JSON exactly. Audit 2 detected and documented this discrepancy.

---

### MIS-05 & MIS-06: Statistical Formula & Citation Nuances in Audit 2
- **The 95% Confidence Interval**:
  Audit 2 reported: `[-$2.07, +$51.30]`.
  Derivation:
  $$\text{Audit 2}: 24.6133 \pm 1.96 \times 13.6149 = [-\$2.07, \; +\$51.30]$$
  $$\text{Exact Student's } t_{149}: 24.6133 \pm 1.9760 \times 13.6149 = [-\$2.29, \; +\$51.52]$$
  $$\text{Difference}: \pm 0.22 \text{ coins}$$
  While both intervals lead to the identical scientific conclusion (spanning zero), Audit 2 should have explicitly noted that it applied the standard normal z-critical value ($1.96$) rather than Student's $t$ critical value ($1.9760$).
- **The P-Value Discrepancy**:
  `AUDIT2_SOURCE_MAP.md:25` cited $p = 0.070$, while `AUDIT2_REPRODUCTIONS.md:21` and `AUDIT2_FINAL_VERDICT.md:32` cited $p = 0.0726$.
  The exact value for $t = 1.8078$ with $df = 149$ is $p = 0.0727$ (two-sided). Under normal approximation, $2(1 - \Phi(1.8078)) = 0.0706$. Audit 2 mixed the normal approximation p-value in one summary table with the t-distribution p-value elsewhere.

---

### MIS-07: Use of "Strictly Dominates" Terminology
- **Statement**: `AUDIT2_FINAL_VERDICT.md:43`, `CLEAN_EVIDENCE_BASE.md:94`:
  *"19S/0T strictly dominates all static hybrid allocations."*
- **Discrepancy**:
  In decision theory, a strategy strictly dominates another if and only if it yields a strictly greater payoff in **every possible state of the world**.
  In `crop_portfolio_sweep_results.json`, 19S/0T achieved a 59.0% win rate against Dmitrii across the 100 matches, and on specific Pizza seeds (e.g. Seed 50042 and Seed 50026), tomato allocations produced higher cash.
  Therefore, 19S/0T is **mean-dominant** or **best-performing in expected value**, but NOT strictly dominant in the game-theoretic sense.
- **Audit 2.1 Correction**:
  Rephrase to: *"19S/0T achieves the highest mean margin and lowest downside risk among all evaluated static crop allocations on the 50-seed Discovery partition."*
