# EXP-DEV-006_HORIZON_KILLTEST — Retrospective Horizon-Gate Mechanism Test

**Status: COMPLETE — verdict: SUPPORTED (see VERDICT.md)**
**Mandate: MECHANISM TEST ONLY. Do NOT qualify DEV-005. No Kaggle change. No new Discovery.**
**Cohort: ONLY the already-consumed DEV-005 Discovery partition 247000–247049.**
**This test must NOT be described as new Discovery, Qualification, generalization, or Kaggle evidence.**

---

## 0. Execution engine: validated pure-Python port (2026-09-14)

The authoritative simulator is the Windows CPython 3.14 extension
`external_repos/kaggriculture-cppsim/kagsim.cp314-win_amd64.pyd`
(SHA-256 `7cf5f62b1f47283606ff0d053a5df0045b041b3e117bb4f4c88daca9c5c1d1cc`).
This session runs in Linux (WSL) where no Linux kagsim build exists, Windows
interop is unavailable, and no compiler/network exists — a full-filesystem
scan confirmed no Linux kagsim anywhere.

Execution therefore used **`port/kagsim_py/`**, a clean-room pure-Python port
of `sim/sim.hpp` + `sim/pyrandom.hpp` + `python/kagsim.cpp`, validated to:

- **47,520/47,520 exact checkpoints** on the 6 bundled golden traces
  (per-step money ×2 + market inventory ×9, all steps, both seats),
- **100/100 DEV-005 games bit-identical** to frozen `RAW_RESULTS.json`
  (all match scores, deltas, paired means),
- **400/400 frozen decision events identical** (shops, liquidity,
  expected values, decisions — full price-path validation).

Port manifest + hashes: `port/PORT_MANIFEST.json`. Validators:
`port/validate_golden.py`, `port/validate_dev005.py`. The kill-test runner
(`port/run_killtest_port.py`) asserts port-manifest integrity, then re-asserts
live DEV-005 replay parity (50/50 bit-identical) and one-factor purity as hard
gates. Residual risk (Windows-vs-Linux libm 1-ulp in log/log10 price amps) is
empirically bounded by the validation above: zero divergence across ~51,000
checkpoints. The reference runner `run_horizon_killtest.py` (for the frozen
`.pyd` under Windows Python) is preserved for independent replication.

---

## 1. Phase 0 — Governance / immutability (VERIFIED)

| Artifact | Expected SHA-256 | Observed | Status |
|---|---|---|---|
| V54++ Residual baseline `candidates/compiled_v54_plus_residual.py` (Sub 56146971) | `18402ec6…cb7eeb` | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` | VERIFIED |
| V54++ Shop baseline `candidates/compiled_v54_plus_shop.py` (Sub 56146947) | `f651ccd2…ffd8b8` | `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8` | VERIFIED |
| DEV-005 treatment `candidates/closed_loop_architecture/dev_005_confirmed_shop_scheduler.py` | `f52b1686…e2a78` | `f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78` | VERIFIED, untouched |
| DEV-005 protocol `experiments/EXP-DEV-005/DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_4.md` | `ac69fc60…e9f6` | `ac69fc602083f232792ad5bdabd699e4b9f96e73462f9edc740ccd63c727e9f6` | VERIFIED |
| Simulator `kagsim.cp314-win_amd64.pyd` | (recorded) | `7cf5f62b1f47283606ff0d053a5df0045b041b3e117bb4f4c88daca9c5c1d1cc` | FILE HASH RECORDED (not executable here) |
| One-factor DEV-006 treatment (this test) | `06db94e5…44f5eb` | `06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb` | VERIFIED |

Submission mapping independently corroborated from `DEVELOPMENT_BASELINE_MAP.md`
(56146971 = residual, 56146947 = shop). Frozen submissions untouched. Forbidden
partitions (50050–50099, 214200–214249, 245000–245049, 246000–246049, 50100–50149)
were never executed; the runner hard-fails on any out-of-cohort seed.

### 1.1 Flawed draft treatment rejected and superseded

A prior draft `dev_006_horizon_guard_scheduler.py`
(SHA-256 `13d328f9b6363aceeac9b5b2b9026355b1e3ffcd0d3854d7f44791067cb67091`,
logged in the original `EXECUTION_LOG.txt` §[4/6] at 2026-09-14 16:33 UTC)
**violated one-factor isolation** and was rejected before any seed was executed
under it (the draft run never progressed past governance):

1. It **rewrote the valuation model** (`evaluate_plan_feasibility_and_value`):
   different price multipliers (×1.5/×0.7 vs spot/×0.65), different harvest
   counting, different livestock cycle bases (cow `t_rem//36` vs `//48`, sheep
   `//48` vs `//72`), different base prices (milk 60 vs 160, wool 140 vs 200),
   added animal purchase costs the DEV-005 model never had, and different
   terminal/dead-inventory logic.
