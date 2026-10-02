# Kaggle Kaggriculture Competition Summary & Official Standing

This document records the official competition parameters, team registration, final ranking, and scoring metrics for the **Kagriculture** research project.

---

## 1. Official Competition Profile

- **Competition Name**: [Kaggriculture](https://www.kaggle.com/competitions/kaggriculture)
- **Competition Host**: Kaggle (Simulation Track / Featured Competition)
- **Prize Pool**: $50,000 USD
- **Environment Specification**: Synchronous, 2-player, 700-turn economic agriculture simulation (`kaggle-environments 1.32.7`)
- **Official Competition Leaderboard**: [Kaggriculture Public Leaderboard](https://www.kaggle.com/competitions/kaggriculture/leaderboard)
- **Competition Close Date**: September 30, 2026 23:59 UTC
- **Standing Verification Date**: **October 2, 2026**

---

## 2. Official Team Registration & Standing

| Metric / Attribute | Verified Value | Verification Source / Method |
| :--- | :--- | :--- |
| **Team Name** | **Eldritch** | Official Kaggle Leaderboard API & CSV Snapshot |
| **Team ID** | `16791873` | Kaggle Public Leaderboard Registry |
| **Team Members** | `thefool00` (Repository Author), `sanjay6727` | Kaggle Public Leaderboard Registry |
| **Official Rank** | **#1,125** (out of 10,246 teams — Top ~11%) | Official Kaggle Leaderboard (`2026-10-02T06:45:07`) |
| **Official Rating / Score** | **1,791.9** | Official Kaggle Rating (Elo-based ladder) |
| **Last Submission Date** | **2026-09-30 17:15:29 UTC** | Official Submission Log |
| **Total Submissions** | 2 active competition submissions | Verified via Kaggle API |

---

## 3. Production Submission Details

- **Final Incumbent Agent**: **V49 Meta Fusion**
- **Production Source File**: [`candidates/v49_meta_fusion/main.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/v49_meta_fusion/main.py)
- **SHA-256 Checksum**: `8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11`
- **Submission Archive Bundle**: [`submissions/v49_meta_fusion_20260929_2212.zip`](file:///c:/Users/Sundareswaran/Kagriculture/submissions/v49_meta_fusion_20260929_2212.zip)
- **Archive SHA-256 Checksum**: `37F10DEE73C7E01BE1FE240FBFC5344F254D2FE29FB0764FB14B2C69AB99306D`

---

## 4. Internal Validation vs. Leaderboard Rating

It is critical to distinguish local experimental metrics from Kaggle's public leaderboard metrics:

1. **Internal Validation Benchmark**:
   - **Win Rate**: **99.31%** (572 Wins / 4 Losses / 0 Ties) across 576 fresh unobserved seeds.
   - **Historical Replay Holdout**: **100% Win Rate** (400 Wins / 0 Losses) against top historical opponent replays.
   - **Environment**: Evaluated locally using `FastKagricultureSim` and official `kaggle-environments 1.32.7`.
2. **Kaggle Leaderboard Rating**:
   - **Rating**: **1,791.9**
   - **Rank**: **#1,125**
   - **Measurement**: Multi-player dynamic matchmaking Elo computed over asynchronous ladder pairings against global competitors.
