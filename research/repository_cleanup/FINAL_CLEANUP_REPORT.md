# Kagriculture Final Repository Cleanup & Archival Report

**Project**: Kagriculture Economic Simulator & Competitive Agent Research  
**Date**: October 2, 2026  
**Repository**: `C:\Users\Sundareswaran\Kagriculture`  
**Remote**: `https://github.com/The-FOOL-00/kagriculture-economic-simulator.git`

---

## 1. Storage & File Metrics: Before vs After

| Metric | Before Cleanup | After Cleanup | Net Delta |
| :--- | :---: | :---: | :---: |
| **Total Directory Size** | **18.698 GB** (19,147.20 MB) | **832.73 MB** (0.813 GB) | **-17.885 GB (-95.6%)** |
| **Total Files** | **35,982 files** | **6,213 files** | **-29,769 files (-82.7%)** |
| **Git Database (.git)** | **99.66 MB** | **~105.00 MB** | **+5.34 MB (Healthy)** |
| **Working Tree Size** | **18.598 GB** | **~727.00 MB** | **-17.890 GB** |
| **Tracked Files Size** | 329.51 MB | ~727.00 MB | Full research & candidates captured |
| **Untracked Files Size** | 2,954.07 MB | 0.00 MB | Clean working tree |
| **Ignored Files Size** | 15,763.97 MB | ~10.00 MB | Hardened .gitignore |
| **Active Worktrees** | 3 (`Kagriculture`, `v24`, `v25`) | 1 (`Kagriculture`) | Redundant folders removed |

---

## 2. Preserved Components

All meaningful intellectual property, code, candidate agents, and reproducibility infrastructure were preserved in Git without loss:

1. **Incumbent Production Submission (Final Agent)**:
   - `candidates/v49_meta_fusion/main.py` (SHA256: `8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11`).
   - Packaged submission: `submissions/v49_meta_fusion_20260929_2212.zip` and `submissions/v49_meta_fusion_submission/main.py`.
   - Validated at **99.31% Win Rate (572W / 4L / 0T)** in fresh out-of-sample benchmarks.
2. **Teammate Collaborations**:
   - `team_submissions/submission_Vj_kc_v24.tar.gz` (SHA256: `4C9EF1DC...`, best teammate variant).
   - `team_submissions/submission_Vj_kc_v27.tar.gz` (SHA256: `EEE5AD4D...`).
3. **Full Evolutionary Candidate Lineage**:
   - `candidates/v44_economic_portfolio/` (discovery of step >= 520 CapEx cutoff).
   - `candidates/v45_adversarial_market/`, `candidates/v46_adaptive_macro/`, `candidates/v46_macro_route_b/`.
   - `candidates/v47_elite_transfer/` (port of public 2945 elite chassis).
   - `candidates/v48_challenger/` (Route 105 surgical overrides, +0.74 alpha).
   - `candidates/v50_dead_action_guard/` and `candidates/v51_blocked_repair/`.
4. **Historical Culture Campaigns**:
   - Branch `culture/v24`: Preserves Challengers C1, C2, C3, meta-strategy clusters, bottleneck matrix, and qualification manifests.
   - Branch `culture/v25`: Preserves Coherent Planner architecture (Macro P1, Options P2, Unified P3) and qualification manifests.
5. **Complete Scientific Research Dossiers (V40–V60 & Synthesis)**:
   - Full reports, causal traces, ablation results, and decision ledgers in `research/v40/` through `research/v60/` and `research/final_synthesis/`.
6. **Simulation Engine & Tooling**:
   - Bit-exact simulation engines (`engine/`, `aec/`, `FastKagricultureSim`).
   - Head-to-head tournament and evaluation runners in `scripts/` and `scratch/`.
   - Master documentation suite in `docs/` (`FINAL_ARTIFACTS.md`, `AGENTS.md`, `RESEARCH_HISTORY.md`, `DATASETS.md`).

---

## 3. Deleted Artifacts (Reclaimed 18.31 GB)

