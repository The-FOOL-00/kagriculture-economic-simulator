# V28 — A7 SPECIFICATION (derived from V27 sources, no inference)

Sources: `V27_FINAL_REPORT.md` §8, `V27_ABLATION_PLAN.md` §2,
`V27_ABLATION_RESULTS.md` §§2–5, `V27_BEHAVIORAL_DELTA_LEDGER.md`,
`V27_COUNTERFACTUAL_ANALYSIS.md`, `V27_REGIME_DECOMPOSITION.md`,
`aec/backbone/v27_ablation_adapters.py` (frozen bytes).

## 1. Exact behavioral change (vs V3)

At game step 0 ONLY: V3's agent is called normally (full step-0
processing runs), and if — and only if — its emitted market action is
exactly `[BUY_PRODUCT WHEAT 50, SELL WHEAT 50]`, the two order quantities
are resized to `[BUY_PRODUCT WHEAT 30, SELL WHEAT 30]`. All other steps,
all other action fields, all other step-0 shapes: bit-identical to V3.

Observed in V27: the rewrite fired on all 240 A7 matches (money1 =
3054/2946 everywhere); the unexpected-shape flag never fired.

## 2. Exact implementation change (vs V3)

`V27AblationAdapter("V27-ABL-A7")` wraps an isolated exec-loaded V3
`agent` callable (same loader semantics as `V3BackboneAdapter`: fresh
namespace `v25_p3_isolated_v3_<id>`, no `sys.modules` reuse):

- `act()`, step 0: `raw = v3(obs, cfg)`; if `raw["market"] == WASH50`:
  replace with `WASH30`, set `step0_rewritten=True`; else set
  `step0_unexpected_shape=True` and pass through unchanged.
- `act()`, steps ≥ 1: return `v3(obs, cfg)` unmodified (dispatch=False).
- Continuation policy mirrors the flags for counterfactual rollouts.

11 lines of behavioral code (the `rewrite_step0_wash` branches); no
livestock, sales, labor, route, expansion, or market code of its own.

## 3. Invariant behavior (A7 ≡ V3)

- Full step-0 processing: route/state init, market-state calibration,
  reservations/horizons — all run (this is what P3's bypass skips).
- Unit actions at every step (farmer + hands): V3's own, unmodified.
- All market actions at steps ≥ 1: V3's reactive policy, unmodified.
- Farm structure, hires, animals, plants: V3-determined.
- Step-0 farmer/hands fields: whatever V3 emits, unmodified.

## 4. Changed behavior (A7 ≠ V3)

- Exactly two integers at step 0: wash BUY 50→30, wash SELL 50→30
  (conditional on the exact-shape assertion holding).

## 5. Expected economic mechanism (V27's exploratory account)

Two large additive factors, both kept by A7 (fits all 9 ablation cells,
residuals <$100):

1. **30-qty (≈ +$1,500 vs 50):** the 30/30 wash nets +$54 where V3's
   50/50 nets −$54 (zero-sum lockstep; +$108 every game), and — more
   importantly — the wash path reshapes downstream fills: A1-vs-A7
   (qty-only contrast) issues IDENTICAL post-wash market orders yet ends
   $1,286 apart because the same orders FILL differently
   (inventory/price cascade from the wash path). Units part at t=153.
2. **step-0-init (≈ +$1,450 call-vs-bypass):** V3's step-0 processing
   calibrates internal market state; starting cold (P3's bypass)
   misfires LATE sells. A3-vs-A7 unit streams are identical all 719
   turns — init's value flows entirely through late reactive MARKET
   decisions (first market divergence t=433 at 30-qty). V3's step-0
   market is exactly [BUY50, SELL50] on all 200 trajectories, so the
   init effect is purely internal-state calibration, not skipped orders.

P3 = qty(+1,500) − init(−1,450) ≈ +$60 by cancellation. A2 (50/bypass)
= −$1,543 (toxic). A7 (30/call) = +$1,451: keeps both. Dispatch ≈ $0.

## 6. Why A7 differs from V3

One deliberate change: the smaller opening wash. V27's exploratory read
is that V3's 50-wash over-commits opening inventory/cash and its own
step-0 calibration is valuable — A7 keeps the calibration while taking
the cheaper wash.

## 7. Why A7 should plausibly generalize (exploratory rationale only)

- Systematic, not threshold-lottery: 119/120 wins, median +$1,286 —
  the median (not just the mean) is large, unlike P3's tip-driven mean.
- Mechanism-level: qty flows through fill cascades present in every
  game; init flows through late reactive markets present in every game.
- Seat-symmetric in V27 (reported per-seat; both seats tip/keep).
- Selected post-hoc on consumed seeds — hence V28. NOTHING in §7 is
  confirmatory; it is the hypothesis V28 tests.
