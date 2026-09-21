# V27 — BASELINE FREEZE & INTEGRITY LEDGER

## 1. Purpose

V27 is a backbone-robustness and causal-attribution study of V25 P3 vs V3.
No new championship agent is built in V27. This document freezes every
baseline V27 depends on and records the integrity evidence.

## 2. Frozen competition artifact (immutable)

| Artifact | Value | Status |
| :--- | :--- | :--- |
| Release tag | `v22r1` (annotated tag object `6bc559b91aea9191d97f3482fb6df560b12d691e`) | FROZEN |
| Release commit (`v22r1^{commit}`) | `33763a8f58b17bc3a32735c2a322883b78ed3778` | FROZEN |
| Worktree `HEAD` at V27 start | `33763a8f58b17bc3a32735c2a322883b78ed3778` | MATCHES |
| Submitted archive | `submission_aec_v22r1.tar.gz` | FROZEN |
| Submitted archive SHA256 | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` | VERIFIED |

Note: `git rev-parse v22r1` returns the annotated-tag object hash
(`6bc559b…`), while `git rev-parse 'v22r1^{commit}'` returns `33763a8…`.
That split is normal annotated-tag behavior, not a compromise. Verified
2026-09-21.

## 3. Research branches

| Branch | Commit | Role |
| :--- | :--- | :--- |
| `research/v25-coherent-planner` | `e4eb8a421562ba9e0a2627375d385fdfe011e32f` | V25 evidence source (read-only for V27) |
| `research/v26-backbone-aware-aec` | `33763a8…` + uncommitted worktree V26 infra | V26 infrastructure base (read-only semantics) |
| `research/v27-v25-robustness` (this work) | `33763a8…` + V27 work | Active V27 branch |

Worktree note: the V26 backbone-aware AEC infrastructure exists in this
checkout as uncommitted work on top of `33763a8` (adapters, tournament
script, checkpoint, docs). V27 reuses it in place. A sibling directory
`../Kagriculture-v27` was NOT created: the execution sandbox restricts
writes to the workspace root, and a fresh worktree would have lost the
uncommitted V26 infrastructure. The branch label above is the V27
isolation boundary; V22R1 files are untouched (see §6).

## 4. Frozen research baselines

| Baseline | Anchor | SHA256 | Cross-checks |
| :--- | :--- | :--- | :--- |
| V3 standalone tarball | `submission_Vj_kc_v3.tar.gz` | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` | recorded in V26 qual manifest; V3 adapter `code_hash` |
| V25 P3 unified planner | `candidates/v25_p3_unified.py` | `13292582c8cc796bc11ccebff9684fbec45cfb97d936fb9e85e4e9bb4dbea179` | byte-identical to `e4eb8a4` blob (`cmp` clean per V26 audit, re-verified by hash here); V25 confirmation `code_hash`; V26 checkpoint `backbone_hash` |

V25 P3 is FROZEN for the first half of V27. Any later ablation is a
labeled research variant, never "V25 P3".

### 4.1 P3 mechanism (exact, from source)

1. **Step 0**: bypass V3 entirely; emit
   `{farmer: PASS, hands: [], market: [BUY WHEAT 30, SELL WHEAT 30]}`.
   V3 at step 0 emits `[BUY WHEAT 50, SELL WHEAT 50]` (parent tape
   `[BUY 5, BUY 10, SELL 60]` rewritten by `OPEN_UNITS = 50` in V3
   `main.py`, plus frontload wrappers P3 skips).
2. **Steps ≥ 1**: call frozen V3, then rewrite `PASS → WATER` for units
   standing on unwatered `PLANT` tiles and `PASS → DIG` for units on
   `WEED` tiles (in-place, zero-inventory only; positions preserved).

## 5. Vendored historical evidence (verbatim, read-only)

Copied verbatim from `research/v25-coherent-planner` via `git show`
(2026-09-21). These files MUST NOT be edited; V27 derived tables live in
separate `v27_*` files.

| File | SHA256 | Lines | Content |
| :--- | :--- | :--- | :--- |
| `results/v25_backbone_matches.jsonl` | `aebf1372552c8d16f255b5c548769357f61c41945d21823d47ea5c506e2d1484` | 120 | V25 discovery: P1/P2/P3 × 20 seeds × 2 seats |
| `results/v25_confirmation_matches.jsonl` | `112194cd3d63bd1cf08f6c02c2d66140e22b34f760660fa90752c23f161738bd` | 40 | V25 confirmation: P3 × 20 seeds × 2 seats |
| `results/v25_aec_transfer_matches.jsonl` | `40e96e15cf6d91d7c092fb8f358ce4b4658a70685afd1a2b4971c52590aa834a` | 80 | V25 4-arm AEC transfer audit |
| `results/v26_aec_transfer_matches.jsonl` | `7aef81965152dea4a5f88eddb7cf53ec83b4954bd802eb1a7177f94f5eb90c2e` | 160 | V26 transfer: 4 arms × 20 seeds × 2 seats |

Cohort map: A = `249430..249449` (V25 discovery P3 arm, 40 records),
B = `249450..249469` (V25 confirmation, 40 records),
C = `249470..249489` (V26 ARM1_V25_STANDALONE, 40 records).

## 6. V26 integrity re-verification (this session)

- Checkpoint: 160/160 lines, 40 per arm; per-arm means/medians/min/max
  reproduce `V26_QUAL_MANIFEST.json` exactly (ARM1 −218.75 / −287.0,
  ARM2 identical, ARM3 −189.65, ARM4 +19.80).
- V26 tests green: `test_v26_backbone_adapters`,
  `test_v26_continuation_fidelity`, `test_v26_null_parity`,
  `test_v26_parallel_parity`, `test_v26_quarantine_scan_parity`, plus
  `test_mechanism_isolation` — **19 passed**.
- V26 verdict preserved unchanged: **TRANSFER FAILED — MECHANISM**.
  No threshold, endpoint, or interpretation change is made in V27.

## 7. Cohort registry (V27 additions are reservations, not uses)

- Consumed through V26: max seed `249489` (audited across `results/`,
  `experiments/`, `scratch/`, root docs; no reference to any seed
  ≥ `249490` anywhere).
- Protected untouched holdouts: `214200..214249`, `340050..340199`.
- Retired/consumed: `340300..340349` (EXP-AEC-004), all `249xxx ≤ 249489`
  development cohorts.
- V27 reservations (formalized in `V27_COHORT_MANIFEST.json` at Phase 9):
  discovery `249490..249509`, confirmation `249510..249529`. Neither is
  touched before its preregistered phase.

## 8. Stop-condition status at freeze time

1. V22R1 integrity compromised? NO (all hashes match).
2. V3 reproducible? YES (tarball hash + adapter tests green).
3. P3 digest drift? NO (four-anchor match).
4. Cohort overlap? NONE (virgin block starts at 249490).
5. Counterfactual exactness? Inherited V26 green (8/8); V27 re-audits.
6.–8. No ablations, nondeterminism, or irreproducibility yet. Open.

## 9. What V27 will NOT do

- Modify V22R1, resubmit, or touch competition fallback behavior.
- Retune or reinterpret V26 (transfer stays FAILED — MECHANISM).
- Tune V25 P3 before the generalization test; ablations are labeled
  variants and come only after frozen historical analysis.
- Build a V27 AEC, transfer market timing again, or add supervisors.
