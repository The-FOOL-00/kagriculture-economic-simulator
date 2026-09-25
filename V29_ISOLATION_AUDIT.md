# V29 — ISOLATION AUDIT (Phase 5, consumed seeds only)

Runner: `scripts/v29_isolation_audit.py`. Data:
`results/v29_isolation_audit.jsonl` (44 runs, SHA256
`9b566ba855b04d9ac8ef17f0c702c105e58d44ddbfb4c78d3819c4915dcb44c3`).
Audit seeds 249431 (V27 primer-demo seed) and 249470 (V26 cohort seed)
— both consumed. The holdout slice (340050+) and the protected
remainder were NOT touched.

## 1. Seven-context regression matrix (brief §16)

| # | Context | Implementation |
| :--- | :--- | :--- |
| 1 | V3 after V3 | A3/B2/B4/C3 V3vV3 runs after V3vV3 in-process |
| 2 | A7 after V3 | A2/A4/B1/B3 A7vV3 runs after V3vV3 in-process |
| 3 | V3 after A7 | A3/C3 V3vV3 runs after A7vV3 in-process |
| 4 | A7 after A7 | B5/B6/C4 A7vA7 runs after A7vV3/A7vA7 in-process |
| 5 | Fresh subprocess A7/V3 | D-subprocess A1/A2/A3/A4 (independent interpreters) |
| 6 | Reversed scheduling | order B (A7→V3→A7→V3) vs order A (V3→A7→V3→A7) |
| 7 | Reused-vs-fresh parity | in-process A/B/C runs vs D-subprocess vs E-pool |

## 2. Invariance verdict (rewards + action digests)

| Group | Runs | Verdict |
| :--- | ---: | :--- |
| A7vV3 seat 0 (249431 / 249470) | 7 / 7 | INVARIANT |
| A7vV3 seat 1 (249431 / 249470) | 2 / 2 | INVARIANT |
| A7vA7 (249431 / 249470) | 5 / 5 | INVARIANT |
| V3vV3 (249431 / 249470) | 7 / 7 | INVARIANT |
| P3vV3 primer (249431 / 249470) | 1 / 1 | recorded (primer only) |

**PASS — every same-(kind, seed, seat) group is bit-identical across
all execution contexts.** Execution order, prior-candidate history
(including the exact V27 P3-primer contamination pattern), worker
reuse, and process identity have zero effect on behavior, on all four
V29 arms.

Cross-check: A7vV3 on 249431 reproduces V28's audit values exactly
(79233/77947); on 249470 (150987/149701). The V29 runner agrees with
the V28 runner on consumed seeds.

## 3. Static checks

- `sys.modules['main']`: absent before AND after adapter construction
  (asserted); adapters never touch `sys.modules`.
- Namespaces: 3 simultaneously-constructed adapters hold 3 distinct
  `__globals__` objects with distinct `__name__`s.
- No `random`/`numpy` use in adapters; no `os.environ` reads; no
  `open()` in the V3 payload (V28 finding, sources frozen since).

## 4. Conclusion

All 7 isolation contexts pass on all four arms. The V29 tournament
runs in pool mode with `max_tasks_per_child=1` (fresh worker process
per match) — ordering dependence is structurally impossible, and the
audit proves even same-process reuse would be behaviorally inert.
Preregistration §11(a) satisfied; §17 STOP condition not triggered.