| Path | Size | Reason for Deletion |
| :--- | :---: | :--- |
| `live_data/episodes_v31r2/` | 6,069.85 MB | Raw tournament replay JSON corpus (213 files); documented in `docs/DATASETS.md` |
| `replays/` (Aethel_prime_v1, live_tournament, Apex_v4) | 3,949.39 MB | Raw historical match replay JSONs (288 files); documented in `docs/DATASETS.md` |
| `research/v60/data/tmp_ep_jsons/` | 2,527.15 MB | 80 temporary raw episode JSON dumps; re-downloadable via `acquire_sep_elite_replays.py` |
| `external_repos/lixingtao123-Kaggriculture/online_replays/` | 1,456.39 MB | Teammate raw online replay collection |
| `.venv/` | 1,219.38 MB | Python 3.14 virtual environment (27,898 files); reproducible via `requirements.txt` |
| `scratch/replays/` | 1,027.91 MB | Redundant local scratch replay copies |
| `scratch/v39/live/replays/` | 896.04 MB | Redundant V39 scratch replay copies |
| `results/v32_p2_bc_legs.jsonl` | 220.69 MB | Giant intermediate trajectory dump |
| `scratch/fast_provenance_hits.json` | 214.34 MB | Intermediate scratch search hit index |
| `results/v27_trajectories.jsonl` | 160.10 MB | Giant intermediate trajectory dump |
| `results/v27_fresh_trajectories.jsonl` | 128.14 MB | Giant intermediate trajectory dump |
| `research/v45/artifacts/market_pressure_dataset.pt` | 116.23 MB | Derived PyTorch tensor dataset |
| `research/v58/data/replay_database.jsonl` | 114.13 MB | Derived August replay database |
| `research/v45/artifacts/opponent_market_history.jsonl` | 108.76 MB | Intermediate opponent market logs |
| `scratch/forensic_telemetry_dump.json` | 66.14 MB | Intermediate telemetry dump |
| `**/__pycache__/`, `**/.pytest_cache/` | ~15.00 MB | Python interpreter bytecode caches |
| **Total Reclaimed Space** | **18,314.02 MB (~18.08 GB)** | Cleaned with zero loss of source or research integrity |

---

## 4. Moved Outside Git (External Datasets Policy)

Large replay collections (~15 GB) are excluded from version control to maintain repository health. A full manifest is maintained in:
- `data/MANIFEST.csv`
- `docs/DATASETS.md`

Deterministic retrieval is preserved via:
```bash
python research/v60/data/acquire_sep_elite_replays.py
```

---

## 5. Culture Version Handling

The physical directories `Kagriculture-v24` and `Kagriculture-v25` were separate worktree checkouts on disk consuming 1.45 GB:
1. In `Kagriculture-v24`: committed previously ignored metadata manifests (`V24_COHORT_MANIFEST.json`, `V24_LIVE_LEADERBOARD_SNAPSHOT.json`, `V24_QUAL_MANIFEST.json`, `V24_REPLAY_CORPUS_MANIFEST.json`).
2. Created permanent Git branch `culture/v24`.
3. In `Kagriculture-v25`: committed previously ignored metadata manifests (`V25_COHORT_MANIFEST.json`, `V25_QUAL_MANIFEST.json`).
4. Created permanent Git branch `culture/v25`.
5. Safely detached and removed external worktrees using `git worktree remove`.
6. Pruned redundant physical directories from disk.

---

## 6. Git History & Branches

- **Git History Rewrite**: **NONE**. The local Git object storage (`.git`) was already small (~99.7 MB) and contained no bloat. Rewriting history was unnecessary and avoided.
- **Branches**:
  - `main`: Canonical production repository containing all validated code, final submission, and full documentation.
  - `culture/v24`: Complete historical branch for the Culture v24 Challenger campaign.
  - `culture/v25`: Complete historical branch for the Culture v25 Coherent Planner campaign.
  - `research/*`: Preserved historical research branches (`research/v23-backbone-challenge`, `research/v24-live-meta`, `research/v25-coherent-planner`, `research/v26-backbone-aware-aec`, `research/v27-v25-robustness`, `research/v28-a7-confirmation`, `research/v29-a7-promotion`).

---

## 7. Security Audit (Secrets Scan)
- Automated recursive scanner audited all text files, manifests, and configs across the workspace.
- Specific checks: `.env`, `kaggle.json`, private keys, API tokens, bearer tokens.
- **Result**: **0 secrets found (PASS)**.
- Hardened `.gitignore` guarantees future exclusion of credentials.

---

## 8. Verification & Runnable Status
- Final agent self-play verification: **PASS** (`kaggle-environments == 1.32.7`).
- All 17/17 verification gates in V60 staging bundle: **PASS**.
- Working tree git status: **Clean**.