2. It changed the **maintenance/reversion behavior**: an already-specialized
   agent below TAU at step 288 would `MAINTAIN_SPECIALIZATION` instead of
   reverting to baseline exactly as DEV-005 does.
3. It changed observation plumbing (`self.seat` vs `obs["player"]` farm lookup).

The draft was replaced by a file verified to be an **exact copy of DEV-005
plus the guard only** (see §3). The draft bytes are preserved at
`/tmp/dev006_draft_flawed.py` (SHA `13d328f9…`) for audit; the original
governance log lines are preserved in `EXECUTION_LOG.txt`.

---

## 2. Phase 1 — Reconciliation of the two losses (from frozen telemetry + code)

Full analysis: `FORENSIC_AUDIT.md`. Summary of simulator-independent findings:

| Item | Seed 247025 | Seed 247034 |
|---|---|---|
| Confirmation step | 288 (Day 12) | 288 (Day 12) |
| Confirmed shop | YARN_STORE (4th unlock) | YARN_STORE (4th unlock) |
| Shops at 72/144/216 | PET_CAFE / +PET_CAFE / +BRUNCH_SPOT | ICE_CREAM / +PIZZA / +SMOOTHIE |
| Decisions 72/144/216 | REJECT_UNCONFIRMED ×3 | BASELINE ×3 (model saw no value) |
| Projected route value at 288 | +$13,491.80 | +$6,027.68 |
| Liquidity at 288 | $13,638 | $15,587 |
| Remaining horizon | 432 steps | 432 steps |
| Terminal candidate cash | $58,338 | $120,362 |
| Terminal baseline cash | $60,182 | $125,755 |
| Realized paired delta | **−$1,844** | **−$5,393** |
| Model prediction error | −$15,335.80 | −$11,420.68 |

Both matches within each seed are bit-identical (seat-symmetric telemetry
verified across all 400 decision events).

### 2.1 Structural facts established without the simulator

1. **First-specialization step perfectly stratifies outcomes.** 72 → 8 ties;
   144 → 7 ties; 216 → 5 large wins; 288 → 2 losses (exactly the two
   first-at-288 seeds; no other seed first-specialized at 288); never → 28 ties.
2. **The valuation model overpredicts in 21 of 22 activated seeds**
   (errors −$1.9k…−$20k). It scales revenue with `t_rem` but has **no
   amortization cliff**: wool cycles `t_rem//72` give 7 cycles at step 216 vs
   6 at step 288 (86% of value retained in-model), and it **never charges
   livestock purchase costs at all** (revenue-only livestock section).
3. **The 288-switch buys NO sheep.** Route-tape analysis of the frozen baseline
   (`_V56_YARN_ROUTE` vs `_V55_LIVE_ROUTE`; replay indexes tape by game step):
   all YARN sheep buys sit at tape-steps ≤265, so a step-288 switch skips them
   entirely. The post-288 behavioral delta is farm-movement proposals plus
   feed (wheat-product), fertilizer, milk/carrot-sell, and hire suffix
   differences, residual-gated — executed against a cow-heavy herd built under
   the LIVE tape. The DEV-005 audit narrative ("buying sheep at Step 288")
   is contradicted by the tape and is corrected in `FORENSIC_AUDIT.md`.
4. **First economic divergence is structurally at step 288**: pre-288 play in
   both seeds was bit-identical backbone policy; step 288 is the first step
   where `active_policy` differs from baseline. Per-step money/inventory
   traces, executed purchase lists, and production/sales decomposition require
   simulator replay (pending, §0).

---

## 3. Phases 2–3 — Mechanism definition and one-factor intervention (FROZEN)

**HORIZON_GUARD**: a NEW specialization (transition from `BASELINE_BACKBONE`
to a specialized route) is allowed only when `remaining_steps >= H`,
with **H = 500 (POST-HOC TEST VALUE — not preregistered, not swept)**.

Semantics (deliberately minimal):

