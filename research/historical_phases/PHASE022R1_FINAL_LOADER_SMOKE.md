# PHASE022R1 — FINAL LOADER SMOKE (release)

**Date**: 2026-09-20
**Artifact**: `submission_aec_v22r1.tar.gz`
**SHA256**: `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5`
**Engine**: `kaggle_environments` 1.32.7 (project `.venv`), Linux
**Seeds**: 249376 / 249380 (consumed cohort; RELEASE_SMOKE_ONLY).
No protected range touched.

## Method

Competition-style source execution of the frozen archive bytes:
`exec(source, {"__name__": "__main__"})` — no `__file__`, extraction dir
on `sys.path` during exec only (mirrors KE `get_last_callable`), repo
scrubbed from the path, clean cwd, no network. Executed via the committed
regression suite `tests/aec/test_phase022r1_competition_loader.py`
(3 tests) plus one short-game repeat probe for determinism.

## Results (all 7 contract points)

| # | Check | Result |
| --- | --- | --- |
| 1 | Source loads (no `__file__`, no exception) | PASS — tokenize scan: every `__file__` occurrence guarded; bare-exec load clean |
| 2 | Agent initializes | PASS — callable defined; packaged `AECExecutor` instantiated (`executor_alive`) |
| 3 | Real actions execute | PASS — full game: 719 decisions (BACKBONE/ABSTAIN/COMMIT), commits > 0, only foundation mechanisms |
| 4 | No degradation to all-PASS | PASS — `all_pass_corpse=false`; V3-scale reward (bar $10,000) |
| 5 | Full game reaches DONE | PASS — 720-step game, P0/P1 DONE/DONE, seed 249380 |
| 6 | Output is valid | PASS — `aec` + V3 opponent both proven loaded from packaged bytes; telemetry complete |
| 7 | Deterministic result | PASS — 12-step seed-249376 game run twice: statuses, rewards ($572/$572), decisions, commits bit-identical |

Suite verdict: `test_phase022r1_competition_loader.py`: 3 passed.

## Archive-content verification (same session)

- `tar -ztvf`: 130 members — `main.py` (loader-safe entrypoint),
  `config.py`, `aec/` package, `extracted_agents/dmitrii_lb2800/` (9 files),
  `submission_Vj_kc_v3.tar.gz` (SHA `845e0d10...`, verified).
- No dev-only dependency, no network imports, no absolute paths, no
  secrets, no debug files in packaged code (scanned).
- V22→V22R1 packaged diff: `main.py` ONLY (`diff -rq` of clean
  extractions); `aec/`, `config.py`, `extracted_agents/`, V3 payload
  byte-identical. No quarantined mechanism active (enabled == exactly
  the 3 foundation mechanisms; tranche/multiworker/funnel/boundary-safe/
  uncertainty flags all off — verified in worktree AND packaged configs).
- Packaged `aec/` vs release worktree `aec/`: content-identical; 3 files
  (`counterfactual/horizon.py`, `evaluation/__init__.py`,
  `opportunities/market.py`) retain CRLF bytes in the package vs LF in the
  worktree — line-ending only, zero content delta (verified modulo-CR).

## Freeze

The archive was not modified by this test (read-only extraction to
scratch dirs). Hash re-verified after the smoke run: unchanged.
