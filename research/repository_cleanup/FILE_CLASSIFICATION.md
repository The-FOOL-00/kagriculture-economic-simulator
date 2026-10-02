# KAGRICULTURE REPOSITORY FILE CLASSIFICATION

This document provides the canonical taxonomy of files and directories across the Kagriculture workspace in accordance with archival and repository engineering standards.

---

## Classification Taxonomy

| Class | Designation | Description | Disposal / Target |
| :---: | :--- | :--- | :--- |
| **A** | **Must Preserve / Commit** | Essential source code, candidate agents, final submission, benchmark harnesses, research reports, postmortems, configurations, and core engine code. | Commit to canonical `main` branch. |
| **B** | **Preserve / Archive** | Important historical milestones and research branches (Culture v24, Culture v25, Challenger suites). | Preserved on dedicated git branches (`culture/v24`, `culture/v25`). |
| **C** | **Regenerable** | Derived metrics, small experiment JSONs, and summary plots that can be reconstructed from source scripts. | Track compact summaries; exclude large redundant outputs. |
| **D** | **Exclude from Git (External Data)** | Multi-gigabyte raw replay corpora and large training datasets with defined reacquisition pipelines. | Exclude via `.gitignore`; record acquisition source, schema, and hashes in `docs/DATASETS.md` and `data/MANIFEST.csv`. |
| **E** | **Safe to Delete** | Disposable caches, virtual environments, temporary episode dumps, compilation caches, and scratch files. | Delete to free ~18 GB of disk space. |
| **F** | **Sensitive** | API tokens, credentials, private keys, `.env` files, and Kaggle authentication secrets. | Strictly forbidden from git; scanned and verified clean. |

---

## Directory & Component Breakdown

### 1. Agents, Candidates & Submissions
| Path | Class | Size | Notes |
| :--- | :---: | :---: | :--- |
| `candidates/v49_meta_fusion/main.py` | **A** | 865 KB | Final Incumbent / Production Submission (SHA256: `8CAFF630...`) |
| `candidates/v50_dead_action_guard/` | **A** | ~870 KB | Post-submission research candidate |
| `candidates/v51_blocked_repair/` | **A** | ~870 KB | Post-submission research candidate |
| `candidates/v45_adversarial_market/` .. `v48_challenger/` | **A** | ~2 MB | Evolution milestones V45-V48 |
| `candidates/closed_loop_architecture/` | **A** | ~1 MB | Closed-loop planner framework |
| `candidates/v30_a7_standalone/` .. `v44_economic_portfolio/` | **A** | ~3 MB | Historical candidate lineage V30-V44 |
| `submissions/v49_meta_fusion_submission/` | **A** | 865 KB | Production submission directory |
| `submissions/v49_meta_fusion_20260929_2212.zip` | **A** | 522 KB | Packaged competition submission archive |
| `team_submissions/submission_Vj_kc_v24.tar.gz` | **A** | 665 KB | Teammate Vj Culture v24 bundle |
| `team_submissions/submission_Vj_kc_v27.tar.gz` | **A** | 665 KB | Teammate Vj Culture v27 bundle |
| `final_submission/` | **A** | 150 KB | Earlier V35/V37 milestone submission archive & reports |
| `submission_final_v35/` | **A** | 418 KB | V35 standalone agent |
| `main.py` | **A** | 22 KB | Root agent entrypoint / evaluation wrapper |
| `agent_frontier.py`, `agent_hamburger.py`, `agent_moon.py`, `agent_v14.py` | **A** | ~100 KB | Benchmark reference agents |

---