- The guard intervenes **only** when DEV-005 logic would select
  `SPECIALIZE_CONFIRMED` as a baseline→specialized transition with
  `remaining_horizon < 500`. That decision becomes `REJECT_HORIZON`
  (stay on baseline).
- Maintenance of a pre-existing specialization, reversion to baseline, shop
  confirmation, route candidates, valuation, liquidity, worker routing,
  preemption, and terminal logic are **bit-for-bit DEV-005**.
- With checkpoints at {72, 144, 216, 288} and H=500, the guard can only
  trigger at step 288 (remaining 432). "Step ≤216" and "remaining ≥500" are
  equivalent on this checkpoint grid.

The treatment diff against DEV-005 is confined to: the `HORIZON_GUARD_THRESHOLD`
constant + comment, class/docstring rename, one telemetry counter, the guard
branch, two additive telemetry fields, `REJECT_HORIZON` event routing, and the
`kaggle_agent` rename. Verified by `diff -u` (see FORENSIC_AUDIT.md §8).
AST zero-leakage audit: clean (0 violations; `self.seed` telemetry attribute
is identical to DEV-005's and is not a leak vector).

### 3.1 Preregistered predictions (falsifiable)

1. `REJECT_HORIZON` fires at step 288 in **exactly** seeds 247025 and 247034
   (the only first-at-288 seeds), both matches.
2. Those two seeds become **exact ties** (delta $0.00): pre-288 play was
   bit-identical backbone, so a guarded run must equal the baseline run
   bit-for-bit. Any deviation ⇒ non-determinism or bug.
3. All other 48 seeds are **bit-identical** to DEV-005 (guard never triggers).
4. Cohort recovery exactly **+$7,237.00** (mean +$144.74); no new losses,
   no sacrificed wins.
5. Live DEV-005 replay matches frozen `RAW_RESULTS.json` **bit-for-bit**
   (100/100 matches + deltas), validating engine parity.

The runner enforces (2)–(5) as hard gates (`replay_parity_ok`,
`one_factor_purity_ok`) and exits non-zero on violation.

---

## 4. Phase 4 — Execution (COMPLETE)

Runner: `port/run_killtest_port.py` (one-factor revision, port engine).
Reference `.pyd` runner: `run_horizon_killtest.py` (preserved for replication).

- **Both arms live, identical CRN**: per seed, DEV-005-vs-baseline (2 games)
  and DEV-006-vs-baseline (2 games) = 4 games/seed, 200 games total.
- Primary comparison: DEV-006 paired mean **minus** DEV-005 paired mean
  (NOT vs V54++). Frozen DEV-005 Discovery result never modified.
- Runtime: 441 s. Log: `EXECUTION_LOG.txt` (appended; draft-run lines preserved).

## 5–6. Results (see STATISTICS_RECOMPUTED.json, VERDICT.md)

| Metric | Value |
|---|---|
| DEV-005 replay mean | +$797.76 (bit-identical to frozen, 50/50) |
| DEV-006 guard mean | +$942.50 |
| Mean paired diff (guard − original) | **+$144.74** |
| Total cohort recovery | **+$7,237.00** |
| 247025 / 247034 | −$1,844 → $0.00 / −$5,393 → $0.00 |
| Losses introduced / wins sacrificed / other changes | 0 / 0 / 0 |
| All 5 wins (216-entry, +$5.4k…+$13.1k) | preserved bit-identically |
| Replay parity / one-factor purity gates | PASS / PASS |

All five preregistered predictions (§3.1) confirmed exactly.

## 7–11. Verdict: SUPPORTED (see VERDICT.md)

Criteria A–D pass cleanly with zero elsewhere-effects. Criterion E passes with
a documented nuance: the recovery is 100% caused by blocking the two 288
entries (purity-gated), but instrumented traces show the 288-entry harm is
mediated by own-farm suffix mismatch AND shared-market/RNG world channels —
broader than pure own-farm amortization (FORENSIC_AUDIT.md §§5–6). H=500 is
supported as a predictive gate; the micro-mediator motivates the H2
runway-aware hypothesis for future preregistered work, not implemented here.

Phase 12/14 stop rule in force: DEV-005 is NOT qualified; no Qualification
(50050–50099), no holdout (214200–214249), no sweep, no submission.
Next justified step: freeze DEV-006 (DEV-005 + H=500, SHA `06db94e5…`) as a
NEW treatment and run fresh Discovery on virgin seeds — await review.
