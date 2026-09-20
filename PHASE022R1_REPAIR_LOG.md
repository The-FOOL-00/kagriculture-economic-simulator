# PHASE022R1 — REPAIR LOG

**Date**: 2026-09-20
**Mission**: V22R1 release repair, evidence correction & competition-loader
reverification. No new mechanisms, no new alpha, no score optimization.
Economic architecture frozen: V3 (`845e0d10...`) +
DEPENDENCY_AWARE_MARKET_TIMING + TERMINAL_LIQUIDATION + PHASE_SHUTDOWN.

## 1. Finding classification (independent audit, 8 files read first)

| # | Finding | Classification | Evidence |
| --- | --- | --- | --- |
| E1 | Entrypoint `__file__` NameError under KE; $3,000 corpse | **confirmed** | bare-`exec` repro + KE 1.32.7 end-to-end ($3,000.00/$3,421, DONE/720); see `PHASE022R1_LOADER_FAILURE_REPRO.md` |
| E2 | Shipped QA assertions vacuous (DONE + reward>0, $3k==$3k, hidden stderr, wrong opponent) | **confirmed** | `scripts/build_phase022_submission.py:188-198`, `debug=False`; repro matches |
| E3 | Release uncommitted (HEAD Phase 021) | **confirmed** | `git` state; corrected by release commit/tag in §22 flow |
| S1 | No Phase 022 preregistration; primary-test (one-sided t, p≈0.43) fails; headlined Wilcoxon secondary/unadjusted; seed-level Wilcoxon p≈0.051; d≈0.03 | **confirmed** | independent scipy recomputation from `results/phase022_consolidation.json`; see `PHASE022R1_FINAL_REPORT.md` §stats |
| S2 | Counterfactual fidelity MAE=$0.00 circular (`realized=predicted`, zero re-simulation) | **confirmed** | `aec/evaluation/win_model.py:373-374`, `scripts/run_phase022_consolidation.py:418-434`; claim withdrawn, see `PHASE022R1_COUNTERFACTUAL_FIDELITY.md` |
| S3 | Causal generality overclaimed ("100%/necessary-and-sufficient") | **confirmed** | cohort-scoped rewording applied; ablation enforcement itself verified valid |
| S5 | P20 "timing ELIMINATED" vs V22 "timing drives" unreconciled | **confirmed** | reconciliation note added (different cohorts; diagnostic probes vs live commits) |
| H1 | Tournament cohort 340300..340349 consumed by EXP-AEC-004, falsely "untouched" | **confirmed** | `results/EXP_AEC_004_*`, experiment records; re-designated CONSUMED/RETIRED, see `PHASE022R1_HOLDOUT_INTEGRITY.md` |
| P1 | "Sub-100ms" false as blanket (P95 229 / P99 405 / max 2347 ms; `within_limit=false`) | **confirmed** | `results/phase022_consolidation.json` latency aggregates recomputed; reworded to median/tail split |
| P2 | 9-stage pipeline table unsourced (telemetry has 6 fields) | **confirmed** | table removed |
| P3 | 719 decision steps/match, not 720; "28,800 steps" wrong (28,760) | **confirmed** | corrected to 719/match, 28,760 total |
| D1 | "720/720 steps bit-identical" unsupported (aggregates only) | **confirmed** | replaced by genuine per-turn replay audit, see `PHASE022R1_DETERMINISM_AUDIT.md` |
| F1 | `safety_violations` counter structurally zero; `purchase_ok`/`market_collision_ok` unevaluated | **confirmed** | inspected `aec/safety/*` + executor gate; see `PHASE022R1_SAFETY_AUDIT.md` |
| F2 | Macro stress test misreported / near-tautological; LIQ/SHUT live paths unexercised | **confirmed** | test source inspected; wording corrected, coverage disclosed |
| A1 | Ablation 3-layer enforcement valid; identical arms explained | **confirmed** | code-traced L1/L2/L3; retained with cohort-scoped phrasing; truth table in `PHASE022R1_FINAL_REPORT.md` §4 |
| V1 | V3 immutability airtight; packaged `aec/` == working tree | **confirmed** | SHA re-verified at rebuild; preserved in V22R1 |
| V2 | Fresh cohort materially pristine; holdouts 340050..199, 214200..249 clean | **confirmed** | repo-wide 6-digit seed search; no executions found |
| G1 | Registry/prose mismatch (tranche/asset EXPERIMENTAL not QUARANTINED) | **confirmed** | wording aligned to "disabled by default + 3-layer blocked" |
| U1 | Live LIQ/SHUT behavior; per-arm ledgers; per-step latency attribution | **not reproducible from artifacts** | disclosed as residual uncertainty; no claim made |

