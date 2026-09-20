# PHASE022R1 — DETERMINISM AUDIT (genuine per-turn replay, §14)

**Date**: 2026-09-20
**Scope claimed (and only this)**: repeated executions with identical seed,
configuration, code, and loader produce identical per-turn actions, V3 base
actions, decisions, commit/abstain outcomes, mechanisms, and terminal rewards.
No "720/720" phrasing is used: a 720-step KE game contains 719 agent
decisions (terminal entry has no agent call — probed live this session).

## 1. What V22 checked vs what R1 checks

- V22: 4 aggregate fields (rewards, delta, commit counts) across 10
  comparisons — trajectory identity unverified.
- R1: every decision step compared across independent processes:
  both seats' actions, V3 base action, decision (BACKBONE/ABSTAIN/COMMIT),
  detected events, candidate IDs + mechanisms + flags, commit/abstain,
  terminal rewards, paired deltas.

## 2. Evidence

| Check | Scope | Result |
| --- | --- | --- |
| Dev-vs-dev cross-process repeats (control) | 2 seeds × 2 seats × 720 records | 4/4 IDENTICAL (engine + harness deterministic; zero RNG in V3/`aec/`; engine RNG is seed-keyed local instances) |
| Dev-vs-repaired per-turn equality (§6 matrix) | 40 games × 720 records × 10 fields = 288,000 comparisons | 0 differences |
| Packaged determinism (QA, Mode C repeats) | rewards + full 720-entry P0 action sequences, seed 249376 | bit-identical |
| Mode C vs Mode A per-step | 2 games × 720 steps (incl. a 2-commit game) | 0 differences |
| Load-invariance | rep 249380/0 under 6-way load vs clean rerun | identical rewards + actions (106924/106792) |

Total: every action, every selected mechanism, every commit/abstain, and
every terminal reward compared — all equal across all repeated executions.

## 3. Determinism foundations (verified, not assumed)

- `aec/`: no `random`/`numpy.random` imports (repo search).
- V3 payload: zero occurrences of `random`.
- KE 1.32.7 `kaggriculture`: gameplay RNG uses `random.Random(seed-derived)`
  local instances (deterministic per seed/day); the only unseeded
  `random.Random()` sits in the unused `random_agent` demo.
- AEC tie-breaking: deterministic `(-score, patch_id)` tuples; no wall-clock
  or hash-order dependence on the decision path (per-step equality across
  processes with different hash seeds would have caught `PYTHONHASHSEED`
  dependence — none found).

## 4. Verdict

**Deterministic at the per-turn level as scoped above.** The V22 aggregate
result is subsumed (all aggregate equalities also hold in R1 data).
