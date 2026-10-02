# V28 — SERIAL/PARALLEL AUDIT (Phase 6, consumed seeds only)

## 1. Runner-level subset (seeds 249436..249439 × 2 seats = 8 matches)

Same subset executed twice via `scripts/v28_confirmation_tournament.py`:

- serial mode (one process, sequential): 8/8 complete
- pool mode (9 workers, `max_tasks_per_child=1`): 8/8 complete

Comparison on (cand_reward, base_reward, action_digest, money_digest):
**8/8 MATCH, 0 mismatches.** Terminal rewards, action streams, and
money trajectories are bit-identical across execution modes.

## 2. Committed regression test (`tests/test_v28_parity.py`)

- `test_serial_pool_subprocess_parity`: consumed seed 249434/seat 0
  across serial, pool, and fresh-interpreter subprocess modes —
  identical rewards + action digest + money digest. Also asserts the
  A7 step-0 rewrite deployed (`step0_rewritten`, no unexpected shape).
- `test_deterministic_reward_and_digest`: same seed twice → identical.
- `test_checkpoint_resume_no_duplicates`: second invocation writes 0
  new rows; keys unique.

## 3. Isolation-audit cross-check

`V28_ISOLATION_AUDIT.md` contexts D (fresh subprocess) and E (pool)
agree with same-process runs on both audit seeds — an independent
second confirmation of mode invariance.

## 4. Conclusion

Serial/parallel/subprocess parity holds exactly. The tournament's pool
mode is validated; §17 STOP condition not triggered.
