# V32 BASELINE FREEZE — population-trained generalist program

Date: 2026-09-22. Status: POST-DEADLINE RESEARCH PROGRAM (not a submission experiment).

## 1. Competition state (immutable during V32)

- Slot A: `V22R1` (`submission_aec_v22r1.tar.gz`, SHA
  `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5`, git `33763a8` / tag `v22r1`).
- Slot B: `A7 / V30` (`submission_a7_v30.tar.gz`, SHA
  `4a07673072b6aef9346bf4c21ee5a5979b9da50fccc609fb731dcdbf8f016619`).
- V31R2 decision: OPTION 1 — KEEP A7. No A8. No replacement of either slot.
- V32 introduces NO experimental learned agent into the competition and
  replaces NEITHER active submission.

Verified untouched at V32 start (2026-09-22): V22R1 tarball SHA matches
`V22R1_RELEASE_MANIFEST.json`; V3 tarball SHA `845e0d10…` matches; all six
A7 dependency SHAs in `V28_A7_FREEZE.md` §2 match byte-for-byte.

## 2. Frozen backbone references

| Artifact | SHA256 |
| :--- | :--- |
| `submission_Vj_kc_v3.tar.gz` (V3) | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` |
| `submission_aec_v22r1.tar.gz` (V22R1) | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` |
| `submission_a7_v30.tar.gz` (A7 pkg) | `4a07673072b6aef9346bf4c21ee5a5979b9da50fccc609fb731dcdbf8f016619` |
| `aec/backbone/v27_ablation_adapters.py` | `18d2c8ea2cf826b0bef71c96988dba0c93d7dbcc73936a0c99f07cb0539e7ae9` |
| `aec/backbone/v25_p3_adapter.py` | `ce8169e95e86bd338b32dada48ba3fa0216bdeea4cebdd34a0264fe18a9f5195` |
| `aec/backbone/v3_adapter.py` | `a0a9fd2c2ce1abe2de7e871e7fd9deec647df9863179c19cf1b94fc5ed2e3135` |
| `aec/backbone/interface.py` | `1a1c5ec7cbc097c13d60eeed98ed98749f11cad7456c368366513dc7eeda4091` |
| `aec/backbone/utils.py` | `53f9277406162cf1789d5dceb944f147ead85d65d52647350533a1c1c7684404` |
| `aec/config.py` | `14c3a22c0141b770efe43244afe77f7ed27064e0256bdb9f8b40750e3b2eabae` |
| `aec/backbone/v31r2_wash_adapter.py` | `08e9832a1351bbf4cdd9e8483a247af719a01f70471434bd6e581acae15c9402` |
| `candidates/v30_a7_standalone/main.py` | `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` |
| `candidates/v25_p3_unified.py` | `13292582c8cc796bc11ccebff9684fbec45cfb97d936fb9e85e4e9bb4dbea179` |
| `extracted_agents/dmitrii_lb2800/main.py` | `495bfa4825c9e58638e804aeeb62a9537826f6d4d869222815e1bbeefd84d3dc` |
| engine `kaggle_environments` | `1.32.7` |

## 3. Seed governance

Consumed 249xxx dev line (executed matches in `results/*.jsonl`): 249530–249577,
249580–249589, 249591–249634. Gaps 249578/249579/249590 never executed; retired
unused (fragmented, left alone to avoid confusion).

V32 cohorts (all virgin at freeze; full-tree scan in `V32_QUAL_MANIFEST.json`):

| Cohort | Seeds | Purpose |
| :--- | :--- | :--- |
| V32-TRAIN | 249635–249674 (40) | imitation data, feasibility RL, router labels |
| V32-DEV | 249675–249694 (20) | architecture iteration, ablations |
| V32-CONFIRM | 249695–249734 (40) | frozen; promotion tests only, single touch |
| V32-EXP1 | 249635–249640 (6, subset of TRAIN) | EXP-1 benchmark block |

Refused (V32 runners hard-abort on these):

- `214200–214249` (GATE0 virgin holdout, protected)
- `340050–340050+39` (V29-consumed, retired; written arithmetically per the V30 convention so slice-quarantine scans treat it as a boundary declaration, not a seed literal)
- `340090–340199` (V29 remainder, protected)
- `340000–340049`, `340200–340299` (EXP-AEC-001/002/003, consumed)
- `340300–340349` (EXP-AEC-004, retired)
- all 249xxx ≤ 249634 (prior dev cohorts, no silent reuse as virgin)

V32-CONFIRM (249695–249734) must not appear in any executed match, trajectory
dump, or training batch before a pre-registered promotion test. `test_v32_freeze.py`
enforces this plus the protected-holdout quarantine.

## 3b. Addendum A1 — commissioning seeds (2026-09-22)

Seeds 249673–249674 (inside V32-TRAIN) are COMMISSIONING-CONSUMED: used by
harness probes (telemetry/encoder schema) and `tests/test_v32_harness.py`
(determinism/parity/packaging legs). Effective TRAIN for learning: 249635–249672 (EXP-1 used 249635–249640;
capture used 249641–249642; 249643–249672 free). DEV 249675–249694 untouched. 249673–249674 must never enter a training batch,
imitation dataset, or DEV/CONFIRM decision.

## 4. Interpreters

- Match execution / trajectory capture: `.venv/bin/python`
  (`kaggle-environments 1.32.7`, `numpy`, `scipy`; no torch).
- Neural probes / analysis: system `python3` (`torch 2.13.0+cpu`).
- Hardware: CPU-only (no GPU), 12 cores, ~7 GB RAM. All V32 training claims
  are conditioned on this (§34 of the brief: architecture follows compute).

## 5. Scope of this milestone

EXP-1 (benchmark), EXP-2 (imitation feasibility), EXP-3 (RL feasibility at
10M–50M-step scale analysis). No large-scale training until feasibility
evidence justifies it. EXP-4–EXP-9 are pre-registered protocol stubs only.

## 6. Stop-condition pre-commitment

If EXP-2/EXP-3 show (a) no imitation signal above trivial baselines, (b) PPO
throughput incompatible with CPU-only iteration, or (c) router parity at far
lower cost, V32 pivots to the lower-complexity route per §52 of the brief.
No compute is spent defending the neural hypothesis.
