# PHASE022R1 — SEMANTIC EQUIVALENCE (old vs repaired, §6)

**Date**: 2026-09-20
**Nature**: software-equivalence test, NOT an economic experiment. The cohort
`249376..249395` (already consumed by Phase 022) is reused here solely to
prove the loader repair is semantically transparent.

## 1. Method

- **Known-working implementation (dev)**: repository working-tree `aec/` via
  normal imports (= V22's packaged `aec/`, diff-identical).
- **Repaired package (rep)**: `submission_aec_v22r1.tar.gz` entrypoint under
  bare-`exec` loader semantics (no `__file__`, repo-isolated subprocess,
  cwd=`/tmp`, exec_dir on path during exec only).
- **Design**: 20 seeds × 2 seats = 40 games per implementation (treatment vs
  frozen V3, same bytes both sides, fresh per game), `kaggle_environments`
  1.32.7, `episodeSteps=720`, each game in its own process.
- **Compared exactly per step** (10 fields × 28,800 step records): both
  seats' recorded actions, V3 base action (backbone cache snapshot),
  decision, detected events, opportunity count, abstain reason, committed
  patch ID, committed mechanism, full candidate list (IDs, mechanisms,
  safety/economic flags, deltas); plus statuses, terminal rewards, paired
  deltas, telemetry counts.
- **Control**: dev-vs-dev cross-process repeats (2 seeds × 2 seats) prove the
  engine+harness deterministic, so any dev-vs-rep difference would be
  repair-caused.

## 2. Result: 40/40 EXACT — zero differences

Control diffs: 0/4. Equivalence diffs: **0/40 matches**, 0/28,800 step
records, 0/288,000 field comparisons. No STOP condition triggered; no
rationalization needed.

| Seed | Seat | Dev trt | Dev ctrl | Dev Δ | Rep trt | Rep ctrl | Rep Δ | Commits dev/rep | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 249376 | 0 | 101,807.00 | 101,807.00 | +0.00 | 101,807.00 | 101,807.00 | +0.00 | 0/0 | EXACT |
| 249376 | 1 | 101,807.00 | 101,807.00 | +0.00 | 101,807.00 | 101,807.00 | +0.00 | 0/0 | EXACT |
| 249377 | 0 | 80,143.00 | 80,143.00 | +0.00 | 80,143.00 | 80,143.00 | +0.00 | 0/0 | EXACT |
| 249377 | 1 | 80,143.00 | 80,143.00 | +0.00 | 80,143.00 | 80,143.00 | +0.00 | 0/0 | EXACT |
| 249378 | 0 | 100,244.00 | 100,141.00 | +103.00 | 100,244.00 | 100,141.00 | +103.00 | 2/2 | EXACT |
| 249378 | 1 | 100,244.00 | 100,141.00 | +103.00 | 100,244.00 | 100,141.00 | +103.00 | 2/2 | EXACT |
| 249379 | 0 | 88,267.00 | 88,267.00 | +0.00 | 88,267.00 | 88,267.00 | +0.00 | 0/0 | EXACT |
| 249379 | 1 | 88,267.00 | 88,267.00 | +0.00 | 88,267.00 | 88,267.00 | +0.00 | 0/0 | EXACT |
| 249380 | 0 | 106,924.00 | 106,792.00 | +132.00 | 106,924.00 | 106,792.00 | +132.00 | 2/2 | EXACT |
| 249380 | 1 | 106,924.00 | 106,792.00 | +132.00 | 106,924.00 | 106,792.00 | +132.00 | 2/2 | EXACT |
| 249381 | 0 | 93,205.00 | 93,090.00 | +115.00 | 93,205.00 | 93,090.00 | +115.00 | 1/1 | EXACT |
| 249381 | 1 | 93,205.00 | 93,090.00 | +115.00 | 93,205.00 | 93,090.00 | +115.00 | 1/1 | EXACT |
| 249382 | 0 | 109,370.00 | 109,351.00 | +19.00 | 109,370.00 | 109,351.00 | +19.00 | 0/0 | EXACT |
| 249382 | 1 | 109,351.00 | 109,370.00 | -19.00 | 109,351.00 | 109,370.00 | -19.00 | 0/0 | EXACT |
| 249383 | 0 | 87,708.00 | 87,550.00 | +158.00 | 87,708.00 | 87,550.00 | +158.00 | 1/1 | EXACT |
| 249383 | 1 | 87,708.00 | 87,550.00 | +158.00 | 87,708.00 | 87,550.00 | +158.00 | 1/1 | EXACT |
| 249384 | 0 | 93,913.00 | 93,939.00 | -26.00 | 93,913.00 | 93,939.00 | -26.00 | 2/2 | EXACT |
| 249384 | 1 | 93,913.00 | 93,939.00 | -26.00 | 93,913.00 | 93,939.00 | -26.00 | 2/2 | EXACT |
| 249385 | 0 | 109,313.00 | 109,313.00 | +0.00 | 109,313.00 | 109,313.00 | +0.00 | 0/0 | EXACT |
| 249385 | 1 | 109,313.00 | 109,313.00 | +0.00 | 109,313.00 | 109,313.00 | +0.00 | 0/0 | EXACT |
| 249386 | 0 | 78,337.00 | 78,474.00 | -137.00 | 78,337.00 | 78,474.00 | -137.00 | 2/2 | EXACT |
| 249386 | 1 | 78,272.00 | 78,192.00 | +80.00 | 78,272.00 | 78,192.00 | +80.00 | 2/2 | EXACT |
| 249387 | 0 | 97,460.00 | 97,460.00 | +0.00 | 97,460.00 | 97,460.00 | +0.00 | 0/0 | EXACT |
| 249387 | 1 | 97,460.00 | 97,460.00 | +0.00 | 97,460.00 | 97,460.00 | +0.00 | 0/0 | EXACT |
| 249388 | 0 | 67,366.00 | 67,341.00 | +25.00 | 67,366.00 | 67,341.00 | +25.00 | 1/1 | EXACT |
| 249388 | 1 | 67,366.00 | 67,341.00 | +25.00 | 67,366.00 | 67,341.00 | +25.00 | 1/1 | EXACT |
| 249389 | 0 | 111,188.00 | 111,726.00 | -538.00 | 111,188.00 | 111,726.00 | -538.00 | 1/1 | EXACT |
| 249389 | 1 | 111,716.00 | 111,198.00 | +518.00 | 111,716.00 | 111,198.00 | +518.00 | 1/1 | EXACT |
| 249390 | 0 | 107,565.00 | 102,678.00 | +4,887.00 | 107,565.00 | 102,678.00 | +4,887.00 | 0/0 | EXACT |
| 249390 | 1 | 102,678.00 | 107,565.00 | -4,887.00 | 102,678.00 | 107,565.00 | -4,887.00 | 0/0 | EXACT |
| 249391 | 0 | 132,192.00 | 132,151.00 | +41.00 | 132,192.00 | 132,151.00 | +41.00 | 2/2 | EXACT |
| 249391 | 1 | 132,192.00 | 132,151.00 | +41.00 | 132,192.00 | 132,151.00 | +41.00 | 2/2 | EXACT |
| 249392 | 0 | 88,943.00 | 88,943.00 | +0.00 | 88,943.00 | 88,943.00 | +0.00 | 0/0 | EXACT |
| 249392 | 1 | 88,943.00 | 88,943.00 | +0.00 | 88,943.00 | 88,943.00 | +0.00 | 0/0 | EXACT |
| 249393 | 0 | 94,011.00 | 95,334.00 | -1,323.00 | 94,011.00 | 95,334.00 | -1,323.00 | 0/0 | EXACT |
| 249393 | 1 | 95,406.00 | 94,172.00 | +1,234.00 | 95,406.00 | 94,172.00 | +1,234.00 | 0/0 | EXACT |
| 249394 | 0 | 81,497.00 | 81,410.00 | +87.00 | 81,497.00 | 81,410.00 | +87.00 | 1/1 | EXACT |
| 249394 | 1 | 81,497.00 | 81,410.00 | +87.00 | 81,497.00 | 81,410.00 | +87.00 | 1/1 | EXACT |
| 249395 | 0 | 58,999.00 | 58,884.00 | +115.00 | 58,999.00 | 58,884.00 | +115.00 | 2/2 | EXACT |
| 249395 | 1 | 58,999.00 | 58,884.00 | +115.00 | 58,999.00 | 58,884.00 | +115.00 | 2/2 | EXACT |

## 3. Cross-engine corroboration (engineering evidence, not qualification)

All 40 KE/Linux (treatment, control, delta) triples reproduce the kagsim/
Windows Phase 022 ledger **exactly** (scripted check: 40/40). The two engines
agree bit-for-bit on this cohort — strong evidence that the researched
behavior is what the repaired artifact executes. This re-uses the consumed
cohort for a software comparison only; it is not new economic qualification
and touches no holdout.

## 4. Conclusion

The loader repair is semantically transparent: the repaired package executes
the same verified AEC behavior (same actions, base actions, events,
candidates, commits, mechanisms, rewards) as the known-working V22
implementation on every tested input.
