# Kagriculture External Datasets & Replay Corpora

Large multi-gigabyte simulation replays, tournament episode dumps, and intermediate neural network tensors are **intentionally excluded from Git tracking**.

Tracking raw simulation JSONs (each match replay is ~33 MB; cumulative corpus exceeds 15 GB) causes severe Git repository bloat without adding version-control value. All simulation logic, agent architectures, benchmark harnesses, postmortems, and evaluation results are tracked in full.

## Manifest
A complete machine-readable ledger of all excluded datasets, local paths, sizes, sources, and reacquisition methods is provided in:
- [`MANIFEST.csv`](file:///c:/Users/Sundareswaran/Kagriculture/data/MANIFEST.csv)
- Detailed acquisition guides, schemas, and API retrieval scripts: [`docs/DATASETS.md`](file:///c:/Users/Sundareswaran/Kagriculture/docs/DATASETS.md)

## Summary of Excluded Data Corpora
| Dataset Name | Typical Path | Size | Description |
| :--- | :--- | :---: | :--- |
| **Live Tournament Episodes** | `live_data/episodes_v31r2/` | ~6.07 GB | Full JSON match replays from official Kaggle tournament ladder. |
| **Competition Replay Archive** | `replays/` | ~3.95 GB | Match replays across top agents (`Aethel_prime_v1`, `Apex_v4`, `live_tournament`). |
| **V60 Sep Elite Replays** | `research/v60/data/tmp_ep_jsons/` | ~2.53 GB | Downloaded match episodes from top September ladder participants. |
| **Teammate Public Replays** | `external_repos/lixingtao123-Kaggriculture/online_replays/` | ~1.46 GB | Raw replays A, B, C1, C2 collected during collaboration. |
| **Derived Trajectory Logs** | `results/*.jsonl` | ~0.51 GB | Turn-by-turn trajectory tables generated during V27 and V32 campaigns. |
| **V45 Market Pressure Dataset** | `research/v45/artifacts/` | ~225 MB | PyTorch tensor dataset (`.pt`) and opponent market history. |
| **August Replay Database** | `research/v58/data/` | ~114 MB | August match replay SQLite/JSONL corpus. |

## How to Reacquire Data
To download fresh replays or re-acquire the September elite dataset:
```bash
python research/v60/data/acquire_sep_elite_replays.py
```
For Kaggle API automated downloads:
```bash
bash research/v60/data/ACQUISITION_COMMANDS.sh
```
Ensure your Kaggle API key is configured at `~/.kaggle/kaggle.json`.