No finding was implemented blindly: each item above was re-verified against
source/artifacts in this session before correction.

## 2. Repairs applied (chronological)

### R1 — Competition-loader entrypoint repair (loader compat, §4)
- Root cause: packaged `main.py:9` unconditional `__file__` at module top.
- Fix: new loader-safe `main.py` template in `scripts/build_phase022r1_submission.py`:
  no module-level `__file__`; validated, non-shadowing sys.path fallback
  (append-only, marker-checked); V3 tarball resolution ordered
  `__file__`-dir → imported-`aec`-module-relative → KE
  `configuration["__raw_path__"]`-dir → config default (BackboneAdapter
  self-relative), each candidate validated by file existence.
- `BackboneAdapter`, V3 payload, AEC semantics untouched.
- Packager also fixed: LF line endings, hardened QA (V3-scale reward bar,
  V3 head-to-head, debug-surfaced exceptions, latency sanity, both rewards
  recorded).

### R2 — Statistical wording correction (§9-§11)
- Preregistration language removed (no artifact exists).
- Four-test table disclosed (match t / match Wilcoxon / seed t / seed Wilcoxon).
- Conservative result wording adopted; superlatives deleted.

### R3 — Counterfactual fidelity claim withdrawn (§13)
- MAE=$0.00 empirical claim withdrawn as circular; architecture description
  retained; independent post-hoc audit declared not-established (recorded
  traces lack pre-intervention full state for genuine replay).

### R4 — Determinism re-audited at per-turn level (§14)
- Genuine per-turn replay audit executed under KE on Linux; every action,
  commit/abstain, and terminal reward compared; "720/720" replaced by the
  verified scope actually checked.

### R5 — Safety audit repaired (§15)
- `purchase_ok` / `market_collision_ok` predicates inspected; genuine
  evaluation status documented; adversarial predicate tests added
  (`tests/aec/test_phase022r1_safety_predicates.py`); counter semantics
  corrected to measure observable rejections; commit-gate behavior unchanged.

### R6 — Performance wording corrected (§16)
- Median/tail split reported from recomputed aggregates; "sub-100ms" blanket
  claim removed; unsourced 9-stage table removed; step counts fixed (719).

### R7 — Holdout registry corrected (§17)
- 340300..340349 marked CONSUMED/RETIRED (EXP-AEC-004); untouched holdouts
  retained only where evidence supports; no experiments run on any holdout.

### R8 — Submission rebuilt as `submission_aec_v22r1.tar.gz` (§18-§19)
- Old archive retired (kept on disk, never overwritten); new archive built
  from repaired packager; SHA recorded in `PHASE022R1_SUBMISSION_SHA256.txt`;
  content audit + three-loader matrix executed.

## 3. Semantic-preservation record
- `diff` of clean extractions (V22 vs V22R1): `aec/`, `config.py`,
  `extracted_agents/`, V3 payload ALL byte-identical; `main.py` is the ONLY
  change (loader-safe entrypoint). The §15 counter repair touched
  `scripts/run_phase022_consolidation.py` ONLY (dev script, not packaged).
  Economics, thresholds, mechanisms, V3 payload byte-identical.
- Old-vs-repaired equivalence on 249376..249395: 40/40 EXACT, 0/288,000
  field diffs — see `PHASE022R1_SEMANTIC_EQUIVALENCE.md`.
