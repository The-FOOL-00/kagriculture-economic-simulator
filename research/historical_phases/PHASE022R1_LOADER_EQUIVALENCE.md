# PHASE022R1 — LOADER EQUIVALENCE (three-mode smoke test, §7)

**Date**: 2026-09-20
**Question**: does the repaired artifact behave identically under (A) exact
competition-loader simulation, (B) normal development execution, and (C) the
actual competition environment path?

## 1. Modes

| Mode | How the agent is loaded | What ran |
| --- | --- | --- |
| A — exact competition-loader sim | `exec(source, {"__name__": "__main__"})`, no `__file__`, exec_dir on path during exec only (mirrors `KE agent.py:get_last_callable`); resulting callable drives the game | §6 matrix rep phase (40 games, 249376..249395 × seats), regression tests, QA bare-exec probe |
| B — normal development execution | Repository working-tree `aec/` via normal imports; `AECExecutor` drives the game | §6 matrix dev phase (40 games, same cohort/seats/opponent), timing probes |
| C — actual competition environment | File path passed to `kaggle_environments` `env.run([path, ...])`; KE execs internally (the true competition path) | Packaged QA: full game vs starter + head-to-head vs V3 reference (both `debug=True`), packaged determinism repeat |

All modes: `kaggle_environments` 1.32.7, `episodeSteps=720`, Linux, no
network, no repo dependence for A/C (subprocess/clean-dir isolated).

## 2. Same-configuration comparison (seed 249376, AEC seat 0, V3 seat 1)

| Mode | AEC reward | V3 reward | Status | Source |
| --- | --- | --- | --- | --- |
| A (bare exec) | $101,807.00 | $101,807.00 | DONE/DONE | §6 matrix `rec_rep_249376_0` |
| B (dev import) | $101,807.00 | $101,807.00 | DONE/DONE | §6 matrix `rec_dev_249376_0` |
| C (KE file path) | $101,807.00 | $101,807.00 | DONE/DONE | packaged QA head-to-head |

All three initialize successfully, execute real AEC behavior (719 decisions,
BACKBONE/ABSTAIN/COMMIT telemetry — no all-PASS corpse), terminate normally,
and agree exactly at reward level. (Also equals the kagsim ledger tie.)

## 3. Per-step cross-mode equality

- A vs B: every per-step record compared exactly across all 40 games (§6
  comparator: both seats' actions, V3 base action, decision, events,
  candidates, commits) — result in `PHASE022R1_SEMANTIC_EQUIVALENCE.md`.
- C vs A: two Mode-C games captured per-step and diffed against the Mode-A
  records for the same (seed, seat, opponent) — (249376, seat 0, tie game)
  and (249380, seat 1, 2-commit game): **0 step-differences across 1,440
  steps** (both seats' actions + rewards + statuses).
- C vs C: packaged determinism — full 720-entry P0 action sequences
  bit-identical across repeats (QA).

## 4. Verdict

**PASS.** All three modes initialize successfully, execute real AEC behavior
(719 decisions with BACKBONE/ABSTAIN/COMMIT telemetry — no corpse),
terminate normally (DONE/DONE), produce V3-scale output, and agree exactly:
A=B per-step on all 40 games (288,000 field comparisons, 0 diffs); C=A
per-step on 2/2 captured games (0 diffs); C=C action sequences bit-identical.
