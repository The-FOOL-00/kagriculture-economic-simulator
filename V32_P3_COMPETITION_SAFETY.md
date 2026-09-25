# V32 P3 COMPETITION SAFETY (entry + exit record)

Date (entry): 2026-09-23. Phase: V32 P3 action-head repair (research-only branch).

## 1. Entry verification (2026-09-23, before any P3 work)

| Artifact | Expected SHA256 | Observed | Verdict |
| :--- | :--- | :--- | :--- |
| `submission_aec_v22r1.tar.gz` (Slot A) | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` | identical | UNCHANGED |
| `submission_a7_v30.tar.gz` (Slot B) | `4a07673072b6aef9346bf4c21ee5a5979b9da50fccc609fb731dcdbf8f016619` | identical | UNCHANGED |
| `submission_Vj_kc_v3.tar.gz` (V3) | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` | identical | UNCHANGED |
| `aec/backbone/v27_ablation_adapters.py` | `18d2c8ea2cf826b0bef71c96988dba0c93d7dbcc73936a0c99f07cb0539e7ae9` | identical | UNCHANGED |
| `aec/backbone/v25_p3_adapter.py` | `ce8169e95e86bd338b32dada48ba3fa0216bdeea4cebdd34a0264fe18a9f5195` | identical | UNCHANGED |
| `aec/backbone/v3_adapter.py` | `a0a9fd2c2ce1abe2de7e871e7fd9deec647df9863179c19cf1b94fc5ed2e3135` | identical | UNCHANGED |
| `aec/backbone/interface.py` | `1a1c5ec7cbc097c13d60eeed98ed98749f11cad7456c368366513dc7eeda4091` | identical | UNCHANGED |
| `aec/backbone/utils.py` | `53f9277406162cf1789d5dceb944f147ead85d65d52647350533a1c1c7684404` | identical | UNCHANGED |
| `aec/config.py` | `14c3a22c0141b770efe43244afe77f7ed27064e0256bdb9f8b40750e3b2eabae` | identical | UNCHANGED |
| `aec/backbone/v31r2_wash_adapter.py` | `08e9832a1351bbf4cdd9e8483a247af719a01f70471434bd6e581acae15c9402` | identical | UNCHANGED |
| `candidates/v30_a7_standalone/main.py` | `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` | identical | UNCHANGED |

P2 exit digests re-verified: frozen a1 config hash `c89777784ead0d84e6d2395f333be6cc1cb9091619159c439313dc0a9a9fe0f8`
recomputed identical via `scripts/v32_p2_freeze_arch.py`; P2 vocab
(`results/v32_p2_vocab.json`, 101+1466) and BC legs
(`results/v32_p2_bc_legs.jsonl`, 120 legs / 172,560 steps) present and unmodified.

Protected holdouts: GATE0 `214200-214249`, V29 remainder `340090-340199`,
V32-CONFIRM `249695-249734` — zero executions (quarantine enforced by
`scripts/v32_common.py::check_seed_allowed`, asserted by
`tests/test_v32_freeze.py`).

Executed-seed audit at entry (scanned result files, not telemetry):
P2-TRAIN `249635-249649` (BC legs), P2-SCREEN `249650-249672` (BC replay),
commissioning `249673-249674`. V32-DEV `249675-249694` virgin at P3 entry.
The P2 prereg draft's mention of `249675-249683` as screen was never executed.

Pre-existing tree state (not P3-caused, left alone): `tests/test_v28_freeze.py`
tracked modification (documented V32 allowlist maintenance), modified
`external_repos/*` submodules, untracked V28-V32 research files (HEAD is at
`d818fb1`, pre-V28; competition state is established by tarball SHAs above).

## 2. P3 seed governance

P3 executes ONLY on already-consumed P2 seeds (`249635-249672`) for
development/closed-loop probes, plus a newly designated P3 screen slice of
virgin V32-DEV seeds declared in `V32_P3_PREREG.md` before first use.
V32-CONFIRM and all protected holdouts remain refused. No Kaggle submission
commands are run in P3.

## 3. Exit verification (2026-09-23, P3 PARTIAL close)

Slot A `6b879b3e…`, Slot B `4a076730…`, V3 `845e0d10…` re-verified
byte-identical; spot adapters (`interface.py`, A7 standalone) identical.
Executed-seed audit over all P3 result files: ONLY `249675–249684`
(prereged P3-SCREEN) + previously consumed P2 seeds (training rows, T5 seed
249635). P3-CONFIRM `249685–249694`, V32-CONFIRM `249695–249734`, GATE0, and
all 340xxx ranges: zero executions. Full P3 test files: 14 new tests
(codec 8 + models 6) green; P2/freeze suites re-verified green at entry
(21 passed).

## 4. Submission statement

No competition submission was modified or launched during P3.
