# V29 — A7 FREEZE (promotion candidate under review; byte-identical to V28)

A7 is the exact `V27-ABL-A7` variant committed at the V27 checkpoint,
instantiated with the identical flag combination V27 measured and V28
confirmed. It is NOT reconstructed, optimized, refactored, retuned, or
"safeguarded" in any way.

## 1. Identity (unchanged from V28)

| Item | Value |
| :--- | :--- |
| Candidate label | `A7` (= `V27-ABL-A7`, frozen bytes) |
| Source path | `aec/backbone/v27_ablation_adapters.py` |
| Class | `V27AblationAdapter(variant="V27-ABL-A7")` |
| Git commit | `b44bf5b60f772f486267347f81322899776494f8` |
| File SHA256 | `18d2c8ea2cf826b0bef71c96988dba0c93d7dbcc73936a0c99f07cb0539e7ae9` |
| Source size | 7140 bytes |
| Drift since V27 Stage A | zero (matches `V27_DISCOVERY_REPORT.md` §5 and `V28_A7_FREEZE.md` §1) |

## 2. Flag vector (the entire A7 configuration; all frozen)

| Flag | Value |
| :--- | :--- |
| `call_v3_at_step0` | `True` |
| `open_units` | `30` |
| `dispatch` | `False` |
| `rewrite_step0_wash` | `True` |

Behavior: at game-step 0 only, call V3 normally; if its market action
is exactly `[BUY_PRODUCT WHEAT 50, SELL WHEAT 50]`, resize both legs to
30; every other step and every other shape bit-identical to V3. No AEC,
no market timing, no supervisor, no seed-specific behavior, no V25
behavior (A7 inherits only the hermetic V3 loader).

## 3. Prohibited changes (all enforced by `test_v29_freeze.py`)

No change to: source bytes, constants, initialization, the 30-unit
mechanism, cash thresholds, melon timing, route execution, worker
dispatch, fallback logic, opponent adaptation, safeguards, or the flag
vector. The V29 runner asserts the §1 SHA256 plus all six dependency
hashes (`V29_BASELINE_FREEZE.md` §2) at every process startup and
refuses to run on mismatch.

## 4. Per-record digest rule (every V29 match, all four arms)

Each raw record stores:

- `a7_digest` = SHA256 of `aec/backbone/v27_ablation_adapters.py`
- `v3_digest` = SHA256 of `submission_Vj_kc_v3.tar.gz`
- `sim_digest` = adapter-dependency digest bundle (P3-adapter, V3-adapter, interface, utils, config — see runner `SIM_DIGESTS`)
- `harness_digest` = SHA256 of `scripts/v29_holdout_tournament.py` at run time (recorded, not asserted, so the audit trail is self-describing)
- `engine_version` = `"1.32.7"`
- `cand_variant` + the 4 flag values (A7 arms) / `"V3_STANDALONE"` (V3 arms)
- `step0_rewritten` / `step0_unexpected_shape` (A7 arms only)

Any record whose digests differ from the frozen values is not a V29
record. The analyzer rejects files containing such records.
