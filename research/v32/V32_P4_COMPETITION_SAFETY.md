# V32 P4 COMPETITION SAFETY (entry record)

Date (entry): 2026-09-23. Phase: V32 P4 critical market ordering & joint-BC stabilization (research-only branch).

## 1. Entry verification (2026-09-23, before any P4 modifications)

All production competition assets and adapters were verified bit-identical against the frozen digests:

| Artifact | Expected SHA256 | Observed SHA256 | Verdict |
| :--- | :--- | :--- | :--- |
| `submission_aec_v22r1.tar.gz` (Slot A) | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` | UNCHANGED |
| `submission_a7_v30.tar.gz` (Slot B) | `4a07673072b6aef9346bf4c21ee5a5979b9da50fccc609fb731dcdbf8f016619` | `4a07673072b6aef9346bf4c21ee5a5979b9da50fccc609fb731dcdbf8f016619` | UNCHANGED |
| `submission_Vj_kc_v3.tar.gz` (V3) | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` | UNCHANGED |
| `aec/backbone/v27_ablation_adapters.py` | `18d2c8ea2cf826b0bef71c96988dba0c93d7dbcc73936a0c99f07cb0539e7ae9` | `18d2c8ea2cf826b0bef71c96988dba0c93d7dbcc73936a0c99f07cb0539e7ae9` | UNCHANGED |
| `aec/backbone/v25_p3_adapter.py` | `ce8169e95e86bd338b32dada48ba3fa0216bdeea4cebdd34a0264fe18a9f5195` | `ce8169e95e86bd338b32dada48ba3fa0216bdeea4cebdd34a0264fe18a9f5195` | UNCHANGED |
| `aec/backbone/v3_adapter.py` | `a0a9fd2c2ce1abe2de7e871e7fd9deec647df9863179c19cf1b94fc5ed2e3135` | `a0a9fd2c2ce1abe2de7e871e7fd9deec647df9863179c19cf1b94fc5ed2e3135` | UNCHANGED |
| `aec/backbone/interface.py` | `1a1c5ec7cbc097c13d60eeed98ed98749f11cad7456c368366513dc7eeda4091` | `1a1c5ec7cbc097c13d60eeed98ed98749f11cad7456c368366513dc7eeda4091` | UNCHANGED |
| `aec/backbone/utils.py` | `53f9277406162cf1789d5dceb944f147ead85d65d52647350533a1c1c7684404` | `53f9277406162cf1789d5dceb944f147ead85d65d52647350533a1c1c7684404` | UNCHANGED |
| `aec/config.py` | `14c3a22c0141b770efe43244afe77f7ed27064e0256bdb9f8b40750e3b2eabae` | `14c3a22c0141b770efe43244afe77f7ed27064e0256bdb9f8b40750e3b2eabae` | UNCHANGED |
| `aec/backbone/v31r2_wash_adapter.py` | `08e9832a1351bbf4cdd9e8483a247af719a01f70471434bd6e581acae15c9402` | `08e9832a1351bbf4cdd9e8483a247af719a01f70471434bd6e581acae15c9402` | UNCHANGED |
| `candidates/v30_a7_standalone/main.py` | `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` | `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` | UNCHANGED |

P3 exit digests re-verified:
- `results/v32_p2_bc_legs.jsonl`: 120 legs / 172,560 steps (SHA16 `55c907db955b1210`)
- `results/v32_p2_vocab.json`: 101 unit + 1466 market (SHA16 `f0df959940dfd216`)
- `results/v32_p2_norm.json`: 157-dim normalizer (`d2a41ab7…`)
- Action schema: `V32_P3_ACTION_SCHEMA.json` (18 U_OP, 12 U_ARG, 17 U_QTY, 7 M_OP, 12 M_ITEM, 77 M_QTY)
- Suite status: 20 passed (tests/test_v32_freeze.py, tests/test_v32_p3_codec.py, tests/test_v32_p3_models.py).

## 2. Seed Quarantine Enforcement

The following seed blocks remain strictly prohibited from execution:
- GATE0 virgin holdout: `214200–214249`
- V29 remainder: `340090–340199`
- V32-CONFIRM: `249695–249734`

P4 evaluation is authorized ONLY on:
- P3-SCREEN seeds: `249675–249684` (for strict paired counterfactuals against P3 baseline)
- P2-TRAIN seeds: `249635–249646` (training)
- P2-VAL seeds: `249647–249649` (validation)

All match executions pass through `scripts/v32_common.py::check_seed_allowed`.

## 3. Submission Statement

No competition submission will be modified, packaged, or launched during P4. P4 is pure offline scientific research.
