# V29 — BASELINE FREEZE (V28 verified end-state + V29 branch point)

V29 branches from the verified V28 end-state. No V28 artifact is
modified; all V29 artifacts are new files prefixed `V29_` / `v29_` /
`test_v29_`.

## 1. V28 end-state (immutable input)

| Item | Value |
| :--- | :--- |
| HEAD at V29 start | `91073c8a7c55611c44bde5704bdca26a3190ef7d` (v28-prereg) |
| V27 checkpoint | `b44bf5b60f772f486267347f81322899776494f8` |
| V28 prereg SHA256 | `54aff6b4c56adb811f3fdc3767a3e415bc2d1c5df149f4cb50fc1f656a4ddb43` |
| V28 cohort-manifest SHA256 | `fe20d1c3fd3ceedd2e2f2abdf21535bfab01c42097581f1fc449de6eccaf5716` |
| V28 raw-result SHA256 | `2efb4446f35da094a1fb9b3c9f65024bcedd60f648b4d5a4a799180165f21082` (80/80 rows) |
| V28 paired-CSV SHA256 | `a0600fc86f0156a896b9ca6d3309491f8b5accd3dedd7784b7c54af5aecc1555` |
| V28 outcome | OUTCOME A — A7 CONFIRMED (6/6 gates; mean +$1,389.99, median +$1,286, 78W/2L/0T, seed CI [+$1,188.18, +$1,591.80]) |

Uncommitted V28 worktree files at V29 start (read-only inputs, never
edited on the V29 line): `V28_CONFIRMATION_REPORT.md`,
`V28_COUNTERFACTUAL_AUDIT.md`, `V28_FINAL_REPORT.md`,
`V28_GATE_RESULTS.md`, `V28_MECHANISM_AUDIT.md`, `V28_TAIL_AUDIT.md`,
`results/v28_raw_results.jsonl`, `results/v28_paired_results.csv`,
`results/v28_farm_gaps.jsonl`, `scripts/v28_analyze.py`,
`scripts/v28_counterfactual.py`, `scripts/v28_mechanism.py`,
`scripts/v28_mechanism_detail.py`, `scripts/v28_verify_farmgaps.py`.

## 2. Frozen bytes (re-verified before the first V29 holdout match)

| Artifact | Path | SHA256 |
| :--- | :--- | :--- |
| A7 source | `aec/backbone/v27_ablation_adapters.py` | `18d2c8ea2cf826b0bef71c96988dba0c93d7dbcc73936a0c99f07cb0539e7ae9` |
| P3 adapter base | `aec/backbone/v25_p3_adapter.py` | `ce8169e95e86bd338b32dada48ba3fa0216bdeea4cebdd34a0264fe18a9f5195` |
| V3 adapter | `aec/backbone/v3_adapter.py` | `a0a9fd2c2ce1abe2de7e871e7fd9deec647df9863179c19cf1b94fc5ed2e3135` |
| Backbone interface | `aec/backbone/interface.py` | `1a1c5ec7cbc097c13d60eeed98ed98749f11cad7456c368366513dc7eeda4091` |
| Backbone utils | `aec/backbone/utils.py` | `53f9277406162cf1789d5dceb944f147ead85d65d52647350533a1c1c7684404` |
| AEC config | `aec/config.py` | `14c3a22c0141b770efe43244afe77f7ed27064e0256bdb9f8b40750e3b2eabae` |
| V3 payload | `submission_Vj_kc_v3.tar.gz` | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` |
| V25 P3 file (hash only) | `candidates/v25_p3_unified.py` | `13292582c8cc796bc11ccebff9684fbec45cfb97d936fb9e85e4e9bb4dbea179` |

All seven A7/V3 dependency hashes are byte-identical to the V28 freeze
record (`V28_A7_FREEZE.md` §2). A7 bytes unchanged since V27 Stage A.

## 3. Simulator / harness / runtime

| Item | Value |
| :--- | :--- |
| Engine | `kaggle_environments==1.32.7` (project `.venv`) |
| Python | `3.14.4` (project `.venv`) |
| V29 runner | `scripts/v29_holdout_tournament.py` (new file; four-arm; pool `max_tasks_per_child=1`, workers=9) |
| V29 analyzer | `scripts/v29_analyze.py` (new file; preregistered math only) |
| Required deps | `kaggle_environments==1.32.7`, `scipy` (t-critical/Wilcoxon; frozen fallback `t=2.0227` if absent), `pytest` |

The V28 runner/analyzer scripts are NOT reused by import for holdout
matches; the V29 runner re-implements the identical match protocol
(fresh adapters per match, mirrored seats, checkpointed JSONL) with
four-arm support and per-record digests. V28 scripts remain untouched.

## 4. V22R1 (competition fallback; unrelated to V29 evaluation)

| Item | Value |
| :--- | :--- |
| Tag | `v22r1` → commit `33763a8f58b17bc3a32735c2a322883b78ed3778` |
| Archive | `submission_aec_v22r1.tar.gz` |
| SHA256 | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` |

Re-verified at V29 start (see `V29_QUAL_MANIFEST.json`). Not modified,
rebuilt, retagged, repackaged, or resubmitted at any point in V29.

## 5. V29 branch discipline

- V29 work happens on new files only; the `git diff` of every path
  listed in §2 and of all `V28_*` / `v28_*` / `results/v28_*` files
  must be empty at V29 close (verified by `test_v29_freeze.py`).
- `V29_PREREGISTRATION.md` is committed BEFORE the first holdout match
  and never edited after holdout results appear.
- Holdout slice `340050..340089` is consumed by V29; remainder
  `340090..340199` stays protected (see `V29_COHORT_MANIFEST.json`).
