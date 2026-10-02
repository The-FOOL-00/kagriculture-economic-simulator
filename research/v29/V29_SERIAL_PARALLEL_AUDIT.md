# V29 — SERIAL/PARALLEL AUDIT (Phase 6, consumed seeds only)

## 1. Runner-level subset (seeds 249436..249439 × Arms 1+2 = 8 matches)

Same subset executed twice via `scripts/v29_holdout_tournament.py`
(`--allow-consumed-qual`):

- serial mode (one process, sequential): 8/8 complete in 45.3s
- pool mode (9 workers, `max_tasks_per_child=1`): 8/8 complete in 28.1s

Comparison on (cand_reward, base_reward, action_digest, money_digest,
state_digest): **8/8 MATCH, 0 mismatches.** Terminal rewards, action
streams, money trajectories, and structural series are bit-identical
across execution modes. (Both modes agree the subset mean is +$1,286.00
on each arm — the canonical effect is visible even on consumed seeds.)

## 2. Committed regression tests

- `tests/test_v29_parity.py` (5 tests, all green):
  `test_serial_pool_subprocess_parity` (A1 across serial/pool/fresh-
  subprocess, incl. `step0_rewritten` assertion),
  `test_selfplay_parity_all_arms` (A3/A4 serial-vs-pool),
  `test_deterministic_reward_and_digest`,
  `test_selfplay_single_match_sufficiency` (re-run bit-identical —
  proves one self-play match per seed suffices),
  `test_checkpoint_resume_no_duplicates`.
- `tests/test_v29_isolation.py` (5 tests, all green): no-`main`
  contamination, distinct namespaces, P3-primer non-leakage,
  execution-order invariance, self-play order invariance.

## 3. Isolation-audit cross-check

`V29_ISOLATION_AUDIT.md` contexts D (fresh subprocess) and E (pool)
agree with same-process runs on both audit seeds across all four arms
— an independent second confirmation of mode invariance.

## 4. Conclusion

Serial/parallel/subprocess parity holds exactly on all arms. The
tournament's pool mode is validated. Preregistration §11(b) satisfied;
STOP condition not triggered.
