# SOURCE MAP — Dmitrii LB2800 submission

Source: `extracted_agents/dmitrii_lb2800/`
(`main.py`, `policy.py`, `router_parent.py`, `actions.json`,
`unit_model.py`, `terminal_planner.py`, `settings.json`).

Engine grounding: `unit_model.py` pins engine 1.32.7
(SHA `bc8a5487…`). Market/day/shop mechanics below are cross-checked
against `external_repos/kaggriculture-cppsim/sim/sim.hpp` (1.32.7
mirror) and `env_backup_1_30_1/kaggriculture.py` (1.30.1; flagged on
drift: COW $600 vs $400, town-center interval 12 vs 24, shop draw
without vs WITH replacement — cppsim/1.32.7 is authoritative).

## 1. Files and control flow

```
main.py: loads settings.json, imports policy.py, build_agent(settings) -> agent(obs, cfg)
policy.py: ShopClosure
  |- router_parent.Policy (parent: tapes + repairs)      [steps 0..711, 713..718 fallback]
  |- terminal_planner (7-turn shadow optimizer)          [steps 712..718 when accepted]
  |- telemetry only (no game effect)
router_parent.py: SHOP_PLANS + Policy + repair_weeds + advance/subtract sales + liquidate
actions.json: 13 tapes x 719 steps, the strategic content
unit_model.py: exact 1.32.7 unit/decay semantics (moves, PLANT/WATER/HARVEST,
  FEED/CARE/COLLECT, BUILD, DIG, FERTILIZE, DROP/PICKUP/PLACE, decay)
terminal_planner.py: simulate/dominates/plan_terminal/terminal_action/recovery
settings.json: {"enabled": true, "max_simulations": 128, "passes": 1, "proposals_per_actor": 8}
```

Per-turn dispatch (`ShopClosure.act`):

1. Rewind/duplicate detection (`step==0` or `step<=last`): drop accepted
   plan, drop parent player state (fresh logical lifetime).
2. If an accepted plan exists and `712<=step<=718`: emit
   `terminal_action`; on `abandoned` without physical deviation, resume
   parent once (`_resume_parent`) and forget the plan.
3. Else if not step 712 (or disabled): `parent.act(obs)` directly.
4. At step 712 exactly: `shadow_baseline` (clone parent, roll 712..718 on
   a deep-copied projection, guard every step) → compare real parent
   callback to shadow step-712 output (must be equal) → `plan_terminal`
   (bounded search) → accept or fall back to parent output.

Parent dispatch (`Policy.act`):

1. Fresh `DayState` on first sight or step rewind.
2. `step==144`: `plan = SHOP_PLANS.get(first_two_shops, 0)`.
3. `step==648`: `plan = 2` (forced, unconditional).
4. `action = deepcopy(tapes[plan][step])`.
5. `repair_weeds`, `subtract_advanced_sales`, `advance_sales`,
   truncate market to 10 orders.
6. `step==718`: discard everything, return `liquidate(view)`.

Executed-tape map (follows from 2–3): steps 0..143 always tape 0;
144..647 the selected tape; 648..718 always tape 2. All other cells are
dead code (see `analysis/01_tape_similarity.md`).

## 2. State representation

- `DayState` per player seat: `plan` (int), `last_step`, `day`,
  `queues` (per-worker deques, expire at dawn), `sale_due_step`,
  `advanced_sales` (expire next turn).
- `FarmView`: own tiles, worker positions, carried inventories, shed
  (clamped non-negative), public prices. Opponent state is never read.
- `ShopClosure`: `plans`/`last_steps` per seat, parent `Policy`
  (tapes + players), telemetry dict.
- Terminal plan (when accepted): `baseline` (7 parent actions),
  `actions` (7 optimized actions), `expected_states` (7 physical
  states), `parent_states_before` (7 logical states, for resume),
  `changed_workers`, `changes`, `certificate`, flags
  (`abandoned/deviated/safety_failure`, recovery counters).

## 3. Shop-selection logic

`SHOP_PLANS`: 15 ordered pairs -> plans 1..12 (details in
`SHOP_ROUTER_ANALYSIS.md`). All 15 pairs contain `YARN_STORE`; the
other 49 of 64 reachable pairs fall through to plan 0. Selection runs
once, at step 144, and is never revisited. At step 648 the plan is
overwritten with 2 unconditionally.

## 4. Strategy-selection checkpoints

Two, both open-loop (no valuation, no feasibility re-check):

- Step 144 (day-6 dawn): 2 shops known -> plan 0..12.
- Step 648 (day-27 dawn): plan := 2.

No checkpoint at 72, 216, or 288. Later shop reveals (days 9–24) never
affect the macro plan.

## 5. Reactive overrides

