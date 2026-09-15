# TERMINAL PLANNER ANALYSIS — the 7-turn shadow optimizer

Code: `policy.py` `ShopClosure.shadow_baseline/_resume_parent/act`;
`terminal_planner.py` all; live settings (128, 1, 8).

## 1. Lifecycle

1. Steps 0..711: pure parent (tapes + repairs). Planner code present
   but dormant; `plans` empty.
2. Step 712 (first of 7): `shadow_baseline` — deep-copy parent
   players (NOT the 13 tapes; tapes immutable, actions deep-copied
   per act), deep-copy obs, roll steps 712..718 through
   `shadow.act` + `simulate` per step, asserting
   `run['actions'][0] == action` (model/parent agreement) each step.
   Guards: parent warm through 711 on plan 2; config pinned
   (10x10/24/720, shed 100, 10 orders); NO weed-blocked op in live
   queues or tape2 712..718; shed valid/≤100, shed+carried items
   supported; nonfinal markets are 9-product SELL≥100. ANY failure
   -> parent acts; planner never engages (silent abstention +
   telemetry case).
3. Real parent callback at 712 must EQUAL shadow step-712 output, or
   abstain (detects shadow/live divergence at the entry point).
4. `plan_terminal`: baseline = `simulate(..., detailed=True)` on the
   7 parent actions; worker-by-worker single pass, ≤8 proposals/
   worker, ≤128 sims; adopt trials only on (value gain AND
   dominates AND no-stealing); final acceptance gate
   (§5); on accept, store plan incl. `expected_states`,
   `parent_states_before`, certificate.
5. Steps 712..718: `terminal_action` per step — emit planned action
   while physical state AND effective parent action match
   expectation; at 718 recompute via `shop_liquidation` on LIVE
   state/prices. On mismatch/non-consecutive: abandon; salvage if
   deviated, else resume parent once and forget.

## 2. Shadow-state construction

`copy(parent)` (shallow: shares immutable tapes) +
`deepcopy(players)` (mutable queues/sales) + `deepcopy(obs)`,
projected forward one step at a time with `step/day/hour` patched
(712..718 share day 29/30... precisely: 712//24=29, all 7 steps on
day 29 — no dawn inside). Each projected step: `shadow.act`
(includes repairs + advance/subtract, exactly as live) then
`simulate` for physical roll. `states_before` (7 logical parent
states) saved for `_resume_parent`.

## 3. Objective

`_value = Σ (sold + final_shed) × price712` over the 9 products.
Frozen step-712 public prices; sold counts units moved shed→market
during the window; final shed counts leftovers at the same prices
(liquidation-equivalent). Maximized subject to dominance (never a
trade: adopt iff strictly greater AND dominating).

## 4. Candidate generation

Per worker, per start-offset 0..6: enumerate resource bundles =
standing-yield HARVESTs (mature only: crops past first_yield_day,
any animal yield>0) + COLLECT_FERTILIZER, excluding cells/ops owned
by another actor in the CURRENT best run (no-steal pre-filter);
keep reachable ones (walk + ops + return ≤ remaining steps); rank
by value/distance; variants = carry-only closure (if loaded) + top-6
singles + top-3×top-3 pairs; each variant routed (walk→ops→
nearest-shed→DROP, PASS-padded); reserve 2 direct-return variants;
keep ≤8/worker. NOTE: no PLANT/WATER/FEED/CARE/BUILD/FERTILIZE
proposals — the optimizer only reaps and ferries. (FERTILIZE absence
is notable: day-29 fertilizing cannot pay — 3-day window, game ends.)

## 5. Movement / harvest / fertilizer / inventory handling

- Movement: Manhattan `_walk` (x-first); return = walk to NEAREST
  shed-access tile + DROP. No collision/pathing model (engine has
  none — moves are single-step, always legal in-bounds).
- Harvest candidates: any tile with yield_units>0 that is mature
  (crops) or any animal yield; value = units × price712.
