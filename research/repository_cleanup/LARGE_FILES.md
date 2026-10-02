# KAGRICULTURE SIZE AUDIT AND LARGE FILES REPORT

Generated during Phase 2 Repository Audit.

## 1. Executive Summary

- **Total Repository Size**: 18.698 GB (19147.20 MB)
- **Git Object Database (.git)**: 99.66 MB
- **Tracked Files Size**: 0.322 GB (329.51 MB) [3997 files]
- **Untracked Files Size**: 2.885 GB (2954.07 MB) [791 files]
- **Ignored Files Size**: 15.395 GB (15763.97 MB)

**Key Takeaway**: The Git object history is clean (~99.7 MB). The ~18.7 GB footprint is entirely in working-tree data: 15.4 GB of ignored files (raw replays, live data, .venv) and 2.88 GB of untracked files (primarily research/v60/data/tmp_ep_jsons and derived datasets).

## 2. Size Buckets

- **Files >= 1 GB**: 0
- **Files 500 MB - 1 GB**: 0
- **Files 100 MB - 500 MB**: 8
- **Files 50 MB - 100 MB**: 1
- **Files 10 MB - 50 MB**: 572
- **Total files >= 10 MB**: 581

## 3. Files >= 100 MB

| File Path | Size (MB) | Git Status | Recommended Action |
| :--- | :---: | :---: | :--- |
| `.venv/lib/python3.14/site-packages/torch/lib/libtorch_cpu.so` | 417.93 | IGNORED | Delete (.venv virtualenv cache) |
| `results/v32_p2_bc_legs.jsonl` | 220.69 | IGNORED | Exclude/Delete (derived trajectory cache) |
| `scratch/fast_provenance_hits.json` | 214.34 | IGNORED | Exclude/Delete (derived trajectory cache) |
| `results/v27_trajectories.jsonl` | 160.10 | IGNORED | Exclude/Delete (derived trajectory cache) |
| `results/v27_fresh_trajectories.jsonl` | 128.14 | IGNORED | Exclude/Delete (derived trajectory cache) |
| `research/v45/artifacts/market_pressure_dataset.pt` | 116.23 | UNTRACKED | Exclude/Document in DATASETS.md |
| `research/v58/data/replay_database.jsonl` | 114.13 | UNTRACKED | Exclude/Document in DATASETS.md |
| `research/v45/artifacts/opponent_market_history.jsonl` | 108.76 | UNTRACKED | Exclude/Document in DATASETS.md |

## 4. Top 100 Largest Files