- `repair_weeds`: per-worker same-day queue; if the queued head is
  PLANT/BUILD_COOP/BUILD_PASTURE and the worker stands on WEED, emit
  DIG and keep the blocked command queued. Queues clear at dawn.
- `advance_sales`: copy next-step planned SELLs (except WHEAT/
  FERTILIZER, except already-selling, except price<2, except
  step%4==0, except next unlock step) into this step when projected
  shed stock covers them; record in `advanced_sales`.
- `subtract_advanced_sales`: at the due step, decrement matching SELL
  quantities by the advanced amounts (can leave `SELL x 0`).
- `liquidate` (step 718): DROP for shed-adjacent loaded workers, then
  SELL projected shed sorted by price*quantity descending.
- Terminal `terminal_action` / `_recover_observed`: positional plan
  while observations match expectation; cargo-salvage recovery
  (return-to-shed + DROP/PLACE) after deviation; pre-deviation
  abandonment resumes the parent once.

## 6. Terminal planner (summary; full detail in TERMINAL_PLANNER_ANALYSIS.md)

- Window 712..718 (7 turns, no day boundary inside).
- `simulate`: exact own unit/decay + SELL-stock transitions on cloned
  state; recomputes step-718 action via `shop_liquidation` (original
  final rule on trial's own physical state); tracks per-actor
  deposits, per-turn pre/post-market shed, sold totals, DROP overflow
  units. Does NOT model shared prices (uses step-712 prices as fixed
  weights), opponent, or RNG (no RNG inside the window).
- `plan_terminal`: worker-by-worker single pass; per worker up to 8
  route proposals (0/1/2 resource bundles + return-to-shed + DROP,
  padded with PASS); each trial simulated (cap 128 sims); adopt only
  on strictly higher stock value AND `dominates` AND no-stealing;
  final acceptance needs changed workers + physical deposit gain +
  all-sold-deltas >= 0 + some sold-delta > 0.
- `dominates`: zero candidate overflow + every row's pre-market shed,
  cumulative sold, and per-actor deposits all superset baseline's.
- Objective: `sum((sold + final_shed) * price712)` over products.

## 7. Rollback / recovery behavior

| Layer | Trigger | Response |
|---|---|---|
| Router rewind | step 0 or non-monotonic step | fresh DayState, plan reset to 0 |
| Weed queue | dawn | queues discarded (work lost, never spills) |
| Advanced sales | due step arrives | quantities subtracted; state cleared |
| Terminal plan | non-consecutive callback | abandon + safety_failure |
| Terminal plan | physical/baseline mismatch | abandon; salvage if deviated, else parent once |
| Terminal plan | pre-deviation abandon | `_resume_parent` (restore logical state, run parent) |
| Shadow build | any guard failure at 712 | planner never engages; parent acts all 7 steps |

There is no mid-game macro rollback: a wrong plan-144 choice executes
to step 648 regardless.

## 8. Objective function

No global objective is optimized at runtime. Implicit objectives:
tapes maximize (design-time search) final money under unknown shops;
`advance_sales` minimizes sale latency; terminal planner maximizes
physical delivered stock value at frozen step-712 prices subject to
dominance. Reward = final `farm["money"]`.

## 9. Dominance tests

Only in the terminal planner (`dominates` + no-stealing + acceptance
conjunction). The router has no dominance concept; the shop router has
no valuation at all.

## 10. Limits on simulation

- Router: zero simulation; `projected_shed` is a one-turn
  order-preserving estimate (PICKUP/DROP/PLACE near shed only).
- Terminal: 7-turn window, <=128 simulations, 1 pass, <=8 proposals/
  worker, <=2 resource bundles per proposal, single-product price
  vector frozen at step 712, no opponent, no RNG, no day boundary,
  worker cap 32 inventories, order cap 10.
- Settings gate: only (64,1,4) and (128,1,8) variants are constructible.

## 11. Deliberate simplifications / assumptions

1. Tapes assume the "happy path" farm: hires succeed on schedule,
   no weed-blocked PLANT/BUILD in 712..718, shed never overfull at 712.
2. `projected_shed` ignores HARVEST/FEED/market-execution effects.
3. `advance_sales` assumes next-step tape sales are desirable one turn
   early whenever stock and price>=2 allow.
4. Terminal sim assumes frozen prices, no opponent interference, and
   that step-718 liquidation recomputation matches the engine.
5. Shop router assumes the first two shops (and YARN presence in them)
   are a sufficient statistic for the whole-game plan.
6. Plan-2 terminal regime assumes converging all games to one shared
   648..718 tape is safe regardless of prior divergence (mitigated by
   the fact that all tapes share one agronomic skeleton).
7. `liquidate` assumes price*quantity ordering fits 10 slots (drops
   zero-stock products first).
