# V27 — STAGE A DISCOVERY REPORT (virgin 249490..249509)

Runner: `scripts/v27_prospective_tournament.py A` (frozen P3 vs frozen
V3, hermetic adapters, no AEC). Data:
`results/v27_discovery_matches.jsonl` (40/40 complete).

## 1. Result

| Metric | Value | Prereg gate (rehearsal) |
| :--- | ---: | :--- |
| Mean paired Δ | **−398.05** | > 0 FAIL |
| Median | −236.0 | > 0 FAIL |
| SD | 743.1 | — |
| W/L/T (exact-zero) | 12/28/0 | W>L FAIL |
| Positive rate | 0.300 | > 50% FAIL |
| Seed-positive rate | 6/20 | > 50% FAIL |
| Tail floor | −2,109 | > −10,000 PASS |
| Max | +570 (no tip) | — |
| Seat-identical | 20/20 | determinism ✓ |

Per-seed (seat0/seat1, all identical): 249490 −327; 249491 +570;
249492 −96; 249493 +202; 249494 +306; 249495 −245; 249496 −1,742;
249497 −289; 249498 −2,109; 249499 +231; 249500 −1,072; 249501 −1,581;
249502 −70; 249503 +437; 249504 −706; 249505 −565; 249506 −142;
249507 −227; 249508 −902; 249509 +366.

## 2. Regime-watchlist observation (exploratory)

The 249463 pattern (large t=288 lead → expansion tip) does NOT
replicate: all 40 t=288 money gaps are positive (+430..+1,369,
quantized) yet terminals are mostly negative; corr(g288, terminal) =
−0.17. Mid-game leads dissipate (mean-reversion); no tip event
occurred (max +570). The watchlist is closed as a positive predictor.

## 3. Farm checks

No |seat-diff| > $300 (all seat-diffs exactly 0) → per preregister §3,
no V3v3 spot checks run.

## 4. Analysis discipline

Analysis-only. No code, threshold, gate, seed, or analysis change
resulted from Stage A. No tuning of P3/V3/adapters/harness.

## 5. Post-Stage-A freeze (code record for Stage B)

| File | SHA256 |
| :--- | :--- |
| candidates/v25_p3_unified.py | 13292582c8cc796bc11ccebff9684fbec45cfb97d936fb9e85e4e9bb4dbea179 |
| submission_Vj_kc_v3.tar.gz | 845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943 |
| aec/backbone/v25_p3_adapter.py | ce8169e95e86bd338b32dada48ba3fa0216bdeea4cebdd34a0264fe18a9f5195 |
| aec/backbone/v3_adapter.py | a0a9fd2c2ce1abe2de7e871e7fd9deec647df9863179c19cf1b94fc5ed2e3135 |
| aec/backbone/v27_ablation_adapters.py | 18d2c8ea2cf826b0bef71c96988dba0c93d7dbcc73936a0c99f07cb0539e7ae9 |
| scripts/v27_prospective_tournament.py | 593c5068a2aeac7daa2d2e1f99621a9d84219df5577ebe728b0cf04c116ea2c9 |

Stage B runs with these exact bytes (runner asserts P3/V3/engine
hashes at startup).
