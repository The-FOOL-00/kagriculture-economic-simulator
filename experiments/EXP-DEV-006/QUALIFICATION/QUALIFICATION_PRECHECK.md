# PRECHECK: EXP-DEV-006 QUALIFICATION READINESS GATES
**Experiment**: EXP-DEV-006 Qualification (50050–50099, N=50)
**Date**: 2026-09-14
**Verdict**: **ALL 12 GATES PASS — AUTHORIZED TO EXECUTE**

| # | Gate | Expected | Observed | Status |
|---|------|----------|----------|--------|
| 1 | Qualification protocol frozen on disk | `QUALIFICATION_PROTOCOL.md` | SHA-256 recorded in `QUALIFICATION_PROTOCOL_HASH.txt` | PASS |
| 2 | Baseline (Sub 56146971) hash | `18402ec6…cb7eeb` | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` (recomputed from disk) | PASS |
| 3 | Treatment dev_006 hash (byte-identical to Discovery) | `06db94e5…44f5eb` | `06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb` | PASS |
| 4 | Diagnostic dev_005 hash | `f52b1686…e2a78` | `f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78` | PASS |
| 5 | Control (Sub 56146947) hash | `f651ccd2…fd8b8` | `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8` | PASS |
| 6 | Discovery protocol V1.5 hash (unchanged) | `e52a0570…7b04e8` | `e52a0570a8bc9cfeafe1165f49f4c9d77ef9a3b7aa030783f8aef7e9ee7b04e8` | PASS |
| 7 | AST zero-leakage audit (dev_006) | 0 violations | 0 violations (runner re-audits at launch) | PASS |
| 8 | One-factor runtime probe | exit 0, guard-only diff | `treatment_identity_probe.py` PASS: identical at 72/144/216, single permitted divergence at 288 | PASS |
| 9 | Simulator parity (§4 of task order) | 5/5 conditions | manifest 4/4 + validators 2/2 match; golden 47,520/47,520; DEV-005 replay 100/100 (219.6 s, re-run 2026-09-14); events 400/400; ENGINE_VERSION 1.32.7 | PASS |
| 10 | Seed provenance | virgin w.r.t. treatment | 50050–50099 certified in `QUALIFICATION_SEED_PROVENANCE.md`; quarantine guard covers all consumed ranges + holdout | PASS |
| 11 | Historical artifacts untouched | read-only | Baseline/control/DEV-004/DEV-005 hashes match frozen records; no writes to historical dirs; Discovery record unmutated | PASS |
| 12 | No Qualification result observed pre-freeze | zero | Freeze commit predates first seed execution (timestamps in manifest) | PASS |

**Simulator note**: Windows binary `kagsim.cp314-win_amd64.pyd` present under
`external_repos/kaggriculture-cppsim/` but not importable on Linux (`ModuleNotFoundError`,
confirmed this session); validated `kagsim_py` port (`__version__ 0.4.0.port1`,
`ENGINE_VERSION 1.32.7`, combined port-bytes SHA-256
`3ed2ab4ca3d30421a7b2d73a909951dc45283305d8752623c3267f0eabcb28a8`) used per task §4
with all parity conditions re-verified this session.

**Task-order "commit 06db94e5" note**: no such Git commit exists; `06db94e5…` is the SHA-256 prefix
of the frozen DEV-006 treatment file. The file on disk recomputes to the full frozen hash, matching
both the worktree and committed (`f42c72b`) Discovery manifest. No STOP triggered.
