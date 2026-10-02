# V28 — BASELINE FREEZE (V27 checkpoint + V28 branch point)

## 1. V27 checkpoint (immutable)

| Item | Value |
| :--- | :--- |
| Checkpoint commit | `b44bf5b60f772f486267347f81322899776494f8` |
| Branch at commit | `research/v27-v25-robustness` |
| Parent | `33763a8f58b17bc3a32735c2a322883b78ed3778` (v22r1 release) |
| Files changed | 77 (72 added, 5 modified) |
| V28 branch | `research/v28-a7-confirmation` (from `b44bf5b`) |

## 2. Verification performed BEFORE the checkpoint

- V22R1: tag commit `33763a8…` ✓, archive
  `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` ✓
- V3 tarball `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` ✓
- V25 P3 `13292582c8cc796bc11ccebff9684fbec45cfb97d936fb9e85e4e9bb4dbea179` ✓
- Engine `kaggle_environments==1.32.7` (project `.venv`) ✓
- Tests: 45/45 green (26 V27 + 19 V26 regression) in 57s ✓
- Vendored V25/V26 checkpoints: all 4 SHA256 match `V27_BASELINE_FREEZE.md` §5 ✓
- Result reproduction: discovery 40 @ −398.05 ✓, confirmation 40 @ −469.85 ✓,
  ablation 1080 (A7 combined mean +1496.88 = (1450.8+1543.0)/2 ✓),
  farm gaps 60 ✓, historical 120 ✓, ledger 200 ✓, F1 replay 40 @ +453.77 ✓

## 3. Result-file hashes at freeze time (committed unless noted)

| File | SHA256 |
| :--- | :--- |
| `results/v27_discovery_matches.jsonl` | `87733720047b22fbcc84531b5623ed90e07a29f7b50a93e23b589f547fb3c5a2` |
| `results/v27_confirmation_matches.jsonl` | `b1b6a403a692eba375e8b5371769d777d43b4dc02b6b487ee760027957273671` |
| `results/v27_ablation_matches.jsonl` | `bf8d20e1c67913debbfaca289dfcd081ef59da18a2ff11928a31431ccf69f550` |
| `results/v27_ledger.jsonl` | `b81a70d923007a095605980038c541d830287577905df43c3f02a1e2262eaa91` |
| `results/v27_historical_matches.jsonl` | `3cb402e757e445a065f674ca36089bf5ec8fba13ccd5369c935a466b965eb1f6` |
| `results/v27_farm_gaps.jsonl` | `14cb255667b6edac7edc2c9717d590c9e5a72d80f587869fb00037992656bf48` |
| `results/v27_f1_conf_replay.jsonl` | `53d2c8cb866b6f4c47513ac538578ec302b221b080768df87b511befd77b96fd` |
| `results/v27_trajectories.jsonl` (161M, worktree-only) | `844bf29ca73619b34924d55990938d1bf9befe487e48532bccbebad3de4dbbf3` |
| `results/v27_fresh_trajectories.jsonl` (129M, worktree-only) | `9b6f3205447a22cfe4ae49b3050081b925f27b41bc05af378e1bd6c2ab48eed8` |

The two large trajectory files are intentionally excluded from git
(`V27_QUAL_MANIFEST.json` lists them as uncommitted); the SHA256 values
above are their immutable snapshot reference.

## 4. Deliberately NOT in the checkpoint

- `scratch/` (dev scratch, not V27 evidence)
- `external_repos/` submodule pointer drift (untouched, left as-is)
- `__pycache__/`, `.venv/`, `*.json` outside the force-added manifests

## 5. V27 results are now immutable

No V27 file may be edited retroactively on the V28 branch. All V28
artifacts are new files prefixed `V28_` / `v28_` / `test_v28_`.
