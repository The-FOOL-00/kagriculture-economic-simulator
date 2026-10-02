# V59 — Current Data Inventory
**Generated:** 2026-09-28  
**Phase:** 0 — Data Discovery

---

## Executive Finding

> **No September replay files with strategic fingerprints are locally available.**

The georgymamarin public dataset and the Kaggle index both end on **2026-08-31**.  
The only local September data is 264 episode *summaries* (outcome + cash + opponent name)  
from our own live games played Sep 20–22 — no action streams, no state features.

---

## Sources Searched

### 1. `replays/raw/georgymamarin/` — PRIMARY CORPUS
| Property | Value |
|---|---|
| Type | Kaggle public dataset (georgymamarin/kaggriculture-episodes) |
| Date range | **2026-07-30 → 2026-08-31** |
| Total episodes | 74,699 |
| September episodes | **0** |
| Key files | episodes.csv, stream_hashes.csv, episode_features.csv, daily_stats.csv |
| Status | ❌ STALE — ends Aug 31 |

### 2. `replays/raw/kaggle_index/manifest.csv` — DAILY INDEX
| Property | Value |
|---|---|
| Date range | **2026-07-30 → 2026-08-31** |
| September entries | **0** |
| Top avg score Aug 07 | 3132.6 |
| Top avg score Aug 31 | 2961.9 |
| Status | ❌ STALE — ends Aug 31 |

**Critical note:** The manifest URLs confirm that Kaggle publishes daily replay datasets,  
but no September daily dataset has been downloaded to this environment.

### 3. `live_data/episodes_v31r2/` — OUR LIVE GAME HISTORY
| Property | Value |
|---|---|
| Date range | **2026-09-20 → 2026-09-22** |
| Total episodes | 264 |
| Submission monitored | v22r1 |
| Engine | 1.32.7 |
| Sep 20 | 39 games: W16 L23 |
| Sep 21 | 111 games: W45 L66 |
| Sep 22 | 114 games: W61 L53 |
| Contains action streams | **NO** |
| Contains replay JSON | **NO** |
| Contains state features | **NO** |
| Contains leaderboard ratings | **NO** (for opponents) |
| Status | ⚠️ SEPTEMBER PRESENT but metadata only |

### 4. `live_data/episodes_v31r2/kaggriculture-publicleaderboard-2026-09-22T08:50:44.csv`
| Property | Value |
|---|---|
| Snapshot time | **2026-09-22 08:50:44** |
| Total teams | 9,807 |
| Teams ≥ 3000 | **7** |
| Teams ≥ 2900 | 29 |
| Teams ≥ 2800 | 78 |
| Top team | DSM — 3109.5 |
| Status | ✅ CURRENT LEADERBOARD — most valuable Sep asset |

### 5. `replays/raw/destbreso/matchups_top.parquet`
| Property | Value |
|---|---|
| Rows | 421 |
| Opponent threshold | 2000+ rating |
| Derived from | Aug georgymamarin corpus |
| Distinct openings above 2000 | 112 |
| Status | ⚠️ AUGUST DERIVED |

### 6. `live_data/episodes_v31r2/team_wash_map.json`
| Property | Value |
|---|---|
| Teams mapped | 139 |
| Contains | Opening action sequences for Sep 20–22 opponents |
| Top Sep-22 3000+ teams present | **NONE** (Fedor is the only known opponent) |
| Status | ⚠️ PARTIAL — only teams we faced |

---

## September Date Coverage

| Date | Leaderboard | Episode Summaries | Replay JSON | Action Streams |
|---|---|---|---|---|
| Sep 01–19 | ❌ | ❌ | ❌ | ❌ |
| Sep 20 | ❌ | ✅ 39 games | ❌ | ❌ |
| Sep 21 | ❌ | ✅ 111 games | ❌ | ❌ |
| Sep 22 | ✅ snapshot | ✅ 114 games | ❌ | ❌ |
| Sep 23–28 | ❌ | ❌ | ❌ | ❌ |

---

## September Leaderboard — Current Elite (Sep 22, 08:50 UTC)

| Rank | Team | Score | Last Submit |
|---|---|---|---|
| 1 | **DSM** | **3109.5** | 2026-09-22 05:27 |
| 2 | **Vadim Vasilenko** | **3099.9** | 2026-09-21 21:16 |
| 3 | **Majkel1337** | **3070.6** | 2026-09-21 09:39 |
| 4 | **Unknown Mother-Goose** | **3052.5** | 2026-09-22 00:34 |
| 5 | **THIRD FARM CLUB** | **3049.1** | 2026-09-22 02:00 |
| 6 | **M & M & P & Q** | **3046.3** | 2026-09-21 18:20 |
| 7 | **Kaggledew Valley** | **3038.8** | 2026-09-22 02:21 |
| 8 | Yannik Schiffner | 2991.6 | 2026-09-22 04:54 |
| 9 | KawattaTaido | 2991.4 | 2026-09-21 05:13 |
| 10 | ymg_aq | 2988.9 | 2026-09-22 02:07 |

**All 7 teams above 3000 submitted as recently as Sep 21–22 → ACTIVE Sep meta**

---

## Gap vs V49

V49's controlled benchmark: **572W / 4L = 99.31%** (local tournament, not Kaggle rating)

The Sep 22 leaderboard shows active teams at 3038–3109 who submitted on Sep 21–22.  
**These are the true current targets — not the August 3138 fossil.**

---

## Acquisition Verdict

| Action | Feasible |
|---|---|
| Download Sep daily datasets via Kaggle API | ❌ No API key / network access in this env |
| Download Sep episode parquets | ❌ Not available locally |
| Read Sep 22 leaderboard | ✅ Done |
| Read Sep 20-22 episode summaries | ✅ Done |
| Read Aug replay fingerprints | ✅ Available (georgymamarin) |

> **Do NOT spend further run time attempting to acquire inaccessible September replay parquets.**  
> Proceed with: Sep 22 leaderboard + Aug corpus + local episode summaries.

---

## Data Inventory Files
- `CURRENT_DATA_INVENTORY.md` — this file
- `CURRENT_DATA_INVENTORY.json` — machine-readable version
- `current_replay_manifest.json` — to be created
- `current_replay_database.jsonl` — not creatable (no replay files)
- `dataset_audit.md` — see V58 equivalent at `research/v58/data/dataset_audit.md`
