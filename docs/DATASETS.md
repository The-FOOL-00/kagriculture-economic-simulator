# Kagriculture External Replay Datasets & Acquisition Protocols

This document details the external datasets, replay collections, and simulation trajectory archives used across the Kagriculture project lifecycle.

---

## 1. Replay Acquisition Overview

The Kagriculture research program utilized competitive match replays from the Kaggle **Kaggriculture** environment to perform:
- Forensic loss analysis and causal tracing (V39, V46, V56).
- Market pressure modeling and opponent action prediction (V45).
- Macro route discovery and bottleneck analysis (V24, V25, V47, V48).
- Elite policy transfer and strategy verification (V49, V58, V60).

Because each full simulation episode JSON is 30–35 MB uncompressed, keeping raw replays in Git creates multi-gigabyte bloat. The datasets below are preserved externally with deterministic re-acquisition scripts.

---

## 2. Dataset Registry

### A. September 2026 Elite Match Replays (V60 Corpus)
- **Dataset Name**: `kaggriculture-sep-elite-replays`
- **Acquisition Date**: September 2026
- **Source**: Kaggle Episodes API (`https://www.kaggle.com/api/v1/episodes/`)
- **Schema**: Standard Kaggle Environment Episode JSON (`steps`, `agents`, `rewards`, `info`, `schema_version`)
- **Required Environment**: Python 3.11+, `kaggle` CLI / API client, `requests`
- **Retrieval Script**: [`research/v60/data/acquire_sep_elite_replays.py`](file:///c:/Users/Sundareswaran/Kagriculture/research/v60/data/acquire_sep_elite_replays.py)
- **Batch Shell Script**: [`research/v60/data/ACQUISITION_COMMANDS.sh`](file:///c:/Users/Sundareswaran/Kagriculture/research/v60/data/ACQUISITION_COMMANDS.sh)
- **Instructions to Reacquire**:
  ```bash
  python research/v60/data/acquire_sep_elite_replays.py --output-dir research/v60/data/tmp_ep_jsons/
  ```

### B. Live Tournament Episode Stream (V31R2 Corpus)
- **Dataset Name**: `kaggriculture-live-episodes-v31r2`
- **Acquisition Date**: Early-Mid September 2026
- **Local Location (Excluded)**: `live_data/episodes_v31r2/keep/` (193 match replays, ~6.07 GB)
- **Purpose**: Live meta monitoring and win-rate scorecards across production candidate versions (V22R1 vs A7).
- **Retrieval Method**: Replayable via episode IDs recorded in [`live_data/episodes_v31r2/`](file:///c:/Users/Sundareswaran/Kagriculture/live_data/episodes_v31r2/).

### C. Teammate Replay Corpus (lixingtao123 Collaboration)
- **Dataset Name**: `lixingtao123-online-replays`
- **Acquisition Date**: September 2026
- **Local Location (Excluded)**: `external_repos/lixingtao123-Kaggriculture/online_replays/` (~1.46 GB, categories A, B, C1, C2)
- **Purpose**: Evaluation of public meta clones, multi-route adaptations, and opening patterns.
- **Source**: Teammate GitHub repository `lixingtao123-Kaggriculture`.

### D. August 3100+ Elite Replay Database (V58 Corpus)
- **Dataset Name**: `august-3100-replays`
- **Acquisition Date**: August 2026
- **Local Location (Excluded)**: `research/v58/data/replay_database.jsonl` (114 MB)
- **Finding**: Evaluated in V58. Stale carrot-0 meta superseded by September wash/carrot meta (0/400 wins vs V49).

---

## 3. Replay Schema Structure

Each match replay JSON file follows the Kaggle Environment specification:
```json
{
  "id": 111953202,
  "specification": { "name": "kaggriculture", "version": "1.32.7" },
  "configuration": { "episodeSteps": 700, "actTimeout": 2 },
  "steps": [
    [
      { "action": {}, "observation": { "step": 0, "cash": 100, ... }, "reward": 0, "status": "ACTIVE" },
      { "action": {}, "observation": { "step": 0, "cash": 100, ... }, "reward": 0, "status": "ACTIVE" }
    ],
    ...
  ]
}
```

---

## 4. Exact Historical Reproducibility Policy

- To reproduce benchmark matches between agents (e.g. V49 vs V44, V49 vs Teammate V24), **external replays are NOT required**. The evaluation harnesses run self-contained local matches using the deterministic simulation engine in `engine/` or `kaggle_environments`.
- External replays are strictly historical observational records used for offline postmortems.
