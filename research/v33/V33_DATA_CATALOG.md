# V33 Data Catalog: Replay & Episode Sources

**Date:** 2026-09-24  
**Program:** Kagriculture V33 Research Program  
**Purpose:** Comprehensive catalog of all available replay, episode, and telemetry data sources across the repository for route extraction, clustering, and behavioral analysis.

---

## 1. Overview of Data Sources

The repository contains three primary classes of replay and telemetry data:
1. **Full-Match Kaggle Replay Archives (Root & `replays/`):** 36 complete 720-step JSON replay files recording full observation and action traces, worker movements, market orders, shed inventories, crop states, and final rewards for both players across diverse seeds.
2. **Live Match Telemetry Records (`live_data/episodes_v31r2/`):** 264 historical live match records from A7 and V22R1 submissions against competition opponents, detailing rewards, deltas, match outcomes (W/L/T), and opponent IDs.
3. **Internal Simulator Trajectory Logs (`results/`):** Extensive benchmark and evaluation runs from V25, V30, V31R2, and V32 capturing per-step money trajectories, 12-turn structured states, action digests, and market transactions.

---

## 2. Full-Match Replay Inventory

### A. Root Strategic Replays

| Filename | Size (MB) | Steps | Seed | Player 0 | Player 1 | Rewards (P0 / P1) | Strategic Focus |
| :--- | :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| `elo3000_test_replay.json` | 11.2 | 720 | 104820229 | Expert A | Expert B | High-tier ($180k+) | Top-ladder benchmark replay |
| `episode-104820229-replay.json` | 30.3 | 720 | 104820229 | Competitor 0 | Competitor 1 | Full observation trace | Detailed multi-worker coordination |
| `master_83k_replay.json` | 12.6 | 720 | 249431 | Candidate | Baseline | $83,066 / $77,947 | Wheat/Livestock balanced |
| `master_fast_replay.json` | 9.5 | 720 | 249431 | Fast Route | Baseline | Early expansion | Rapid early worker deployment |
| `master_fixed_replay.json` | 10.9 | 720 | 249431 | Fixed Zone | Baseline | Stable cashflow | Zoning and weed management |
| `titan_day0_replay.json` | 11.5 | 720 | 249100 | Titan variant | Opponent | Day 0 expansion | Aggressive opening purchases |
| `titan_test_replay.json` | 12.6 | 720 | 249101 | Titan variant | Opponent | Crop/Livestock mix | Heavy animal stocking |
| `titan_wheat_replay.json` | 10.7 | 720 | 249102 | Wheat specialist | Opponent | Wheat monoculture | Bakery saturation regime |

### B. Dedicated Match Replays (`replays/`)
Contains 23 full Kaggle replay files (`episode-92890298-replay.json` through `episode-92913673-replay.json`), each ranging from 14.7 MB to 24.4 MB and covering complete 720-step episodes across diverse seeds and agent architectures.

---

## 3. Live Opponent Telemetry (`live_data/episodes_v31r2/summary.jsonl`)

- **Total Recorded Matches:** 264 matches
- **Submission Breakdown:**
  - `v22r1` (Slot A champion): 156 matches
  - `a7` (Slot B incumbent): 108 matches
- **Overall Match Record:**
  - Wins: 172 (65.2%)
  - Losses: 79 (29.9%)
  - Ties: 13 (4.9%)
- **Data Schema:**
  - `episode_id`: Kaggle episode ID
  - `sub`: Submission alias (`v22r1`, `a7`)
  - `createTime`: Timestamp
  - `our_idx`: Seat index (0 or 1)
  - `opp_team`: Opponent team / username
  - `our_reward`: Final cash achieved by our agent
  - `opp_reward`: Final cash achieved by opponent
  - `delta`: `our_reward - opp_reward`
  - `result`: `"W"`, `"L"`, or `"T"`
  - `seed`: Environment seed

---

## 4. Replay Index & Data Accessibility

All datasets are indexed in `data_catalog.json`.
The replay normalizer (`replay_normalizer.py`) converts these diverse files into a uniform canonical schema defined in `trajectory_schema.py`.
