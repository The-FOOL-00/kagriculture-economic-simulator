# V30 BASELINE FREEZE

Date: 2026-09-21. Engine: kaggle_environments 1.32.7.

## Frozen inputs (untouched by V30)

- V22R1: release commit `33763a8`, archive `submission_aec_v22r1.tar.gz`,
  SHA256 `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5`.
  Never modified, never re-packaged.
- V3: `submission_Vj_kc_v3.tar.gz`,
  SHA256 `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`.
  Loaded only via `aec/backbone/v3_adapter.py` (frozen).
- A7: `V27AblationAdapter("V27-ABL-A7")`, file SHA
  `18d2c8ea2cf826b0bef71c96988dba0c93d7dbcc73936a0c99f07cb0539e7ae9`.
  Step-0 50→30 wash rewrite only; all else V3-identical.
- V29 reference levels (seeds 340050..340050+39 (40-seed slice), now retired):
  A7vA7 == V3vV3 mean $94,574.78; A7-vs-V3 +$1,289.18 all EXTRACT.

## V30 seed governance

| Range | Status |
|---|---|
| 249530..249569 | V28 consumed (retired) |
| 249570..249577 | **V30 exploration gauntlet** (this campaign) |
| 249578..249579 | exploration buffer (unused unless needed) |
| 249580..249619 | **V30 confirmation reserve** (virgin; audit before use) |
| 340050..340050+39 | V29 consumed (retired) |
| 340090..340199 | protected holdout remainder — NEVER TOUCH |
| 214200..214249 | GATE0 holdout — NEVER TOUCH |
| 340300..340349 | EXP-AEC-004 retired — NEVER REUSE |

`scripts/v30_gauntlet.py` hard-refuses 340050..340199, 214200..214249,
340300..340349. Prior max executed 249xxx seed-field in results/*.jsonl
before V30 was 249569 (V28); `249570` literals in v28 scripts are exclusive
`range()` bounds, and EXECUTION_LOG `249632` is a timestamp fraction.

## V30 isolation standard

Fresh process per match (pool, max_tasks_per_child=1); serial mode for
parity spot-checks; exec-isolated namespaces per agent load; no AEC.
