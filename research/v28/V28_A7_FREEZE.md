# V28 — A7 SOURCE FREEZE (exact V27 artifact, unmodified)

A7 is NOT reconstructed, reimplemented, or "cleaned up". It is the exact
`V27-ABL-A7` variant class committed at the V27 checkpoint, instantiated
with the identical flag combination V27 measured.

## 1. Identity

| Item | Value |
| :--- | :--- |
| V28 candidate label | `A7` (= `V27-ABL-A7`, frozen bytes) |
| Source path | `aec/backbone/v27_ablation_adapters.py` |
| Class | `V27AblationAdapter(variant="V27-ABL-A7")` |
| Git commit | `b44bf5b60f772f486267347f81322899776494f8` |
| File SHA256 | `18d2c8ea2cf826b0bef71c96988dba0c93d7dbcc73936a0c99f07cb0539e7ae9` |
| Source size | 7140 bytes |
| Cross-check | identical to post-Stage-A freeze record (`V27_DISCOVERY_REPORT.md` §5) — zero drift since Stage A |

## 2. Dependency set (all frozen, hashed at V28 startup)

| Dependency | Path | SHA256 |
| :--- | :--- | :--- |
| P3 adapter base class | `aec/backbone/v25_p3_adapter.py` | `ce8169e95e86bd338b32dada48ba3fa0216bdeea4cebdd34a0264fe18a9f5195` |
| V3 adapter (loader semantics) | `aec/backbone/v3_adapter.py` | `a0a9fd2c2ce1abe2de7e871e7fd9deec647df9863179c19cf1b94fc5ed2e3135` |
| Interface | `aec/backbone/interface.py` | `1a1c5ec7cbc097c13d60eeed98ed98749f11cad7456c368366513dc7eeda4091` |
| Utils | `aec/backbone/utils.py` | `53f9277406162cf1789d5dceb944f147ead85d65d52647350533a1c1c7684404` |
| Config | `aec/config.py` | `14c3a22c0141b770efe43244afe77f7ed27064e0256bdb9f8b40750e3b2eabae` |
| V3 payload | `submission_Vj_kc_v3.tar.gz` | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` |
| Engine | `kaggle_environments` | `1.32.7` |

## 3. Configuration parameters (the entire A7 flag vector)

| Flag | A7 value | Meaning |
| :--- | :--- | :--- |
| `variant` | `"V27-ABL-A7"` | selects the flag vector below |
| `call_v3_at_step0` | `True` | V3's agent runs at step 0 (full step-0 processing) |
| `open_units` | `30` | wash quantity (used only if bypassing; A7 never bypasses) |
| `dispatch` | `False` | no PASS→WATER/DIG rewrite at any step |
| `rewrite_step0_wash` | `True` | resize exact-shape step-0 wash 50→30 |

No AEC, no market timing, no supervisor, no seed-specific behavior.

## 4. Imported modules (transitive, A7-relevant)

`copy`, `typing`, `hashlib`, `os`, `tarfile`,
`aec.backbone.interface` (BackbonePolicy, ContinuationPolicy),
`aec.backbone.utils` (`_get`, `_int`, `build_simulated_observation`,
`align_hands`, `compute_base_macro_fingerprint`),
`aec.backbone.v3_adapter` (`snapshot_v3_globals`, `restore_v3_globals`),
`aec.backbone.v25_p3_adapter` (`V25P3BackboneAdapter`,
`apply_p3_labor_dispatch`), `aec.config` (AECConfig),
`kaggle_environments` (engine).

V25 P3's *candidate file* (`candidates/v25_p3_unified.py`) is NOT in A7's
load path: `V25P3BackboneAdapter._load_v25_p3` only hashes that file for
`code_hash()` and loads V3 from the tarball. A7 inherits the loader, not
any P3 behavior. (Every V28 match additionally records `code_hash` so any
drift is detectable; the adapter asserts the class flags, not P3 bytes.)

## 5. Digest rule for every V28 match

Each match record stores:

- `cand_digest` = SHA256 of `aec/backbone/v27_ablation_adapters.py`
- `cand_variant` = `"V27-ABL-A7"` (+ the 4 flag values)
- `base_digest` = SHA256 of `submission_Vj_kc_v3.tar.gz`
- `engine_version` = `"1.32.7"`

The V28 runner asserts all four digests at startup and refuses to run on
mismatch. Any record whose digests differ from §1–§2 is not a V28 record.

## 6. Freeze discipline

A7 source, V3 source, harness, configuration, simulator, engine, and the
flag vector above are frozen from the first V28 confirmation match until
the final report. No parameter, threshold, timing, route, labor,
expansion, dispatch, or fallback change is permitted (§28 of the brief).