| # | File Path | Size (MB) | Git Status |
| :-: | :--- | :---: | :---: |
| 1 | `.venv/lib/python3.14/site-packages/torch/lib/libtorch_cpu.so` | 417.93 | IGNORED |
| 2 | `results/v32_p2_bc_legs.jsonl` | 220.69 | IGNORED |
| 3 | `scratch/fast_provenance_hits.json` | 214.34 | IGNORED |
| 4 | `results/v27_trajectories.jsonl` | 160.10 | IGNORED |
| 5 | `results/v27_fresh_trajectories.jsonl` | 128.14 | IGNORED |
| 6 | `research/v45/artifacts/market_pressure_dataset.pt` | 116.23 | UNTRACKED |
| 7 | `research/v58/data/replay_database.jsonl` | 114.13 | UNTRACKED |
| 8 | `research/v45/artifacts/opponent_market_history.jsonl` | 108.76 | UNTRACKED |
| 9 | `scratch/forensic_telemetry_dump.json` | 66.14 | IGNORED |
| 10 | `research/v60/data/tmp_ep_jsons/111953202.json` | 46.61 | UNTRACKED |
| 11 | `replays/raw/georgymamarin/state.json` | 36.84 | IGNORED |
| 12 | `.venv/lib/python3.14/site-packages/kaggle_environments/envs/open_spiel_env/games/repeated_poker/preset_hands.jsonl` | 35.56 | IGNORED |
| 13 | `scratch/v39/live/replays/episode-113177277-replay.json` | 33.03 | IGNORED |
| 14 | `live_data/episodes_v31r2/keep/v22r1-episode-111504241-replay.json` | 33.01 | IGNORED |
| 15 | `live_data/episodes_v31r2/keep/a7-episode-111876058-replay.json` | 32.99 | IGNORED |
| 16 | `research/v60/data/tmp_ep_jsons/111725606.json` | 32.96 | UNTRACKED |
| 17 | `live_data/episodes_v31r2/keep/a7-episode-111975251-replay.json` | 32.96 | IGNORED |
| 18 | `research/v60/data/tmp_ep_jsons/111815011.json` | 32.95 | UNTRACKED |
| 19 | `live_data/episodes_v31r2/keep/a7-episode-111890799-replay.json` | 32.94 | IGNORED |
| 20 | `live_data/episodes_v31r2/keep/v22r1-episode-111476273-replay.json` | 32.94 | IGNORED |
| 21 | `live_data/episodes_v31r2/keep/a7-episode-111950940-replay.json` | 32.92 | IGNORED |
| 22 | `live_data/episodes_v31r2/keep/v22r1-episode-111342636-replay.json` | 32.91 | IGNORED |
| 23 | `live_data/episodes_v31r2/keep/v22r1-episode-111619120-replay.json` | 32.90 | IGNORED |
| 24 | `live_data/episodes_v31r2/keep/v22r1-episode-111488047-replay.json` | 32.88 | IGNORED |
| 25 | `live_data/episodes_v31r2/keep/v22r1-episode-111446099-replay.json` | 32.87 | IGNORED |
| 26 | `scratch/v39/live/replays/episode-113166778-replay.json` | 32.83 | IGNORED |
| 27 | `live_data/episodes_v31r2/keep/a7-episode-111919236-replay.json` | 32.83 | IGNORED |
| 28 | `live_data/episodes_v31r2/keep/a7-episode-111895336-replay.json` | 32.83 | IGNORED |
| 29 | `live_data/episodes_v31r2/keep/v22r1-episode-111327426-replay.json` | 32.83 | IGNORED |
| 30 | `live_data/episodes_v31r2/keep/a7-episode-111864683-replay.json` | 32.83 | IGNORED |
| 31 | `live_data/episodes_v31r2/keep/v22r1-episode-111630639-replay.json` | 32.82 | IGNORED |
| 32 | `research/v60/data/tmp_ep_jsons/111630639.json` | 32.82 | UNTRACKED |
| 33 | `live_data/episodes_v31r2/keep/v22r1-episode-111429400-replay.json` | 32.82 | IGNORED |
| 34 | `live_data/episodes_v31r2/keep/a7-episode-111887492-replay.json` | 32.82 | IGNORED |
| 35 | `live_data/episodes_v31r2/keep/a7-episode-111878712-replay.json` | 32.82 | IGNORED |
| 36 | `live_data/episodes_v31r2/keep/v22r1-episode-111743592-replay.json` | 32.81 | IGNORED |
| 37 | `research/v60/data/tmp_ep_jsons/111743592.json` | 32.81 | UNTRACKED |
| 38 | `live_data/episodes_v31r2/keep/v22r1-episode-111382834-replay.json` | 32.81 | IGNORED |
| 39 | `live_data/episodes_v31r2/keep/v22r1-episode-111621363-replay.json` | 32.81 | IGNORED |
| 40 | `live_data/episodes_v31r2/keep/episode-111787995-replay.json` | 32.81 | IGNORED |
| 41 | `research/v60/data/tmp_ep_jsons/111787995.json` | 32.81 | UNTRACKED |
| 42 | `research/v60/data/tmp_ep_jsons/111948638.json` | 32.81 | UNTRACKED |
| 43 | `live_data/episodes_v31r2/keep/v22r1-episode-111347065-replay.json` | 32.80 | IGNORED |
| 44 | `live_data/episodes_v31r2/keep/a7-episode-111896472-replay.json` | 32.80 | IGNORED |
| 45 | `live_data/episodes_v31r2/keep/a7-episode-111911269-replay.json` | 32.80 | IGNORED |
| 46 | `live_data/episodes_v31r2/keep/v22r1-episode-111921933-replay.json` | 32.80 | IGNORED |
| 47 | `research/v60/data/tmp_ep_jsons/111921933.json` | 32.80 | UNTRACKED |
| 48 | `live_data/episodes_v31r2/keep/v22r1-episode-111432728-replay.json` | 32.79 | IGNORED |
| 49 | `research/v60/data/tmp_ep_jsons/111866674.json` | 32.78 | UNTRACKED |
| 50 | `live_data/episodes_v31r2/keep/v22r1-episode-111337013-replay.json` | 32.78 | IGNORED |
| 51 | `live_data/episodes_v31r2/keep/v22r1-episode-111530511-replay.json` | 32.78 | IGNORED |
| 52 | `live_data/episodes_v31r2/keep/v22r1-episode-111906269-replay.json` | 32.78 | IGNORED |
| 53 | `research/v60/data/tmp_ep_jsons/111906269.json` | 32.78 | UNTRACKED |
| 54 | `live_data/episodes_v31r2/keep/v22r1-episode-111671179-replay.json` | 32.77 | IGNORED |
| 55 | `research/v60/data/tmp_ep_jsons/111671179.json` | 32.77 | UNTRACKED |
| 56 | `live_data/episodes_v31r2/keep/v22r1-episode-111397659-replay.json` | 32.77 | IGNORED |
| 57 | `live_data/episodes_v31r2/keep/v22r1-episode-111608213-replay.json` | 32.77 | IGNORED |
| 58 | `scratch/v39/live/replays/episode-113183263-replay.json` | 32.76 | IGNORED |
| 59 | `scratch/v39/live/replays/episode-113176099-replay.json` | 32.76 | IGNORED |
| 60 | `live_data/episodes_v31r2/keep/v22r1-episode-111966360-replay.json` | 32.75 | IGNORED |
| 61 | `research/v60/data/tmp_ep_jsons/111809491.json` | 32.74 | UNTRACKED |
| 62 | `research/v60/data/tmp_ep_jsons/111738881.json` | 32.74 | UNTRACKED |
| 63 | `live_data/episodes_v31r2/keep/v22r1-episode-111383075-replay.json` | 32.74 | IGNORED |
| 64 | `live_data/episodes_v31r2/keep/v22r1-episode-111921667-replay.json` | 32.74 | IGNORED |
| 65 | `research/v60/data/tmp_ep_jsons/111921667.json` | 32.74 | UNTRACKED |
| 66 | `live_data/episodes_v31r2/keep/episode-111883982-replay.json` | 32.73 | IGNORED |
| 67 | `live_data/episodes_v31r2/keep/v22r1-episode-111418055-replay.json` | 32.73 | IGNORED |
| 68 | `scratch/v39/live/replays/episode-113186749-replay.json` | 32.73 | IGNORED |
| 69 | `live_data/episodes_v31r2/keep/v22r1-episode-111325969-replay.json` | 32.69 | IGNORED |
| 70 | `live_data/episodes_v31r2/keep/v22r1-episode-111754576-replay.json` | 32.68 | IGNORED |
| 71 | `research/v60/data/tmp_ep_jsons/111754576.json` | 32.68 | UNTRACKED |
| 72 | `live_data/episodes_v31r2/keep/episode-111470041-replay.json` | 32.65 | IGNORED |
| 73 | `live_data/episodes_v31r2/keep/v22r1-episode-111470041-replay.json` | 32.65 | IGNORED |
| 74 | `live_data/episodes_v31r2/keep/v22r1-episode-111793314-replay.json` | 32.63 | IGNORED |
| 75 | `research/v60/data/tmp_ep_jsons/111793314.json` | 32.63 | UNTRACKED |
| 76 | `scratch/v39/live/replays/episode-113164394-replay.json` | 32.61 | IGNORED |
| 77 | `scratch/v39/live/replays/episode-113170295-replay.json` | 32.60 | IGNORED |
| 78 | `scratch/v39/live/replays/episode-113180924-replay.json` | 32.54 | IGNORED |
| 79 | `research/v60/data/tmp_ep_jsons/111762675.json` | 32.44 | UNTRACKED |
| 80 | `live_data/episodes_v31r2/keep/v22r1-episode-111543772-replay.json` | 32.39 | IGNORED |
| 81 | `live_data/episodes_v31r2/keep/v22r1-episode-111400403-replay.json` | 32.02 | IGNORED |
| 82 | `live_data/episodes_v31r2/keep/v22r1-episode-111768023-replay.json` | 31.76 | IGNORED |
| 83 | `research/v60/data/tmp_ep_jsons/111768023.json` | 31.76 | UNTRACKED |
| 84 | `scratch/v39/live/replays/episode-113172595-replay.json` | 31.62 | IGNORED |
| 85 | `scratch/v39/live/replays/episode-113179717-replay.json` | 31.48 | IGNORED |
| 86 | `live_data/episodes_v31r2/keep/a7-episode-111886277-replay.json` | 31.48 | IGNORED |
| 87 | `scratch/v39/live/replays/episode-113158665-replay.json` | 31.37 | IGNORED |
| 88 | `scratch/replays/Crop_Dusta_104824599.json` | 31.33 | IGNORED |
| 89 | `scratch/replays/top_episodes_top_55929317_104824599.json` | 31.33 | IGNORED |
| 90 | `scratch/replays/top_episodes_top_55957002_104824599.json` | 31.33 | IGNORED |
| 91 | `scratch/replays/Whyme_Labs_104824599.json` | 31.33 | IGNORED |
| 92 | `replays/live_tournament/episode_107561605.json` | 31.30 | IGNORED |
| 93 | `scratch/replays/Whyme_Labs_104821658.json` | 31.29 | IGNORED |
| 94 | `replays/live_tournament/episode_107679641.json` | 31.28 | IGNORED |
| 95 | `replays/live_tournament/episode_107688598.json` | 31.27 | IGNORED |
| 96 | `scratch/v39/live/replays/episode-113165586-replay.json` | 31.25 | IGNORED |
| 97 | `replays/live_tournament/episode_107544060.json` | 31.23 | IGNORED |
| 98 | `live_data/episodes_v31r2/keep/a7-episode-111874934-replay.json` | 31.22 | IGNORED |
| 99 | `.venv/lib/python3.14/site-packages/torch/lib/libtorch_python.so` | 31.21 | IGNORED |
| 100 | `scratch/replays/MtN_104823472.json` | 31.21 | IGNORED |