- Fertilizer candidates: `fertilizer_available` animal tiles;
  value = 1 × FERT price.
- Carried inventory: valued in variants (`carried`); proposals
  replace the worker's whole suffix from the offset, so the
  optimizer can abandon baseline carries — BUT the dominance +
  deposit-prefix + no-steal gates (§6) forbid stranding them.

## 6. Dominance / overflow / no-stealing

- `dominates`: candidate overflow==0 AND for EVERY row: pre-market
  shed ⊇ baseline's, cumulative sold ⊇ baseline's, per-actor
  cumulative deposits ⊇ baseline's. (Row-wise prefix dominance —
  the candidate is never behind at any turn, for any worker.)
- Overflow: DROP overflow units counted during sim (cargo destroyed
  by shed-cap discard); any overflow fails dominance.
- No-stealing (second gate at adoption): every harvest/fertilizer
  acquisition by OTHER actors in the current best must still occur
  (same cell, same op, same actor, ≥ quantity) in the trial.
- Acceptance (third gate): changed workers non-empty AND some actor
  deposited strictly more of some product AND every product's sold
  delta ≥ 0 AND some product's sold delta > 0 AND final re-sim
  dominates AND 712..717 markets unchanged.

## 7. Simulation limits

max_simulations=128 (live; 64 in default), passes=1, 16-worker…
precisely: proposals/worker=8, bundles≤2, sims counted per trial
(+1 detailed re-sim per adopted worker, uncounted). Price vector
frozen. No opponent. No RNG (none exists in-window). No day
boundary (rejected if a boundary falls inside). Worker inventories
must equal n≤32 or Unsupported. Order cap 10 enforced in `_validate`.

## 8. Final-turn liquidation

Step-718 tape action is NEVER executed as taped: `simulate` replaces
it per-trial with `shop_liquidation` (the router's own DROP-near-shed
+ price×qty-ordered SELL, computed on THAT trial's physical state);
`terminal_action` at 718 recomputes it on LIVE state with LIVE
prices. All candidate/listed 718 markets are therefore
apples-to-apples: each trial is scored with its own realizable
liquidation, and live execution uses live prices (never the frozen
planning prices) for the final sale.

## 9. What makes it safe (explicit)

1. Abstain-by-default: 10+ guard clauses; any failure → parent acts.
2. Entry handshake: live-712 must equal shadow-712.
3. Frozen prices + dominance (never-behind-every-turn) instead of
   expected-value betting: the plan can only win ties, never lose
   them, PROVIDED the model is exact — and in-window the model IS
   near-exact (deterministic unit/decay rules, no RNG, no day
   boundary, markets 712–717 fixed clearing SELLs whose execution
   `min(requested, stock)` is also modeled).
4. Residual model risk (opponent price moves on SHARED prices,
   SELL-execution interleaving vs the modeled solo execution) is
   confined to the VALUE comparison, not to physical legality: the
   dominance certificate is in UNITS (shed/sold/deposits), which the
   opponent cannot alter — opponent can only change the unit PRICES
   that weight an already-dominating physical outcome. Worst case:
   a physically-dominating plan worth less money than hoped — still
   ≥ baseline units of every product at every turn.
5. Stepwise re-verification: any live deviation kills the plan
   before the next planned command issues; recovery never replays
   stale positions.
6. Shed-100/order-10/rectangular-window config pins: the planner
   refuses to run in any configuration it was not validated for.

## 10. Deliberate limits (what it cannot do)

- Cannot change markets 712–717 (fixed clearing) or the 718 rule.
- Cannot plant/water/feed/care/build/fertilize (by proposal design).
- Cannot coordinate two workers in one proposal (worker-by-worker
  greedy, 1 pass — no joint search, no repair pass).
- Cannot see past 718 or past frozen prices (terminal myopia is the
  safety case, §9.4).
- Costs up to 128 full 7-step sims at step 712 (planning_ms
  telemetered; worst case bounded by construction, not by wallclock).
