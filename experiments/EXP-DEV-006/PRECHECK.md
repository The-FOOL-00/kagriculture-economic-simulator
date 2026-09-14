# PRECHECK: EXP-DEV-006 DISCOVERY READINESS GATES
**Experiment**: EXP-DEV-006
**Date**: 2026-09-14
**Verdict**: **ALL 10 GATES PASS — AUTHORIZED TO EXECUTE**

| # | Gate | Expected | Observed | Status |
|---|------|----------|----------|--------|
| 1 | Protocol V1.5 frozen on disk | `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_5.md` | SHA-256 `e52a0570a8bc9cfeafe1165f49f4c9d77ef9a3b7aa030783f8aef7e9ee7b04e8` | PASS |
| 2 | Baseline (Sub 56146971) hash | `18402ec6…cb7eeb` | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` (recomputed from disk) | PASS |
| 3 | Treatment dev_006 hash | `06db94e5…44f5eb` | `06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb` | PASS |
| 4 | Diagnostic dev_005 hash | `f52b1686…e2a78` | `f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78` | PASS |
| 5 | Control (Sub 56146947) hash | `f651ccd2…fd8b8` | `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8` | PASS |
| 6 | AST zero-leakage audit (dev_006) | 0 violations | 0 violations (prohibited modules/names scan) | PASS |
| 7 | One-factor proof | guard-only diff + probe exit 0 | `TREATMENT_DIFF_AUDIT.md` (byte-exact diff verified) + probe PASS | PASS |
| 8 | Simulator conditions (§8) | 5/5 | manifest 4/4 + validators 2/2 match; golden 47,520/47,520; DEV-005 replay 100/100 (202.3 s, re-run 2026-09-14); no source changes; ENGINE_VERSION 1.32.7 | PASS |
| 9 | Seed provenance | virgin block certified | `248000–248049` certified in `SEED_PROVENANCE.md`; quarantine guard covers 7 ranges | PASS |
| 10 | Historical artifacts untouched | DEV-004/DEV-005 + submissions read-only | Baseline/control hashes match frozen records; no writes to historical dirs | PASS |

**Simulator note**: Windows binary `kagsim.cp314-win_amd64.pyd` present but not loadable on Linux; validated `kagsim_py` port (`__version__ 0.4.0.port1`, `ENGINE_VERSION 1.32.7`) used per §8 with all conditions re-verified this session.