### 2. Research History & Synthesis (V40 - V60)
| Path | Class | Size | Notes |
| :--- | :---: | :---: | :--- |
| `research/final_synthesis/` | **A** | ~500 KB | Definitive research postmortem, decision ledger, and causal traces |
| `research/v40/` through `research/v59/` | **A** | ~40 MB | Source code, experiment definitions, evaluation scripts, and reports |
| `research/v60/` (scripts, reports, analysis) | **A** | ~15 MB | Sep Elite benchmark scripts and recovery protocols |
| `V46_*.md`, `V47_*.md` (root markdown reports) | **A** | ~300 KB | Strategic reports (adversarial, ladder, golden property, evidence reconciliation) |
| `research/v60/data/tmp_ep_jsons/` | **E** | 2,527 MB | Temporary raw downloaded JSON episodes (reacquirable via scripts) |
| `research/v45/artifacts/market_pressure_dataset.pt` | **D** | 116 MB | Derived ML tensor dataset |
| `research/v45/artifacts/opponent_market_history.jsonl` | **D** | 108 MB | Derived opponent replay market logs |
| `research/v58/data/replay_database.jsonl` | **D** | 114 MB | Derived August replay database |

---

### 3. Core Engine, Infrastructure & Tooling
| Path | Class | Size | Notes |
| :--- | :---: | :---: | :--- |
| `engine/`, `aec/` | **A** | ~4 MB | Core simulation engine and AEC environment wrapper |
| `scripts/` | **A** | ~2 MB | Utility, benchmark, and tournament runner scripts |
| `configs/` | **A** | ~1 MB | Experiment configurations and hyperparameters |
| `tests/` | **A** | ~8 MB | Comprehensive test suites and assertions |
| `docs/` | **A** | ~500 KB | Project architecture, datasets, provenance, and final artifacts |
| `.gitignore`, `README.md`, `CHANGELOG.md` | **A** | ~50 KB | Repository metadata and guidelines |

---

### 4. Large External Datasets & Replay Corpora (Class D)
| Path | Class | Size | Reacquisition Method |
| :--- | :---: | :---: | :--- |
| `live_data/episodes_v31r2/` | **D** | 6,070 MB | Downloadable via Kaggle API / recorded in `docs/DATASETS.md` |
| `replays/` (live_tournament, Aethel_prime_v1, Apex_v4) | **D** | 3,949 MB | Kaggle competition tournament replay corpus |
| `external_repos/lixingtao123-Kaggriculture/online_replays/` | **D** | 1,456 MB | Teammate public replay dump |

---

### 5. Disposable Caches, Virtual Environments & Scratch Bloat (Class E)
| Path | Class | Size | Reason for Deletion |
| :--- | :---: | :---: | :--- |
| `.venv/` | **E** | 1,219 MB | Local Python virtual environment (27,898 files); reproducible via `requirements.txt` |
| `scratch/replays/` | **E** | 1,028 MB | Redundant local scratch replay copies |
| `scratch/v39/live/replays/` | **E** | 896 MB | Redundant V39 scratch replays |
| `scratch/fast_provenance_hits.json` | **E** | 214 MB | Intermediate scratch search dump |
| `scratch/forensic_telemetry_dump.json` | **E** | 66 MB | Intermediate telemetry dump |
| `results/v32_p2_bc_legs.jsonl` | **E** | 221 MB | Giant intermediate trajectory dump |
| `results/v27_trajectories.jsonl` | **E** | 160 MB | Giant intermediate trajectory dump |
| `results/v27_fresh_trajectories.jsonl` | **E** | 128 MB | Giant intermediate trajectory dump |
| `**/__pycache__/`, `**/.pytest_cache/` | **E** | ~15 MB | Python execution bytecode and test caches |

---

### 6. Historical Branches & Culture Worktrees (Class B)
| Worktree / Branch | Destination | Preserved Content | Size on Disk (Cleaned) |
| :--- | :--- | :--- | :---: |
| `Kagriculture-v24` (`research/v24-live-meta`) | `culture/v24` branch | Challengers C1, C2, C3, reports, bottleneck matrix, manifests | ~15 MB |
| `Kagriculture-v25` (`research/v25-coherent-planner`) | `culture/v25` branch | Planners P1, P2, P3, macro candidates, confirmation reports, manifests | ~15 MB |

---

### 7. Secrets & Security (Class F)
- Scanned for `.env`, `kaggle.json`, private keys, API tokens across whole tree: **0 secrets found**.
- Hardened `.gitignore` guarantees future exclusion of credentials.
