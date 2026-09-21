# V28 — ISOLATION AUDIT (Phase 3, consumed seeds only)

Runner: `scripts/v28_isolation_audit.py`. Data:
`results/v28_isolation_audit.jsonl` (34 runs). Audit seeds 249431
(V27 primer-demo seed) and 249470 (V26 cohort seed) — both consumed.
The virgin cohort (249530+) was NOT touched.

## 1. Behavioral invariance matrix (rewards + action digests)

| Context | 249431 A7vV3 | 249470 A7vV3 | V3vV3 invariant? |
| :--- | :--- | :--- | :--- |
| A: V3→A7→V3→A7 same process (2 A7 runs) | 79233/77947 `54b0db47c91b` | 150987/149701 `e6e02390fe22` | yes (2/2) |
| B: A7→V3→A7→V3 same process (2 A7 runs) | identical | identical | yes (2/2) |
| C2: A7 after P3 primer, same process | identical | identical | C3 V3vV3 identical |
| D: fresh interpreter subprocess | identical (new pid) | identical (new pid) | — |
| E: pool, max_tasks_per_child=1 | identical (new pid) | identical (new pid) | — |
| F: seat flip (A7@1, subprocess) | 79233/77947, same digest | 150987/149701, same digest | seat-symmetric |

Verdict: **PASS — 7/7 A7vV3 runs invariant per seed; 5/5 V3vV3 runs
invariant per seed.** Execution order, prior-candidate history, worker
reuse, and process identity have zero effect on behavior.

## 2. V27 bug-pattern regression (P3 primer)

C1 ran P3vV3 immediately before A7vV3 in the same process (the exact
V27 contamination pattern). C2 A7vV3 is bit-identical to primer-free
runs. Cross-validation: C1 itself reproduces V27's history-free P3 row
on 249431 exactly (Δ +1145, digest `e631d38d…`). The stale-`main`
failure mode cannot recur: adapters `exec()` V3 into a fresh namespace
per instance and never touch `sys.modules`.

## 3. Static checks (§3 items 4–7, 11–15)

- `sys.modules['main']`: absent before AND after adapter construction
  (asserted); no `sys.modules`/`__import__` reference in any adapter,
  util, interface, or config file.
- Namespaces: 3 simultaneously-constructed adapters hold 3 distinct
  `__globals__` objects with distinct `__name__`s
  (`v25_p3_isolated_v3_<id>` × 2, `aec_v3_frozen_runtime`).
- RNG: no `random`/`numpy` use in adapters; V3 payload has zero
  `random`/`numpy` references (all 57 `seed` hits are crop-seed game
  domain: BUY_SEED, seeds inventory). Determinism is engine-seed-only.
- Env vars: zero `os.environ`/`os.getenv` in adapters and V3 payload.
- Filesystem: zero `open()` in V3 payload; the audit created no files
  except its own output JSONL (worktree diff verified).
- No global mutable candidate/simulator state: each adapter instance
  owns its V3 namespace; engine instances are per-match; V3 globals are
  only mutated through snapshot/restore in counterfactual probes
  (V26-tested, unused by the tournament path).

## 4. Conclusion

All 15 integrity items pass. The V28 tournament runs in pool mode with
`max_tasks_per_child=1` (fresh worker process per match) — ordering
dependence is structurally impossible, and the audit proves even
same-process reuse would be behaviorally inert.
