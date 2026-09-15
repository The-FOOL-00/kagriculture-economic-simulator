# SEED PROVENANCE AUDIT: EXP-DEV-007_MECHANISM_EXPOSURE COHORT CERTIFICATION

**Experiment**: `EXP-DEV-007_MECHANISM_EXPOSURE`
**Date**: 2026-09-15
**Auditor**: Muse Code powered by Meta Muse Spark (Zero-Leakage Governance)
**Selected Cohort**: Seeds `310000` to `310499` (N=500 contiguous, per
`SEED_SELECTION_RULE.md`)
**Certification Status**: **100% CERTIFIED VIRGIN — ZERO PRIOR EXPOSURE**

No candidate seed was executed, constructed, or simulated during this audit.
All checks are static (file-content, history, and arithmetic inspection).

---

## 1. Protected ranges (never touched)

- `214200–214249` virgin final holdout (95,751 seeds below this cohort)
- `50050–50099`, `50000–50049`, `50100–50149`, `50000–50499` (consumed/
  benchmark/contaminated)
- `245000–245049`, `246000–246049`, `247000–247049`, `248000–248049`
  (consumed DEV-003/004/005/006 cohorts)
- Full disjointness table: `SEED_SELECTION_RULE.md` §3.

## 2. Audit results by dimension

| Dimension | Method | Hits | Verdict |
|---|---|---|---|
| Full-tree literals | `grep -rIln -E '\b310[0-4][0-9]{2}\b'`, excl. .git | 5 files, all classified below | Clean |
| Tracked files | `git grep -l` same pattern | 1 file (timestamp artifact) | Clean |
| Git history | pickaxe `-S 310000/-S 310499`, regex `-G`, message grep | 1 commit (CSV-add artifact) | Clean |
| Stride / range | all `range()` 6-digit bounds; seed-arithmetic bases | 0 covering the block | Clean |
| Result DBs (JSON) | `"seed": 310xxx` full-tree | 0 | Clean |
| Result tables (CSV) | `^310xxx,` seed rows | 0 | Clean |
| Execution logs | `Seed 310xxx` / `Game(310xxx` | 0 | Clean |
| Session stores | execution-pattern grep over Muse sessions | 0 execution contexts | Clean |
| Manifests/registries | covered by full-tree scan | 0 | Clean |
| Caches (`__pycache__`) | transitive: no `.py` source references the block | 0 possible | Clean |
| Temp/sandbox | `/tmp` sandbox listing | empty | Clean |

## 3. Classification of every match

**Full-tree literal scan (5 files):**

1. `experiments/EXP-DEV-007_MECHANISM_EXPOSURE/PROTOCOL.md` — this freeze's
   own protocol (post-selection documentation, written during this audit).
2. `experiments/EXP-DEV-007_MECHANISM_EXPOSURE/SEED_SELECTION_RULE.md` — this
   freeze's own rule (post-selection documentation).
3. `replays/raw/georgymamarin/teams.csv` — 21 matches, ALL verified as
   leaderboard-timestamp microsecond fractions (`.310000` in
   `YYYY-MM-DD HH:MM:SS.ffffff` fields; zero non-timestamp lines).
4. `scratch/analyzed_episodes_55944418.csv:54` — single timestamp fraction
   (`2026-09-02 09:36:41.310000`) in a live-episode telemetry column.
5. `scratch/kernels_list.json:539` — single timestamp fraction
   (`"last_run": "2026-08-09 13:14:47.310000"`).

Items 3–5 are numeric artifacts, not seeds, executions, results, ranges, or
design references. No game was simulated and no outcome observed on any
310000–310499 seed.

**Git history:** commit `07b8f16` (2026-09-02) is the sole pickaxe/regex hit;
verified to be the commit that ADDED the `analyzed_episodes` CSV containing
the timestamp artifact. No seed, range, or design reference.

**Stride / range:** `range()` bounds in 200000–400000 are only known
cohort/guard constants (214200/214250, 245000–250050); scratch seed grids sit
at 920001–970020; seed-arithmetic bases in 300000–319999 are only the static
auditor listing (`find_virgin_candidates.py`, imports os/re/sys/subprocess
only, never executes games) and single-seed literals {42, 314159, 777777,
123456789, 999999999} in `run_closed_loop_mutation_audit.py` — nearest is
314159, 3,660 seeds above this block. No interval or progression reaches
310000–310499.

**Session stores:** zero `Game(310…` / `Seed 310… |` / `seed=310…` execution
contexts. Any-mentions: this session's own audit text plus one prior-session
telemetry artifact (`byte_count:310387`, a buffer size, not a seed).

## 4. Certification verdict

Cohort **310000–310499** (N=500) is formally certified as **100% VIRGIN**:
zero prior simulations, logs, result rows, seed constructions, range/stride
coverage, or design references anywhere in the workspace, its history, or
accessible session artifacts. Authorized as the experimental cohort for
**EXP-DEV-007_MECHANISM_EXPOSURE** upon protocol freeze. Fallback blocks
(410000+, per the rule) were not audited and remain untouched.
