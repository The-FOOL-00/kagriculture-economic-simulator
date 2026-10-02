# PHASE022R1 — SUBMISSION INTEGRITY (repaired release)

**Date**: 2026-09-20
**Release candidate**: `submission_aec_v22r1.tar.gz`
**SHA256**: `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5`
**Size**: 549,911 bytes (130 members)
**Packager**: `scripts/build_phase022r1_submission.py` (V22 packager untouched)
**Retired**: `submission_aec_v22.tar.gz` (`2b23bc22...`, kept on disk, never
overwritten; retirement record in `PHASE022_SUBMISSION_INTEGRITY.md` §4)

## 1. Content audit (clean extraction outside the repo, then inspected)

| # | Check (§19) | Result |
| --- | --- | --- |
| 1 | File list | 130 members: `main.py`, `config.py`, `submission_Vj_kc_v3.tar.gz`, `aec/` (package), `extracted_agents/dmitrii_lb2800/` (9 files) |
| 2 | Main entrypoint | `main.py:agent(obs, configuration)` — loader-safe (no unconditional `__file__`; tokenize-verified) |
| 3 | Code hash | Archive SHA `6b879b3e...` recorded in `PHASE022R1_SUBMISSION_SHA256.txt` + `PHASE022R1_QA_RESULTS.json` |
| 4 | V3 embedded payload | SHA `845e0d10...` bit-identical to frozen V3; `cmp`-identical to V22's payload |
| 5 | Mechanism configuration | Packaged `build_robust_qualified_config()`: enabled = exactly the 3 foundation mechanisms; `frozen_mode=True`; tranche/asset/multiworker flags False (asserted by QA from extracted code) |
| 6 | Imports | stdlib + shipped locals only; no heavy deps; no network modules (`socket/urllib/requests/http`) |
| 7 | Resources | V3 tarball + `unit_model.py` physics located without `__file__` assumptions |
| 8 | No `__file__` runtime requirement | Every code occurrence guarded (`globals().get`/`getattr`); bare-exec proven |
| 9 | No repository-only dependency | Subprocess-isolated tests prove packaged-only imports (`aec.__file__` under extraction dir) |
| 10 | No forbidden network access | Scan-clean (see row 6) |
| 11 | No unintended experimental module | Same member set as V22; research/quarantined code present-but-disabled exactly as in V22 (3-layer gating re-verified) |

`archive → clean extraction → competition-loader simulation` executed from
`/tmp` (outside the repo) in QA, regression tests, and the §6 matrix.

## 2. Freeze proof (V22 → V22R1 packaged diff)

`diff -r` of clean extractions of both archives:

- `aec/`: **IDENTICAL** (also identical to the working tree)
- `config.py`: **IDENTICAL**
- `extracted_agents/`: **IDENTICAL**
- `submission_Vj_kc_v3.tar.gz`: **IDENTICAL** (SHA `845e0d10...`)
- `main.py`: **only change** (31 → 110 lines: the loader-safe entrypoint)

No economic logic, threshold, mechanism, macro evaluator, candidate economics,
opportunity definition, commit economics, or safety-policy semantic changed.
Line endings: LF (V22's CRLF fixed at write time).

## 3. Hardened QA results (seed 249376, RELEASE_SMOKE_ONLY)

| Gate | Result |
| --- | --- |
| Bare-exec loader sim (no `__file__`) + step-0 action | PASS (valid dict action) |
| Full KE game vs starter (`debug=True`) | PASS — P0 DONE $185,041.00, P1 DONE $3,658.00, 53.5 ms/step (V3-scale bar $10,000; corpse $3,000 rejected by construction) |
| Head-to-head vs V3 reference | PASS — AEC $101,807.00 / V3 $101,807.00, both DONE (matches the kagsim ledger tie on 249376) |
| Packaged determinism | PASS — rewards AND full 720-entry P0 action sequences bit-identical across repeats |
| Portability/security scan | PASS (0 paths, 0 heavy/network deps) |

Raw record: `PHASE022R1_QA_RESULTS.json`.

## 4. Cross-engine corroboration (observed, not claimed as qualification)

The KE/Linux runs reproduce kagsim/Windows ledger values exactly where
compared: 249376 tie $101,807 (QA H2H), 249378 +$103, 249380 seat1
$106,924/$106,792 (§6 matrix). This corroborates engine consistency; it is
engineering evidence, not new economic qualification (no holdouts touched;
consumed cohort only).