## 5. Top 50 Largest Directories

| Directory Path | Size (MB) | File Count | Primary Contents |
| :--- | :---: | :---: | :--- |
| `live_data` | 6069.85 | 213 | Live tournament replay corpus |
| `live_data/episodes_v31r2` | 6069.85 | 212 | Live tournament replay corpus |
| `live_data/episodes_v31r2/keep` | 6068.55 | 193 | Live tournament replay corpus |
| `replays` | 3949.39 | 288 | Replay JSON archive |
| `research` | 2980.80 | 1009 | Source / Research artifacts |
| `research/v60/data` | 2540.05 | 128 | Source / Research artifacts |
| `research/v60` | 2540.05 | 128 | Source / Research artifacts |
| `research/v60/data/tmp_ep_jsons` | 2527.15 | 80 | V60 temporary episode json dumps |
| `scratch` | 2287.25 | 2185 | Scratch replay dumps & telemetry |
| `external_repos` | 1582.44 | 492 | Source / Research artifacts |
| `external_repos/lixingtao123-Kaggriculture` | 1567.39 | 264 | Source / Research artifacts |
| `external_repos/lixingtao123-Kaggriculture/online_replays` | 1456.39 | 49 | Replay JSON archive |
| `replays/live_tournament` | 1443.81 | 48 | Replay JSON archive |
| `replays/Aethel_prime_v1` | 1409.09 | 101 | Replay JSON archive |
| `.venv` | 1219.38 | 27898 | Python virtual environment |
| `.venv/lib/python3.14/site-packages` | 1219.17 | 27854 | Python virtual environment |
| `.venv/lib/python3.14` | 1219.17 | 27854 | Python virtual environment |
| `.venv/lib` | 1219.17 | 27854 | Python virtual environment |
| `scratch/replays` | 1027.91 | 36 | Replay JSON archive |
| `scratch/v39` | 897.32 | 69 | Scratch replay dumps & telemetry |
| `scratch/v39/live` | 896.67 | 50 | Scratch replay dumps & telemetry |
| `scratch/v39/live/replays` | 896.04 | 29 | Replay JSON archive |
| `.venv/lib/python3.14/site-packages/torch` | 736.80 | 14471 | Python virtual environment |
| `results` | 711.92 | 297 | Trajectory results |
| `replays/Apex_v4` | 498.81 | 52 | Replay JSON archive |
| `.venv/lib/python3.14/site-packages/torch/lib` | 454.39 | 16 | Python virtual environment |
| `external_repos/lixingtao123-Kaggriculture/online_replays/C1` | 380.57 | 13 | Replay JSON archive |
| `external_repos/lixingtao123-Kaggriculture/online_replays/B` | 358.89 | 12 | Replay JSON archive |
| `external_repos/lixingtao123-Kaggriculture/online_replays/A` | 356.17 | 12 | Replay JSON archive |
| `external_repos/lixingtao123-Kaggriculture/online_replays/C2` | 331.13 | 11 | Replay JSON archive |
| `research/v45` | 225.40 | 48 | Source / Research artifacts |
| `research/v45/artifacts` | 225.19 | 15 | Source / Research artifacts |
| `.venv/lib/python3.14/site-packages/kaggle_environments` | 135.27 | 761 | Python virtual environment |
| `.venv/lib/python3.14/site-packages/kaggle_environments/envs` | 134.79 | 734 | Python virtual environment |
| `replays/raw` | 128.01 | 60 | Replay JSON archive |
| `research/v58` | 125.97 | 81 | Source / Research artifacts |
| `research/v58/data` | 114.23 | 5 | Source / Research artifacts |
| `.venv/lib/python3.14/site-packages/scipy` | 103.04 | 2412 | Python virtual environment |
| `replays/raw/georgymamarin` | 94.68 | 14 | Replay JSON archive |
| `external_repos/lixingtao123-Kaggriculture/opponents` | 89.17 | 12 | Source / Research artifacts |
| `external_repos/lixingtao123-Kaggriculture/opponents/top1_tetsuya/replays` | 88.85 | 3 | Replay JSON archive |
| `external_repos/lixingtao123-Kaggriculture/opponents/top1_tetsuya` | 88.85 | 3 | Source / Research artifacts |
| `.venv/lib/python3.14/site-packages/torch/test` | 84.65 | 112 | Python virtual environment |
| `.venv/lib/python3.14/site-packages/kaggle_environments/envs/open_spiel_env` | 74.52 | 312 | Python virtual environment |
| `.venv/lib/python3.14/site-packages/kaggle_environments/envs/open_spiel_env/games` | 74.40 | 302 | Python virtual environment |
| `.venv/lib/python3.14/site-packages/sympy` | 69.17 | 3093 | Python virtual environment |
| `.venv/lib/python3.14/site-packages/torch/bin` | 51.01 | 40 | Python virtual environment |
| `experiments` | 49.27 | 372 | Source / Research artifacts |
| `.venv/lib/python3.14/site-packages/numpy` | 39.07 | 1309 | Python virtual environment |