# V29 — CONFIRMATION REPORT (promotion-holdout verification record)

Verdict: **OUTCOME B — HOLDOUT POSITIVE BUT DECOMPOSITION WEAK:
A7 CONFIRMED AS A COMPETITIVE RESPONSE, NOT A GENERAL ECONOMIC
DOMINANCE CANDIDATE** (6/6 preregistered gates pass; decomposition
shows CREATE = $0 exactly, extract share 100%).

## Promotion checklist (preregistration §8)

| Requirement | Result |
| :--- | :--- |
| (a) Isolation regression 7/7 | PASS (`V29_ISOLATION_AUDIT.md`, 44 runs, all invariant) |
| (b) Serial/pool parity 8/8 | PASS (`V29_SERIAL_PARALLEL_AUDIT.md`, + subprocess parity in tests) |
| (c) Independent rerun 14/14 | PASS (`V29_INDEPENDENT_RERUN_AUDIT.md`) |
| (d) Digests frozen, all 160 records | PASS (analyzer asserts A7/V3/sim/engine on every row) |
| (e) No unexplained execution artifact | PASS (160/160 distinct pids+nonces; no errors) |
| (f) Mechanism measurable, rewrite 80/80 | PASS (100% telemetry; 80/80 canonical; 0 unexpected shapes) |
| (g) No catastrophic weakness | PASS (C = $0 exactly; veto requires C significantly < 0) |
| (h) No tail-dependence overlay | PASS (top-1 share 2.7%) |
| Six gates | 6/6 PASS (`V29_GATE_RESULTS.md`) |
| OUTCOME-B pattern (`Cbar≤0` or `E/M≥50%`) | **TRIGGERED (both: C=0, E/M=100%)** |

All six gates pass and all integrity checks pass, but the
preregistered decomposition pattern for OUTCOME B triggered on both
clauses. Per the decision mapping (§8), the classification is
OUTCOME B — deterministically, not by judgment call.

## What V29 establishes

1. A7 beats V3 head-to-head on a protected holdout: +$1,289 mean,
   80W/0L/0T, seed CI [+$1,284, +$1,294] — the third independent
   replication of the +$1.3k effect (V27 ≈+$1,451, V28 +$1,390).
2. The melon mechanism is universal on this slice (80/80 canonical)
   with 80/80 replication on every telemetry field.
3. A7 creates ZERO absolute economic value: A7vA7 ≡ V3vV3 to the
   dollar at every step on all 40 seeds. The edge is 100% positional
   (smaller-washer extraction, zero-sum at obs[1]: +$54/−$54).
4. The result is not tail-dependent (2.7% top-1 share), not
   farm-driven (gaps ≤ |$219|, zero losses), and fully reproducible
   (14/14 reruns, 160/160 fresh processes).

## Promotion status

A7 is NOT promoted to the standalone research-candidate tier. It
remains a CONFIRMED competitive mechanism against V3 — a solved
positional edge in the wash game, with no absolute-level dominance.
V22R1 (`33763a8` / `6b879b3e…`, re-verified untouched) remains the
competition fallback. No Kaggle submission was made or is authorized;
no AEC work was started; the protected remainder `340090..340199`
remains untouched (verified by test + analyzer assertions).
