# PHASE022R1 — FINAL REGRESSION (release)

**Date**: 2026-09-20
**Interpreter**: project `.venv` (`kaggle-environments` 1.32.7, `pytest` 9.1.1)
**Code state**: worktree code byte-identical to HEAD (LF); only
docs/`.gitignore`/new release files differ. No code change in this
finalization, so no genuine regression is possible from release activity.

## Literal suite invocation

`pytest tests/aec -q` on Linux: collection interrupted — 5 modules import
the Windows-only engine module `kagsim`, absent on this platform:

- `test_exp_aec_004_isolation.py`
- `test_market_coupling_parity.py`
- `test_phase014_headroom_probe.py`
- `test_phase022_adversarial_stress.py`
- `test_trace_equivalence.py`

`ModuleNotFoundError: No module named 'kagsim'` at import; zero tests ran
in that invocation. Pre-existing release-environment limitation, already
disclosed in the R1 audit ("V22 full-suite re-execution impossible on
Linux (Windows-only kagsim)"). Not a code regression; no code touched.

## Runnable subset (5 kagsim-bound modules ignored)

Command: `pytest tests/aec -q` + `--ignore` × 5 (listed above).

- **Total collected**: 759
- **Passed**: 759
- **Failed**: 0
- **Runtime**: 69.95s (0:01:09)

Includes the release-critical suites green:

- `test_phase022r1_competition_loader.py`: 3 passed (static `__file__`
  scan, short game, full 720-step DONE game with real commits)
- `test_phase022r1_safety_predicates.py`: 7 passed
  (adversarial safety regression)
- 749 neighboring existing tests: all passed (no collateral)

A system-interpreter (`/usr/bin/python3`) trial run failed only the 2
loader subprocess tests for lack of `kaggle_environments` outside the
`.venv` — harness-environment artifact, resolved by using the project
`.venv`; not recorded as a code failure.

## Verdict

PASS. No failing regression tests in the release on the qualified
interpreter; the only exclusions are the pre-existing kagsim-bound
environment constraint.
