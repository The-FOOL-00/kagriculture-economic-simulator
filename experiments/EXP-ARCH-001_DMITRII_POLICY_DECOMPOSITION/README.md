# EXP-ARCH-001 — Dmitrii Policy Decomposition

Separate research track. Analysis only. No candidate, no runner, no Kaggle
submission, no performance experiment.

## Boundary compliance

- Did NOT modify: `candidates/compiled_v54_plus_residual.py`,
  `candidates/compiled_v54_plus_shop.py`, `EXP-DEV-005`, `EXP-DEV-006`,
  `EXP-DEV-007` protocol, final holdout 214200–214249.
- All work products live in this directory only:
  `experiments/EXP-ARCH-001_DMITRII_POLICY_DECOMPOSITION/`.
- No Kaggle submission code was executed. No matches were simulated for
  performance comparison. The decoder scripts in this directory perform
  static analysis of the extracted tapes only.

## Phase 1 — Immutability record (verified 2026-09-15)

| Artifact | SHA-256 (recomputed) | Status |
|---|---|---|
| `candidates/compiled_v54_plus_residual.py` | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` | clean, matches DEV-004/005/006/007 frozen records |
| `candidates/compiled_v54_plus_shop.py` | `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8` | clean, matches DEV-006/007 frozen records |
| DEV-005 protocol V1.4 | `ac69fc602083f232792ad5bdabd699e4b9f96e73462f9edc740ccd63c727e9f6` | matches `PROTOCOL_HASH.txt` |
| DEV-006 protocol V1.5 | `e52a0570a8bc9cfeafe1165f49f4c9d77ef9a3b7aa030783f8aef7e9ee7b04e8` | matches `PROTOCOL_HASH.txt` |
| DEV-007 `PROTOCOL.md` + 4 companions | `d10ee185…`, `10ea5be8…`, `3bf2492c…`, `4e3536a5…`, `899d4797…` | all match `PROTOCOL_HASH.txt` |

Git: branch `main` at `4f55010`. Pre-existing working-tree diffs in
EXP-DEV-005/006 result CSVs are line-ending-only
(`git diff --ignore-cr-at-eol` is empty); protocol `.md` files are clean.
None of these were touched by this track.

## Headline result

Dmitrii is **one shared agronomic plan with 11 shop-conditional route
permutations, two micro-repair overlays, and a 7-turn shadow optimizer**.
The 13 "strategies" are NOT 13 economies: planting schedules are identical
day-by-day across all tapes, herd size is 16–17 head in all tapes, and even
the most action-distant tape pairs (504/504 steps differ) agree to ~90% on
daily operation mix. The genuine economic differences are small: sheep/cow/
goose composition, wool-clearing aggressiveness, and seed-purchase batching.

## Deliverables

| File | Content |
|---|---|
| `README.md` | this file |
| `SOURCE_MAP.md` | Phase 2: complete control-flow / state / limits map |
| `STRATEGY_TAPE_DECODER.md` | Phase 3: decoder method + per-strategy economic narratives |
| `STRATEGY_SUMMARY.csv` | Phase 3/4: machine-readable 13-row summary |
| `STRATEGY_COMPARISON.md` | Phase 4: comparison matrix, economic vs positional |
| `SHOP_ROUTER_ANALYSIS.md` | Phase 5: shop-pair mapping, reachability, checkpoints |
| `REACTIVE_OVERLAY_ANALYSIS.md` | Phase 6: repair_weeds / advance_sales / recovery |
| `TERMINAL_PLANNER_ANALYSIS.md` | Phase 7: 7-turn optimizer reconstruction |
| `TRANSFERABILITY_MATRIX.md` | Phase 9: idea-by-idea comparison vs our systems |
| `HYPOTHESES.md` | Phases 10–11: classified, testable hypotheses |
| `FINAL_ARCHITECTURE_REPORT.md` | Phases 8 + synthesis; ends with STOP |

## Intermediate evidence (this directory)

- `decode_tapes.py`, `decode_tapes2.py` — static tape decoders.
- `analysis/01_tape_similarity.md` … `analysis/12_workforce.md` — decoder
  output. All quantitative claims in the reports trace to these files.

## Engine grounding

Unit semantics: `extracted_agents/dmitrii_lb2800/unit_model.py` (engine
1.32.7). Market/day-boundary/shop semantics: `env_backup_1_30_1/
kaggriculture.py` (1.30.1, flagged where it differs) cross-checked against
`external_repos/kaggriculture-cppsim/sim/sim.hpp` (1.32.7 mirror: COW $400,
shops drawn WITH replacement, town-center interval 24).
