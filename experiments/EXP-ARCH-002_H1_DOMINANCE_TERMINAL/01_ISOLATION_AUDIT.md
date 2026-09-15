# EXP-ARCH-002 H1 — ISOLATION AUDIT

**Experiment**: `EXP-ARCH-002_H1_DOMINANCE_TERMINAL` (prospective; not yet
preregistered)
**Document**: `01_ISOLATION_AUDIT.md`
**Date**: 2026-09-15
**Status**: AUDIT ONLY — input to preregistration, not a protocol, not an
implementation. No candidate was created, no game or seed was executed, no
Kaggle contact occurred, no frozen artifact was modified.
**Auditor**: Muse Spark (read-only session)
**Question**: can a dominance-gated terminal optimizer (H1, after Dmitrii's
verified 712–718 planner) be grafted onto our frozen baseline such that the
treatment differs from the baseline ONLY inside the terminal window and ONLY
through terminal worker re-routing plus a preregistered step-718 market rule?

**Verdict** (justified in §24): `ISOLATION PASS — suitable for ARCH-002
preregistration`, conditional on freezing the 14 protocol requirements in §23.
PASS means: the repository establishes the baseline side exactly, proves no
structural contamination pathway, and converts every residual question into a
freezable protocol constraint. PASS does not claim H1 will activate often,
gain money, or beat anything — those are empirical questions for the
experiment.

## §0. Citation foundation: the frozen baseline's executed code

The frozen baseline `candidates/compiled_v54_plus_residual.py` (SHA-256
`18402ec6…`, verified in the takeover session) embeds its policy machinery as
nested compressed bundles. This audit verified by static recursive
decompression (no imports, no execution; method in Appendix B) that all 15
embedded modules are byte-identical (modulo CRLF/LF) to repo-visible copies:

- `scripts.v19_terminal` ≡ `scratch/bundled_modules/scripts.v19_terminal.py`
  (terminal overlays: `terminal_market`, `monetizable_terminal_units`)
- `v49.residual_controller` ≡
  `scratch/bundled_modules/v49.residual_controller.py` (also ≡
  `forensic_verification/extracted_sources/v49_modules/v49_residual_controller.py`,
  SHA `0b09713a…`)
- `v50.hybrid` ≡ `scratch/bundled_modules/v50.hybrid.py`
- `scripts.v21_route_memory_search`, `scripts.v22_market_impact`,
  `scripts.v22_weed_repair`, `v23.planner`, `v23.policy_library`,
  `v23.simulator`, `v23.state_encoder`, `v24.market_maker`,
  `v44.gold_floor`, `v48.fast_route_router`, `v50.suffix_router`,
  `v19_terminal` ≡ their `scratch/bundled_modules/` namesakes (all 15 match).

Every module citation below therefore points at a readable repo file AND at
the frozen baseline's executed logic simultaneously. Supporting record:
`research/compiled_semantic_equivalence.md` §1–§4 (719-turn route equality,
parameter invariance, S2 predicate identity, overlay equivalence PASS).

Live execution path of the frozen baseline per turn (established from the
sources above; dead code excluded in §0.1):

1. Outer `agent()` resolves step, updates `_SHOP_STATE`, selects route via
   `_select_route`, and calls exactly one of `_POLICY_BACKBONE/_YARN/_BAKERY`
   (`candidates/compiled_v54_plus_residual.py:4433–4466`).
2. Each policy = `build_route_value_hybrid(route, config)`
   (`scratch/bundled_modules/v50.hybrid.py:12–41`): `replay_policy` (route
   action at clamped step,
   `scratch/bundled_modules/scripts.v21_route_memory_search.py:4–8`) →
   `wrap_weed_repair` (DIG + retry + 8-step replay,
   `scratch/bundled_modules/scripts.v22_weed_repair.py:26–122`,
   `replay_steps=8` via `scratch/bundled_modules/v23.planner.py:20–33`) →
   `reorder_sell_slots` (SELL reorder only,
   `scratch/bundled_modules/v23.policy_library.py:54–79`) → residual
   controller (`_repay` → `_release_pending` → `_defer` → `_preempt` →
   fronting reorder → optional market-maker → step-718 `terminal_market` →
   truncate to `maximum_orders`,
   `scratch/bundled_modules/v49.residual_controller.py:743–816`).
3. Outer overlays in fixed order: `_v60_seed_trim`
   (`candidates/compiled_v54_plus_residual.py:4469`), `_v60_shed_guard`
   (`:4472–4473`), `_route_loaded_units` on 713–716 (`:4476–4477`),
   `_TERMINAL_UNITS` on 717–718 (`:4480–4481`), `_TERMINAL_MARKET` at 718
   (`:4484–4485`).

## §0.1 Dead or disabled code in the live path (excluded from the model)

- `v23.policy_library.terminal_liquidation` (`:134–151`) and
  `plan_sell_quantities` (`:82–131`): zero callers in any embedded module or
  outer file (static grep). Only `scripts.v19_terminal.terminal_market` is
  wired (v49 `:801–804`, outer `:4484–4485`).
- `v44.gold_floor`, `v48.fast_route_router`, `v50.suffix_router`: embedded
  but never imported by live code (static grep over all 15 modules plus the
  outer V54/V62/V66 files). Not executed.
- `defer_enabled=False`, `market_maker_enabled=False`: dataclass defaults
  (`scratch/bundled_modules/v49.residual_controller.py:92,107`); the frozen
  `_V54_CONFIG` dict
  (`candidates/compiled_v54_plus_residual.py:1976`) and the three
  `_CONFIG_DICT` overrides (`:4395–4399`) set neither key. `_defer` always
  returns its input (`v49:542–548`); the market-maker branch never runs
  (`v49:799–800`). The v24 helpers `_project_private_after_actor` and
  `_animal_count` ARE live (`v49:150–185,610–647` import them from
  `v24.market_maker`).
- The v58/v59/v60 agent entrypoints (`kaggle_agent_v58/v59/v60_composite`)
  and `_V58_STATES`-driven routing are never called by the outer residual
  agent; `_V58_STATES` stays at its `{0:{},1:{}}` initializer
  (`candidates/compiled_v54_plus_residual.py:3626`; sole write at `:3794`
  sits in the uncalled v58 agent). Consequence: `_v59_route` (used only by
  `_v60_seed_trim`, `:4135`) always takes the `mode="base"` path (`:3891`)
  and returns a route from the first shop only (`:3914–3924`) — which can
  differ from the outer agent's actual route (e.g. outer `bakery` vs
  seed-trim `backbone`). Pre-existing baseline property; in-window it is
  moot because `_v60_seed_trim` provably no-ops on steps 700–718 (§1.3).

## §1. Exact current baseline terminal behavior

### §1.1 Per-step pipeline inside steps 712–718

| Step | Unit ops source | Market source | Overlay behavior (cites) |
|---|---|---|---|
| 712 | route replay + weed repair + (no recall yet) | route SELLs + fronting reorder only | No outer terminal overlay fires at 712 (`:4476–4485` gates start at 713). Controller: preempt OFF (≥700, §18), `_repay` may still cut SELLs if dues carried (`v49:476–503`). |
| 713–716 | same, then `_route_loaded_units` reroutes a loaded unit one step toward shed access iff its Manhattan distance to shed access EQUALS `718 − step` (`:4360–4389`, equality at `:4384`; SELLABLE-cargo filter at `:4375–4379`) | same as 712 | `_TERMINAL_UNITS`/`_TERMINAL_MARKET` do not fire. |
| 717–718 | same, then `monetizable_terminal_units`: loaded unit on shed access → DROP; at 717 only: loaded unit at distance 1 → step toward shed; unloaded unit on shed access standing on yield>0 tile → HARVEST (`scratch/bundled_modules/scripts.v19_terminal.py:264–308`) | 717: same as 712. 718: controller-internal `terminal_market(replace=True)` (`v49:801–804`) runs first; outer `_TERMINAL_MARKET(rule="collision", replace=True)` (`:4484–4485`) runs last and recomputes from the post-`_TERMINAL_UNITS` action, so it sells cargo dropped by `_TERMINAL_UNITS` (projection reads unit orders, `scripts.v19_terminal:68–128`). Double application is idempotent (same projection input → same rows). | `_route_loaded_units` gate ends at 716 (`:4361`). |

`_TERMINAL_MARKET` = `terminal_market` (`:4344`), `_TERMINAL_UNITS` =
`monetizable_terminal_units` (`:4346`), `_MOVE_TOWARD`/`_SHED_ACCESS`/`_SELLABLE`
bound from the same module's globals (`:4347–4349`).

### §1.2 What the routes propose in-window (static decode of frozen blobs)

All six live routes are exactly 719 actions (indices 0–718). Decoded
operation mix over steps 700–718 (method: Appendix B):

- `_V56_BACKBONE_ROUTE`: moves 141, WATER 25, HARVEST 27, DROP 15,
  COLLECT_FERTILIZER 14, CARE 5, PASS 1; market: SELL MILK×3, WOOL×2,
  CARROT×3, FERTILIZER×4, WHEAT×7. Step-718 market: three 1-unit SELLs
  (WHEAT/FERTILIZER/WHEAT); step-718 farmer COLLECT_FERTILIZER with hands
  mid-field (cargo strands without recall).
- `_V56_YARN_ROUTE`, `_V58_BAKERY_YARN_ROUTE`, `_V57_PET_ROUTE`: identical
  count profiles (WATER 22, moves 120, HARVEST 27, DROP 15,
  COLLECT_FERTILIZER 11, CARE 5, PASS 28; market: BUY_PRODUCT WHEAT×5, SELL
  WHEAT×10/CARROT×3/FERTILIZER×4/WOOL×1/MILK×1/STRAWBERRY×1); step-718
  market EMPTY and all units PASS. (Count-identical; byte-identity of the
  three blobs was not checked and is not needed.)
- `_V58_SMOOTHIE_ROUTE`: moves 128, WATER 23, HARVEST 27, DROP 15,
  COLLECT_FERTILIZER 14, DIG 2, PASS 16, CARE 3; SELL-only market
  (WOOL/CARROT/MILK/FERTILIZER/WHEAT).
- `_V58_PIZZA_RECOVERY_ROUTE`: HARVEST 28, COLLECT_FERTILIZER 11, DROP 15,
  DIG 1, otherwise moves/WATER/PASS; market includes BUY_PRODUCT WHEAT×5.

Established consequences: (a) ZERO PLANT, ZERO BUILD, ZERO BUY_SEED, ZERO
BUY_ANIMAL, ZERO HIRE, ZERO BUY_LAND in any live route over 700–718; (b)
COLLECT_FERTILIZER (11–14 ops/route) and HARVEST (27–28) continue
in-window; (c) WATER (22–25) and CARE (3–5) also continue — H1 reap/ferry
proposals would displace them, so the H1 shadow model must cover WATER,
CARE, decay, and hunger effects (§13–§14); (d) yarn-family in-window
markets contain BUY_PRODUCT WHEAT — any transplanted SELL-only validator
fails on them (§8.2, transplant gap G2).

### §1.3 Two provable in-window no-ops

- `_v60_shed_guard` no-ops on every step 700–718: it returns immediately
  unless `hour == 23` (`:4284–4285`); engine hour is `step % 24`
  (`experiments/EXP-DEV-006_HORIZON_KILLTEST/port/kagsim_py/sim.py:335`),
  and no step in 700–718 has hour 23 (last: 695; next would be 719, which
  never executes, §4). Micro-assumption: live env hour mapping matches the
  validated port (see §22, U11).
- `_v60_seed_trim` no-ops on every step 700–718: it returns immediately
  unless the action market contains BUY_SEED STRAWBERRY (`:4128–4134`).
  Route markets contain zero BUY_SEED (§1.2), and no live mechanism ADDS
  market orders in-window except SELLs (`_preempt` adds SELLs only and is
  off ≥700, §18; `_v60_append_sale` adds SELLs only, `:4270–4280`;
  fronting/reorder preserve the order multiset, §11). Chain complete.

## §2. H1 intervention boundary (proposed; repo-grounded constraints)

H1 = a terminal overlay that, at and after a frozen entry step E
(`UNKNOWN — requires verification before protocol freeze.`, §3, decision D2),
may REPLACE the baseline action's worker commands (farmer + hands)
with a planned reap-and-ferry schedule and NOTHING else, subject to:

- B1. No market-order changes on steps E–717 (no adds, removes, quantity
  or order changes). Rationale: Dmitrii's `markets_712_717_unchanged`
  certificate (`extracted_agents/dmitrii_lb2800/terminal_planner.py:391`)
  and the fixed-markets guard (`…/policy.py:56–64`, `_fixed_market`).
  Our sparse/BUY-containing markets need a re-derived form (transplant
  gap G1, §8.2).
- B2. Step-718 market governed by ONE preregistered rule applied AFTER the
  outer `_TERMINAL_MARKET` (ordering requirement R14): either keep the
  baseline collision liquidation verbatim, or recompute on live
  state/prices à la Dmitrii `shop_liquidation`
  (`terminal_planner.py:115–118`, `terminal_action` `:463–467`).
  `UNKNOWN — requires verification before protocol freeze.` (decision D3).
- B3. Worker-command whitelist: `UNKNOWN — requires verification before protocol freeze.` (decision D1). Dmitrii's generator emits only moves,
  HARVEST, COLLECT_FERTILIZER, DROP, PASS (proposals are walk→ops→return
  +DROP, PASS-padded; `terminal_planner.py:286–294`), and the analysis
  records no PLANT/WATER/FEED/CARE/BUILD/FERTILIZE proposals
  (`experiments/EXP-ARCH-001_DMITRII_POLICY_DECOMPOSITION/TERMINAL_PLANNER_ANALYSIS.md:64–66`).
  Our window additionally contains baseline WATER/CARE/DIG (§1.2) that
  proposals would displace; whether H1 may emit DROP vs PLACE on the
  final turn, and whether COLLECT_FERTILIZER is in-whitelist (H4
  boundary, §15), must be frozen explicitly.
- B4. No writes to any cross-step state except one per-seat accepted-plan
  record created at/after E and discarded on step 0 or non-monotonic step
  (mirror of `policy.py:122–126`). No writes to controller ledgers, no
  config mutation, no checkpoint/route-registry access (R1, R6, R7).
- B5. Pure function of (obs, baseline action, frozen config, accepted-plan
  record). Deterministic: no RNG, no wallclock, no iteration-order
  dependence (R12). Dmitrii's in-window model uses no RNG
  (`TERMINAL_PLANNER_ANALYSIS.md:102–104`); the engine has no RNG in-window
  either (all RNG use is at dawn: `sim.py:754,769–774`, and no dawn falls
  in 712–718, §4).

## §3. Terminal entry point

- Baseline overlay gates: 713 (`:4476`), 717 (`:4480`), 718 (`:4484`).
  Nothing terminal-specific fires at 712 in our baseline (§1.1).
- Dmitrii entry: exactly step 712 (`policy.py:START,FINAL=712,718` at
  `:12`; planning gate `terminal_planner.py:311`).
- H1 entry step E: `UNKNOWN — requires verification before protocol freeze.` (decision D2). Constraints from evidence: (a) E ≥ 712 keeps H1 inside
  the dawn-free, shop-static, RNG-free window (§4); (b) E ≤ 716 leaves a
  multi-turn ferry horizon (recall math needs distance ≤ 718 − E); (c) any
  E must come with an entry handshake (live baseline action at E must
  equal the shadow's predicted baseline action, mirroring
  `policy.py:159–163`) because weed-repair replay tails (§12.2) and
  due-ledger carry (§18.2) make the baseline's in-window behavior
  history-dependent; (d) E = 712 maximizes comparability with Dmitrii but
  also maximizes exposure to baseline Wheat BUY orders and fronting
  feedback (§11.2).

## §4. Terminal horizon

Last agent-action step is 718 — established four independent ways:

1. Validated port: `sim.py:138` (`episode_steps=720`) + `sim.py:336–337`
   (`if step_i >= episode_steps − 2: done`) → done after 718 executes.
2. C++ mirror: `external_repos/kaggriculture-cppsim/sim/sim.hpp:142`
   (`episode_steps = 720`) + `:359` (same done rule).
3. All live routes/tapes hold exactly 719 actions: our six routes (static
   decode, §1.2) and Dmitrii's 13 tapes
   (`router_parent.py:197–198`, `LAST_STEP = 718` at `:20`).
4. Replay clamps defensively anyway: `replay_policy` indexes
   `min(max(0,step), len−1)`
   (`scratch/bundled_modules/scripts.v21_route_memory_search.py:6`).

In-window engine statics (all steps 712–718, from the port unless noted):

- No dawn: dawns complete after steps with `(step+1) % 24 == 0`
  (`sim.py:331–332`); last pre-window dawn completes 695→696; next would
  complete 719→720, which never executes. Corroborated by
  `TERMINAL_PLANNER_ANALYSIS.md:40–41`.
- Therefore, frozen for the whole window: `watered/fed/cared_today`
  flags, `consecutive_dry` counters, `pending_care_bonus`, animal/crop
  yield accrual (dawn-only: `sim.py:777–834`), `fertilizer_available`
  refresh (dawn-only, `sim.py:832`), weed spawning (dawn-only,
  `sim.py:759`), carried-inventory drops (dawn-only, `sim.py:760`), shop
  unlocks (dawn-only, `sim.py:768–775`; last unlock day 24/step 576 in any
  case), and all RNG draws (`sim.py:754,770`).
- Live dynamics in-window: unit actions → market → town_consume → decay
  (`sim.py:325–331`); shop demand ticks at steps divisible by 4 (712, 716;
  `sim.py:720–727`); NO town-center tick (24 ∤ any step in 712–718;
  `sim.py:728–731`); even-step rot of expired ongoing crops
  (`sim.py:734–751`, §13.2).
- Reward = terminal `farm["money"]` (`sim.py:316–317`); H1 cannot leak
  effects past the episode (done after 718) or into other games if its
  plan record resets on rewind (R1).

## §5. State representation

Baseline layers consume the following obs slices in-window (all read-only):

- Replay/weed-repair/reorder: `step`, `player`, `farms[seat]` (positions,
  tiles), unit counts for alignment (`v21:6`, `v22_weed_repair:47–69`,
  `v23.policy_library:54–79`).
- Residual controller: market `inventory`/`prices`, `town.unlocked_shops`,
  both farms' `money` (gap), opponent tiles (exposure), own shed +
  inventories (projection), seeds (implicitly via route), plus its own
  ledgers: `due`, `pending`, `opponent_supply`, `last_market_net`,
  `last_inventory`, `last_shops`, `near_streak/latched`,
  `mirror_confidence/evidence_turns` (`v49:369–386`, updated `:394–474,
  808–814`). Ledgers are readable at runtime (`agent.controller.states`;
  `agent.controller` exposed at `v49:830`) — the H1 shadow CAN clone
  them (relevant to R4).
- Weed-repair ledger: per-seat `active` transactions + `last_step`
  (`v22_weed_repair:34,49–63`). NOT exposed (only `.telemetry`,
  `.replay_steps`, `.stop_on_match` at `:119–121`) — the H1 shadow canNOT
  read it; handshake + stepwise re-verification is the only sound
  treatment (R10, §12.2).
- v19 overlays: positions, `private.inventories`, tiles, shed, prices,
  opponent tiles (exposure), hand counts (`scripts.v19_terminal:52–65,
  68–150, 264–308`).
- DEV schedulers add `active_plan` + `decision_events` (§19); the outer
  V54++ agent adds `_SHOP_STATE` (route/last per seat, `:4406`).

Dmitrii's shadow state for comparison: `physical_state` = own farm minus
money + private (`terminal_planner.py:40–44`); plan record holds
`baseline`/`actions`/`expected_states`/`parent_states_before`/`certificate`
(`:382–391`, `policy.py:167`). H1's exact shadow-state contents are
`UNKNOWN — requires verification before protocol freeze.` (must cover §5
baseline ledgers per R4 or abstain per R10).

## §6. Action representation

- Unit commands: `{farmer: [...], hands: [[...], …]}` with ops from the
  engine set; Dmitrii's `_validate` pins the legal op vocabulary
  (`terminal_planner.py:14–16,84–91`).
- Market: list of orders, engine-truncated to the FIRST `max_orders = 10`
  (`sim.hpp:145`, `:554`; port defaults `sim.py:139`). Order position
  matters (truncation + per-unit lockstep interleaving); any H1 step-718
  rule change is therefore a real treatment choice (D3), not bookkeeping.
- `align_hands` pads/truncates hands to the live unit count without
  remapping the validated prefix (`scripts.v19_terminal:52–65`); H1 must
  emit hand-count-aligned actions (R12-a).
- H1's exact emitted-action schema (which ops, DROP-vs-PLACE at 718,
  PASS-padding): `UNKNOWN — requires verification before protocol freeze.`
  (part of D1).

## §7. Candidate-generation mechanism

Dmitrii's generator, exactly (`terminal_planner.py:241–303`):

- Per worker, per start-offset 0–6 from the detailed baseline run: bundle
  = standing-yield HARVESTs (mature only — crops past `first_yield_day`,
  any animal yield>0; `:265–270`) + COLLECT_FERTILIZER on flagged animal
  tiles (`:271–273`), excluding cells/ops owned by another actor in the
  current best run (no-steal pre-filter, `:268,271`); keep reachable
  bundles (walk + ops + return ≤ remaining steps, `:275–276`); rank by
  value/distance (`:278`); variants = carry-only closure + top-6 singles
  + top-3×top-3 pairs (`:279–285`); each routed walk→ops→nearest-shed→
  DROP and PASS-padded (`:286–294`); 2 direct-return variants reserved
  (`:301`); ≤8/worker (`:303`, live `proposals_per_actor=8`).
- Outer loop: worker-by-worker single pass, ≤128 sims live
  (`policy.py` settings gate `:37–40`; live `(128,1,8)` per
  `SOURCE_MAP.md:27`; loop `:322–363`).

H1's candidate-generation mechanism: `UNKNOWN — requires verification before protocol freeze.` (decision D4). Repo-grounded constraints: must
exclude PLANT/BUILD/BUY/HIRE (none in baseline window, §1.2; whitelist
D1); must respect no-steal against the BASELINE's own scheduled
acquisitions (route HARVEST/COLLECT events, §1.2) AND against sibling H1
proposals; must use engine-true movement (single-step, in-bounds always
legal, `sim.py:364–371`) and reachability against remaining steps
(≤ 718 − E); compute budget must be bounded and stated (mirror R13).

## §8. Exact physical-dominance predicate

### §8.1 Dmitrii's predicate (primary source)

`dominates(candidate, baseline)` (`terminal_planner.py:209–220`): candidate
overflow == 0 AND for EVERY row: pre-market shed ⊇ baseline's (`:214`),
cumulative sold ⊇ baseline's (`:216`), per-actor cumulative deposits ⊇
baseline's (`:218`). Row-wise prefix dominance — never behind at any turn,
for any worker. Overflow = DROP-destroyed units counted during sim
(`:174–176`; engine destroys over-cap DROP units, `sim.py:375–390`).

Adoption additionally requires (all primary-sourced):

- Strictly greater stock value at frozen step-712 prices
  (`:341`, `_value` at `:223–225`: Σ(sold + final_shed) × price712).
- No-stealing: every harvest/fertilizer acquisition by OTHER actors in the
  current best must still occur (same cell, op, actor, ≥ quantity) in the
  trial (`:342–353`).
- Final acceptance conjunction (`:364–391`): changed workers non-empty +
  some actor deposited strictly more of some product + every product's
  sold delta ≥ 0 + some sold delta > 0 + final re-sim dominates + cert
  `markets_712_717_unchanged` (`:391`).

### §8.2 Transplant gaps: what a verbatim port CANNOT reuse (all blockers)

- G1. `_fixed_market` (`policy.py:56–64`) requires 712–717 parent markets
  to cover ALL 9 products with SELL ≥ 100 each. Our in-window route
  markets are sparse (often 0–3 small SELLs, sometimes EMPTY at 718;
  §1.2). Verbatim reuse ⇒ always-abstain. The H1 guard must be re-derived
  for sparse markets (R2-a).
- G2. `_validate` (`terminal_planner.py:92–99`) requires SELL-only
  markets. Yarn-family in-window route markets contain BUY_PRODUCT WHEAT
  (§1.2). Verbatim reuse ⇒ Unsupported ⇒ abstain on exactly the YARN
  games H1 most wants. The H1 validator must admit (and exactly model)
  baseline BUY orders (R2-b) or abstain on BUY-containing steps — a
  protocol decision with first-order exposure consequences.
- G3. Dmitrii's shadow replays `shadow.act` = tape + repairs + advance/
  subtract (`policy.py:98–108`). Our shadow must replay replay +
  weed-repair (unreadable ledger — handshake only, R10) + reorder +
  residual controller (`_repay` with due-carry, `_release_pending`,
  fronting reorder, `_update_flow`, step-718 `terminal_market`; R4) +
  seed-trim/shed-guard (provable no-ops in-window, §1.3) + recall/units/
  market overlays. No such shadow procedure exists in the repository.
- G4. Dmitrii's parent has no money/flow-dependent market reorder; ours
  reorders SELLs every step via fronting (`v49:784–797`), whose trigger
  reads `money_gap` and `opponent_supply` — both downstream of H1's own
  deposit changes (§11.2, §18.3). The H1 shadow must model fronting
  exactly each simulated step (deterministic — feasible) or the entry
  handshake / stepwise re-verification will abandon (safe direction:
  resume baseline, never a corrupted plan).

H1's exact dominance predicate: `UNKNOWN — requires verification before protocol freeze.` (decision D5). It must be stated as: row-wise relations +
overflow rule + value comparison (which prices?) + no-steal scope (which
baseline acquisitions?) + acceptance conjunction. §8.1 is the template;
G1–G4 are the mandatory adaptations.

## §9. Tolerances and tie-breaking

- Dmitrii: strict `score > best_value` (no epsilon;
  `terminal_planner.py:341,364`); proposal sort `(-value, offset, route)`
  (`:299`); bundle sort `(-value/distance, -value, xy)` (`:278`); winner
  keeps the LAST strictly-improving trial per worker (`:353` reassigns on
  strict improvement only); 2 direct-return variants reserved (`:301`).
  Integer-unit comparisons elsewhere (`_ge`, `:205–206`).
- H1 tolerances and tie-breaking: `UNKNOWN — requires verification before protocol freeze.` (decision D6). Must be frozen exactly (strict vs epsilon
  comparisons, sort keys, proposal caps, sim budget, price source for the
  value term) because each choice changes which candidate wins ties and
  hence the treatment's action stream.

## §10. Abstention behavior

Dmitrii abstains (parent acts) on ANY of (primary sources):

1. Settings/config pins fail (`policy.py:37–40`, `:50–54`,
   `terminal_planner.py:28–37`).
2. Parent not warm through 711 on plan 2 / day ≠ 29
   (`policy.py:70–72`).
3. Any weed-blocked op in live queues or tape2 712–718 (`:73–79`).
4. Shed invalid/overfull or unsupported shed/carried items (`:80–91`).
5. Nonfinal market not 9-product SELL≥100 (`_fixed_market`, `:102–103`).
6. Shadow/model final-action mismatch any step (`:105–106`).
7. Live-712 parent output ≠ shadow-712 output (entry handshake,
   `:159–163`).
8. Planning entry violated / sim Unsupported / budget exhausted
   (`terminal_planner.py:311–313,327–328,392–393`).
9. No strictly-positive dominating candidate (`:364–368`).
10. Final re-sim fails dominance or acceptance conjunction fails
    (`:369–381`).
11. Post-acceptance: non-consecutive callback, physical-state mismatch,
    or effective-baseline-action mismatch → abandon; salvage iff
    deviated else resume parent once and forget (`:445–470`,
    `policy.py:129–148`).

Our baseline's implicit abstention analogue: every overlay is gated and
returns its input unchanged outside its window/trigger (recall `:4361`,
units `scripts.v19_terminal:267–268`, shed-guard `:4284–4285`, seed-trim
`:4128–4134`, preempt `v49:610–615`). H1's exact abstention procedure
(guard list, handshake, stepwise re-verification, resume-baseline vs
salvage, telemetry reason codes): `UNKNOWN — requires verification before protocol freeze.` (decision D7). Required properties: abstain-by-default
(R3), resume-baseline on pre-deviation abandon (safe; cf. Dmitrii
`_resume_parent`, `policy.py:111–117`), per-seed reason-code telemetry
for the mechanism-exposure analysis.

## §11. Interaction with sales

### §11.1 Baseline in-window market mechanics (all preserved by H1)

- Route SELLs/BUYs replay (§1.2); `_repay` cuts SELLs against the due
  ledger, carrying unrepaid remainder forward while `step < 718` and
  dropping it at 718 (`v49:476–503`).
- Fronting reorder runs EVERY step with no step gate (`v49:784–797`):
  `_sort_sells_front` when latched/deficit/flow-tripped, else
  `reorder_sell_slots` — both preserve the order multiset exactly
  (`v23.policy_library:54–79`, `v22_market_impact:125–146` docstring).
  Reordering changes truncation survivors and lockstep interleave → real
  economic effect, baseline-owned.
- Step 718: controller-internal `terminal_market(replace=True)` then
  outer `terminal_market(rule="collision", replace=True)`; both sell
  every projected unit over SELLABLE (9 products incl. FERTILIZER),
  ordered by collision score
  `(1+exposure)×GLUT_WEIGHT×price×log1p(qty)`
  (`scripts.v19_terminal:190–239`); BUY orders wiped. ≤9 SELLs ⇒ the
  10-order cap cannot bite a pure terminal market, but ORDER still
  matters for lockstep interleaving (§6).

### §11.2 Feedback paths H1 must model (not block)

- H1 unit-op changes → different DROP/PLACE deposits → different shed
  stock → route SELLs execute different quantities
  (`min(requested, stock)`; `terminal_planner.py:191–195` models it;
  engine lockstep `sim.hpp:551ff`) → different revenue → `money_gap`
  moves → fronting trigger (`v49:784–788`) may flip at t+1 → different
  SELL order → different sales. Intended causal channel; the shadow must
  model fronting exactly (R4) or handshake/re-verification abandons
  (safe).
- Same-deposit sensitivity via `_executable_market_net` (clips own SELLs
  to projected shed; `v49:150–185`) → `last_market_net` → next-step
  `opponent_supply` inference (`v49:394–474`) → fronting/preempt triggers.
  Deterministic and modelable (R4); preempt itself is off ≥700 (§18.1).
- Shared-price residual: solo-execution modeling cannot predict
  opponent-driven price moves. Confined to the VALUE comparison, never to
  physical legality, exactly as Dmitrii documents
  (`TERMINAL_PLANNER_ANALYSIS.md:128–135`): dominance is certified in
  units. H1 must adopt the same confinement explicitly (R5).

H1 market-touching permissions: none on E–717 (B1); step-718 rule per D3/B2.

## §12. Worker movement

### §12.1 Baseline recall mechanics (preserved; H1 supplants within its plan)

- `_route_loaded_units` (713–716): reroute iff `distance == 718 − step`
  (`:4384`) via `_move_toward` (greedy axis step toward nearest shed
  access, in-bounds non-LOCKED only, else PASS;
  `scripts.v19_terminal:242–261`). Shed access = 4 central tiles
  (`:42–49`, board/2 based; engine `is_shed_adjacent` equivalent,
  `sim.py:375–377`).
- `monetizable_terminal_units` (717–718): DROP on access; 717-only
  distance-1 approach and on-access HARVEST (`scripts.v19_terminal:291–302`).
- Engine moves: single-step, in-bounds always legal, no collision model
  (`sim.py:364–371`; corroborated
  `TERMINAL_PLANNER_ANALYSIS.md:70–72`). H1 walk modeling is therefore
  exact Manhattan routing (Dmitrii `_walk` x-first, `_return` to nearest
  access + DROP; `terminal_planner.py:228–238`).

### §12.2 Weed repair in-window (read carefully — handshake driver)

`wrap_weed_repair` runs inside the base policy on EVERY step including
712–718 (`v23.planner:29–33`). Trigger: route op BUILD_PASTURE/PLANT
(note: BUILD_COOP not covered, unlike Dmitrii's
`WEED_BLOCKED_WORK={"PLANT","BUILD_COOP","BUILD_PASTURE"}`,
`router_parent.py:27`) issued while standing on a WEED tile
(`v22_weed_repair:95–113`). Response: DIG now, retry intended at age 1,
replay that actor's previous route actions for 8 steps
(`:72–93`, `replay_steps=8`); market and other actors untouched (`:30–31`
docstring). Route decode (§1.2) shows no PLANT/BUILD in-window, so no
transaction can START in-window under the baseline — but a transaction
started as late as step 710 is still replaying route actions into
712–718 (ages 2–9). Its ledger is unreadable (§5) ⇒ the H1 entry
handshake + stepwise re-verification (R10) is the only sound treatment;
any divergence abandons to baseline (safe). If H1's whitelist (D1)
excludes PLANT/BUILD (as Dmitrii's does), H1's own proposals can never
start a repair transaction either.

## §13. Harvest and crop state

- Baseline in-window: HARVEST 27–28 ops/route, WATER 22–25/route (§1.2).
  H1 reap proposals displace WATER/CARE turns — legal but must be
  dominance-checked, because: (a) WATER raises single-harvest yield
  inside the age window (`sim.py:447–458`; ongoing crops unaffected);
  (b) rot proceeds on even steps for expired ongoing crops
  (`sim.py:734–751`: even `step_i`, `(step − max_lifespan_step)` even ⇒
  −1 yield, →WEED at 0); (c) HARVEST requires maturity
  (`day − planted_day ≥ first_yield_day`; `sim.py:459–467`,
  `unit_model.py:239–247`) and empties single-harvest tiles.
- No yield accrues in-window (dawn-only, §4): H1 candidates can only reap
  STANDING yield + fertilizer, exactly Dmitrii's bundle design (§7).
- H1 shadow must model WATER/rot/maturity exactly (engine-exact
  `unit_model.py` exists and is SHA-pinned per `SOURCE_MAP.md:7–12`,
  but H1's sim choice is a protocol decision, part of D4/R4).

## §14. Animals, feed, and care

- Route decode: ZERO FEED ops in any live route over 700–718 (§1.2);
  CARE 3–5 ops/route. `fed_today/cared_today` are frozen all window (no
  dawn, §4); hunger/yield/fertilizer ticks are dawn-only (`sim.py:809–834`).
  Consequence: animals neither starve further nor yield further in-window
  regardless of H1 — EXCEPT H1 displacing a baseline CARE is value-free
  in-window (care bonus pays at dawn, `sim.py:830–831`, and no dawn
  remains) while displacing a HARVEST of standing animal yield is
  value-negative unless the proposal reaps it elsewhere. Both are
  dominance-checkable; the shadow must implement animal HARVEST + yield
  semantics exactly (R4).
- H1 must not emit FEED/CARE (Dmitrii excludes both; whitelist D1):
  in-window they cannot pay (no dawn remains) and would only burn ferry
  turns. Feed reserve protection (v49 wheat gating, `:639–647`) is
  preempt-path code, inactive ≥700 (§18.1); WHEAT sales in-window come
  from route SELLs + 718 liquidation only.

## §15. Fertilizer

- FERTILIZER is a first-class terminal product on BOTH sides: baseline
  SELLABLE includes it (`scripts.v19_terminal:14–17`); routes COLLECT it
  11–14× in-window (§1.2); `_v60_project_units` models COLLECT (+1,
  `:4240–4241`) and FERTILIZE (−1, `:4245–4247`); shed-guard's day≥29
  branch adds FERTILIZER+WHEAT sale candidates (`:4306–4310`, though the
  guard itself is hour-gated off in-window, §1.3); 718 liquidation sells
  it (`scripts.v19_terminal:203–224`). Dmitrii likewise reaps flagged
  fertilizer (`terminal_planner.py:271–273`) and sells it most
  frequently (TRANSFERABILITY item 12). Correction of a possible
  misreading: the ARCH-001 note "no FERTILIZER reference in dev_004"
  concerns the DEV PLANNING MODEL's valuation code, not the executed
  routes — V54++ demonstrably collects and liquidates fertilizer.
- No FERTILIZE ops in-window in any route (§1.2); day-29 fertilizing
  cannot pay (3-day window, game ends;
  `TERMINAL_PLANNER_ANALYSIS.md:64–66`). H1 whitelist must exclude
  FERTILIZE (D1).
- H4 boundary (R8): H1 may reap fertilizer ALREADY flagged available at
  E (flags set at the last dawn, step 696; no refresh in-window, §4) as
  part of terminal reaping — Dmitrii does exactly this. H1 must NOT
  change collection policy pre-window, add drip-sell markets, or value
  fertilizer beyond the frozen terminal price vector. The protocol must
  state COLLECT_FERTILIZER's whitelist status explicitly (D1); either
  choice is isolatable, ambiguity is not.

## §16. Deposits

- Engine order per turn: unit actions (incl. DROP/PLACE deposits) execute
  BEFORE the market (`sim.py:325–327`; corroborated by v19's
  `projected_shed` docstring, `scripts.v19_terminal:69`). Same-turn
  DROP→SELL is therefore legal and is the mechanism of both baselines'
  718 liquidation and any H1 ferry gain.
- DROP at shed access deposits whole inventory up to room; EXCESS IS
  DESTROYED (`sim.py:375–390`, `f.discarded[it] += …`). PLACE deposits
  min(requested, carried, room) and is non-destructive (`sim.py:403–428`;
  animal-PLACE on COOP/PASTURE excluded from deposit modeling,
  `:406–417`). This asymmetry is WHY Dmitrii counts overflow as
  dominance failure (`terminal_planner.py:174–176,211`) and why its
  recovery PLACEs the dearest fitting product when DROP would discard
  (`:422–429`). H1's dominance rule must take a position on DROP
  overflow (part of D5); mirroring Dmitrii (overflow ⇒ fail) is the
  conservative, repo-grounded choice.
- Two deposit projectors exist in our stack: v19's `projected_shed`
  (DROP/PLACE only, `:68–128`) and v24's `_project_private_after_actor`
  (adds PICKUP + FEED wheat burn, deliberately no harvest credit;
  `scratch/bundled_modules/v24.market_maker.py:220–232` docstring). H1's
  shadow must use (or beat the conservatism of) the engine-exact
  semantics, not either approximation, wherever dominance is certified
  (R4).

## §17. Inventory

- Shed capacity 100 enforced by truncation-on-deposit (DROP destroys
  excess, §16) and sale clipping (`min(requested, stock)`). Shed validity
  (non-negative ints, total ≤ 100) is a Dmitrii entry guard
  (`policy.py:81–82`); H1 needs the same guard (R2-a).
- Carried inventories persist across in-window turns (no dawn drop,
  §4) and are the ferry payload. Dmitrii requires supported carried
  stock + shape `inventories == n ≤ 32` (`policy.py:89–91`,
  `terminal_planner.py:132–134`); H1 needs equivalent shape guards (R2-a).
- `private.seeds` is irrelevant in-window (no PLANT/BUY_SEED, §1.2) but
  H1's validator should still reject unknown unit items explicitly
  (mirror `terminal_planner.py:87–91`).

## §18. Interaction with existing residual market preemption

### §18.1 Preemption itself is structurally OFF in-window (proof)

`_preempt` returns its input unless `active_start ≤ step < active_stop`
(`v49:610–615`). Defaults are 72/700 (`v49:36–37`); the frozen
`_V54_CONFIG` (`:1976`) and `_CONFIG_DICT` overrides (`:4395–4399`) set
neither key; the live residual config is therefore
`preempt_money_deficit=2000.0 / preempt_minimum_delta=4.0 /
preempt_maximum_batch=12 / preempt_horizon=2 / front_money_deficit=4500.0 /
front_on_near=True` on steps 72–699 ONLY. No SELL is ever fronted into,
out of, or within 700–718 by this mechanism. H2-style sale-timing
changes are therefore impossible through the preemption path in-window —
but also: H1 must NOT reintroduce any advance/subtract logic of its own
(R3; H2 contamination check in §21, T8).

### §18.2 What REMAINS active in-window (must be modeled or abstained-on)

- `_repay` (`v49:476–503`): cuts route SELLs against the due ledger every
  step; unrepaid remainder carries to step+1 while `step < 718` and is
  dropped at 718. A due created by the last legal preempt (step 699,
  horizon 2 → dues at 700–701) can in principle propagate day-by-day to
  717 if route SELLs stay insufficient. The due ledger is readable
  (`agent.controller.states[seat]["due"]`) ⇒ modelable (R4).
- Fronting reorder every step, trigger reads `near_latched`,
  `money_gap`, `opponent_supply` (`v49:784–797`; §11.2). Modelable (R4).
- `_update_flow` every step (`v49:750` + `:394–474`): updates
  `opponent_supply`, `mirror_confidence`, `last_market_net`,
  `last_inventory`, `last_shops`. Market-effect-free EXCEPT through the
  §18.3 feedback paths. Modelable (R4).
- `_release_pending`: live code but `pending` is always empty because
  `_defer` is disabled (`v49:505–508` gate + `:542–548`); returns input.
  (Defense in depth: the H1 validator should still assert empty pending
  at entry — cheap, mirrors the unsupported-item guards.)

### §18.3 Feedback: H1's unit ops perturb controller market state next turn

Two deterministic paths (both modelable, neither blocks isolation):

1. Deposits → shed stock → SELL execution quantities → revenue →
   `money_gap` → fronting trigger flip at t+1 (§11.2).
2. Deposits → projected shed → `_executable_market_net` clipping
   (`v49:150–185`) → `last_market_net` → next-step `opponent_supply`
   inference (`v49:407–418`) → fronting trigger.

The shadow must implement these transitions exactly (all pure functions
of obs + action + cloned ledgers, R4). Any residual misprediction is
caught by the entry handshake / stepwise re-verification and abandons to
baseline (safe direction, §10 item 11 analogue). Worst case of chronic
mismatch is always-abstain (mechanism untestable, cf. DEV-007 pattern C),
never a corrupted plan — EXPLICITLY: isolation holds even if activation
fails; activation rate is an empirical telemetry question, not an
isolation blocker.

### §18.4 Untouched-by-H1 requirements

H1 must not mutate `ResidualConfig`, controller ledgers, telemetry, or
the route prior; must not call `build_residual_controller` or construct
policies (R6). H1 reads the BASELINE's emitted action and obs only.

## §19. Interaction with DEV-005 confirmed-shop gating

- DEV-004/005/006 share: checkpoints at exactly {72,144,216,288}
  (`dev_004:365`, `dev_005:348–349`, `dev_006:375–376`); 6-plan registry
  built once at init from baseline routes + baseline `_CONFIG`
  (`dev_004:132–142`, `dev_005:110–119`, `dev_006:119–128`); identical
  terminal overlay chain to the outer baseline (`dev_004:374–383`,
  `dev_005:355–364`, `dev_006:382–391`); gate
  `best_delta ≥ TAU(1500) ∧ money ≥ L_MIN(100)` (`dev_004:321`);
  DEV-005 adds `ROUTE_REQUIRED_SHOPS` confirmation (`dev_005:41–48`,
  gate `:297–308`, decisions `SPECIALIZE_CONFIRMED/REJECT_UNCONFIRMED/
  BASELINE`); DEV-006 adds the horizon guard (`dev_006:309–326`).
- `active_plan`/`active_policy` are STATIC over 712–718 (no checkpoint in
  or after the window; last checkpoint 288). Checkpoints cannot observe
  H1 (H1 acts ≥ E ≥ 712; checkpoint telemetry at ≤288 predates it).
  H1 must not import, call, or reference any checkpoint/valuation/
  registry symbol (R7); H1 operates strictly downstream of
  `active_policy(obs, visible)` + overlays.
- ARCH-002 baseline choice (V54++ vs DEV-005 vs DEV-006): `UNKNOWN — requires verification before protocol freeze.` (decision D8). Isolation
  holds under any of the three (all static in-window with identical
  overlay chains), but the shadow procedure differs (DEV holds 6 live
  controller states vs V54++'s 3; DEV passes `configuration=None`, see
  below). The protocol must name exactly one.
- None-configuration consequence (existing DEV property, H1 must
  preserve): DEV `act()` calls `active_policy(obs, None)`
  (`dev_005:351–353`) because its signature takes no configuration,
  while the outer baseline passes seed-stripped live config
  (`:4452`). With `None`, `regime_from_configuration` defaults to
  legacy (`v23.state_encoder:51–53`: interval default 12 < 24), so DEV
  policies sort SELL slots with `demand_alpha=0.0` (`v23.planner:49–58`)
  and `_demand_at` uses default intervals (`v49:203–205`: 4/24). H1's
  shadow must replay the baseline call with the SAME configuration the
  baseline used (R11) — i.e. `None` under a DEV baseline, `visible` under
  V54++. (Whether live Kaggle config yields rebalance is immaterial to
  isolation; what matters is shadow/live agreement.)

## §20. Whether H=500 exists in the baseline

H=500 exists ONLY in `dev_006` (`HORIZON_GUARD_THRESHOLD = 500`,
`dev_006:21–23`; enforcement `:309–326`; telemetry `:340–356`). Static
grep (case-insensitive `horizon`) over the other two sources finds only:
`preempt_horizon: 2` config keys (`:1805`, `:1976` — a 2-turn preemption
lookahead, unrelated) and one comment (`dev_004:196`). It is absent from
`compiled_v54_plus_residual.py` as a mechanism, absent from `dev_004`,
absent from `dev_005`, and — structurally — evaluated only at checkpoints
≤288. H1 (window ≥712) cannot interact with it except by deliberately
importing checkpoint code, which R7 forbids. Test F (no H=500
contamination) is satisfiable by construction: the H1 implementation must
contain zero references to `HORIZON_GUARD_THRESHOLD`, `REJECT_HORIZON`,
`remaining_horizon`, or the DEV checkpoint functions, verifiable by grep
at protocol-freeze review.

## §21. ADVERSARIAL SECTION — Could H1 accidentally be more than H1?

Each pathway below was traced end-to-end through the cited sources in an
attempt to falsify isolation. Verdicts: BLOCKED (source fact closes it),
CLOSED-BY-REQUIREMENT (protocol must freeze the cited R), or OPEN (would
force FAIL — none found).

- T1. H1 alters pre-window actions. BLOCKED. H1 is gated to steps ≥ E ≥
  712 (B5/R3); turns < E are already emitted (causality). The only
  cross-step writes permitted are the post-E plan record (R1). Pre-E
  controller/weed/shop state is read-only input H1 must not mutate (R6).
- T2. H1 alters macro route selection. BLOCKED. Outer `_select_route`
  reads only `shops[0:2]` (`:4409–4430`), fixed since step 144 (unlocks
  end day 24/step 576; `EVD-02`, `sim.py:768–775`); it is re-evaluated
  every step but its inputs are constant over 712–718. DEV
  `active_plan` changes only at checkpoints ≤288 (§19). H1 has no path
  to either (§19/R7).
- T3. H1 alters shop/town state. BLOCKED. Unlocks are engine-RNG at dawn
  (`sim.py:768–775`); no dawn in-window (§4); agent has no shop-facing
  action. Nothing H1 emits can change `unlocked_shops`.
- T4. H1 alters crop/animal strategy (plant/buy/hire). BLOCKED given D1.
  No PLANT/BUILD/BUY/HIRE exists in baseline window routes (§1.2); the
  whitelist (D1, mirroring Dmitrii's reap-only emission, §7) excludes
  them; validator must reject them (R2-a). Residual risk: NONE once D1
  frozen — verifier greps the whitelist + validator.
- T5. H1 alters worker schedules outside the window. BLOCKED (same
  argument as T1; per-step action function, no retroactive writes).
- T6. H1 alters 712–717 sale timing/quantities (H2 contamination).
  CLOSED-BY-REQUIREMENT (B1/R3): H1 must emit baseline markets verbatim
  on E–717. Indirect perturbation via deposits→fronting is baseline-owned
  mechanics the shadow models (R4/G4); the dominance certificate
  (`markets_712_717_unchanged` analogue, D5) polices it. Direct
  advance/subtract code is forbidden by R3 (grep-verifiable).
- T7. H1 alters the step-718 market rule silently. CLOSED-BY-REQUIREMENT
  (D3/B2/R14): exactly one frozen rule, applied after the outer
  `terminal_market`, or verbatim baseline passthrough. ORDER matters
  (§6) so the choice is treatment, not plumbing — but in-window
  treatment is H1's definition, not contamination.
- T8. H1 reintroduces preemption/advance logic (H2 via repay confusion).
  BLOCKED given R3+R6. `_repay` cutting SELLs is BASELINE behavior H1
  preserves, not H1 behavior; H1 adds no SELLs and shifts no sale timing
  (B1). Distinguish in telemetry: repay-driven SELL cuts (baseline) vs
  H1-driven unit changes (treatment).
- T9. H1 becomes a fertilizer program (H4 contamination). CLOSED-BY-
  REQUIREMENT (R8/D1): in-window reaping of already-flagged fertilizer
  is inside H1's definition (Dmitrii does it, §15); collection-policy
  changes, drip-sell markets, or out-of-window valuation are outside.
  The protocol must state COLLECT's whitelist status (D1).
- T10. H1 changes checkpoint routing (H5 contamination). BLOCKED given
  R7: no checkpoint code reachable from the H1 call site (downstream of
  `active_policy` + overlays); checkpoints ≤288 cannot observe H1.
- T11. H1 inherits/tunes H=500. BLOCKED given R7 + §20 (grep-verifiable
  absence; mechanism lives only in dev_006 checkpoints ≤288).
- T12. H1 perturbs residual-controller ledgers directly. BLOCKED given
  R6 (no ledger writes; read-only clone for shadow, R4). Indirect
  perturbation via deposits is modeled (§18.3) or abandons safely.
- T13. Weed-repair replay tail corrupts the H1 plan mid-window.
  CLOSED-BY-REQUIREMENT (R10): unreadable ledger ⇒ handshake at E +
  stepwise re-verification each step + abandon-to-baseline on ANY unit-
  op divergence between live baseline and shadow baseline (Dmitrii's
  exact pattern, §10 item 11). Pre-deviation abandonment resumes the
  baseline action for that step — zero treatment effect on abandonment
  steps, by construction.
- T14. Due-ledger carry reaches the window and H1 ignores it.
  CLOSED-BY-REQUIREMENT (R4): dues are readable and the repay/carry rule
  is deterministic (`v49:476–503`); shadow must implement it. (Alternative
  the protocol MAY choose: abstain unless `due` empty at E — simpler,
  costs exposure on due-carrying seeds. Either is isolatable; D7.)
- T15. H1's 718 DROP overflows the shed, destroying baseline cargo.
  CLOSED-BY-REQUIREMENT (D5/R4): overflow must fail dominance (mirror
  Dmitrii) or be PLACE-routed with proof; the engine destroys over-cap
  DROP units (§16), so an unmodeled DROP is the single most dangerous H1
  primitive. Validator + dominance sim must both cover it.
- T16. H1 plan record leaks across games/seats/rewinds. BLOCKED given R1
  (per-seat record, created ≥ E, discarded on step 0 / non-monotonic
  step — mirror `policy.py:122–126`).
- T17. H1 is nondeterministic (RNG/wallclock/order-dependence).
  BLOCKED given R12 (B5). No in-window RNG exists anywhere (§4/B5).
- T18. H1 exceeds compute budget and times out the turn. CLOSED-BY-
  REQUIREMENT (R13): frozen sim/proposal caps (mirror Dmitrii's
  (128,1,8) + `planning_ms` telemetry, `SOURCE_MAP.md:27`,
  `terminal_planner.py:394`). Latency is a deployment gate, not an
  isolation falsifier — but an unbounded H1 cannot be preregistered.

Falsification result: no OPEN pathway. Every route from H1 to out-of-
window or out-of-definition effects is either structurally absent from
the repository's code or closable by a numbered, freezeable, review-
verifiable requirement. The closest calls are T6/T12/T13/T14 (all
require the shadow to be exactly faithful) and T15 (DROP overflow);
each has a safe-direction failure mode (abandon → baseline).

## §22. UNKNOWN register (protocol decisions + verification gaps)

Every item in this register: `UNKNOWN — requires verification before protocol freeze.`
Each item's home section carries the same label with repo-grounded option sets.

Decisions the protocol must freeze (each has repo-grounded options above):

- D1. Worker-command whitelist + emitted-action schema (§2/B3, §6, §7).
- D2. Entry step E (§3).
- D3. Step-718 market rule: verbatim baseline vs live recompute (§2/B2).
- D4. Candidate-generation mechanism + sim choice + budget (§7, R13).
- D5. Dominance predicate + acceptance conjunction (§8, incl. G1–G4).
- D6. Tolerances and tie-breaking (§9).
- D7. Abstention procedure + reason codes (+ optional abstain-if-dues,
  T14) (§10).
- D8. ARCH-002 baseline identity: V54++ vs DEV-005 vs DEV-006 (§19).

Verification gaps (not decisions; must be closed before/at freeze):

- U9. Shadow-procedure exactness (G3/R4): no shadow of OUR stack exists;
  the protocol must attach the shadow algorithm + a parity proof method
  (e.g. shadow-vs-live baseline agreement gate on consumed cohorts —
  NOT on the future experimental cohort, NOT on the holdout).
- U10. Activation-rate prior: unknown how often the handshake + guards
  pass on our sparse-market routes. Empirical; measured by the
  experiment's exposure telemetry (D7 reason codes), not knowable from
  static analysis. Affects power, not isolation.
- U11. Live-env parity micro-assumption: engine hour mapping, 718-last
  semantics, and config intervals corroborated by port + cppsim + Dmitrii
  + routes (§4), but live-Kaggle receipt is unverified as a standing
  program caveat (cf. `DEVELOPMENT_EVIDENCE_LEDGER.md` EVD-14 limits).

## §23. Protocol requirements register (freeze all 14 with the protocol)

- R1. Per-seat plan record only; created ≥ E; discarded on step 0 or
  non-monotonic step (§2/B4, T16).
- R2-a. Entry validator: shed validity (≤100, non-neg ints), supported
  items, inventory shape, no PLANT/BUILD in baseline window slice,
  empty pending, config pins (mirror §10 items 1–4; adapted per G1).
- R2-b. Market admissibility: validator admits baseline BUY orders and
  models them exactly, or abstains on BUY-containing steps (G2; state
  which — exposure-critical).
- R3. Abstain-by-default; no market touches E–717 (B1); no
  advance/subtract/preemption/defer/market-maker code (T6/T8).
- R4. Shadow fidelity: exact replay of reorder + `_repay`/carry +
  fronting + `_update_flow` + overlays with cloned readable ledgers and
  engine-exact unit/decay/deposit/sale semantics; same `configuration`
  object the baseline call used (R11).
- R5. Unit-dominance confinement: shared-price residual confined to the
  value term; legality certified in units only (§11.2).
- R6. No writes to configs, ledgers, telemetry, route priors; no policy
  construction (§18.4).
- R7. No checkpoint/valuation/registry/H500 references (grep-verifiable)
  (§19, §20, T10/T11).
- R8. Fertilizer boundary: reap-only-flagged-at-E; no collection-policy
  or drip-sell changes (§15, T9).
- R9. (Folded into D3/D5 at freeze; reserved.) Step-718 rule + dominance
  overflow position stated as one conjunction.
- R10. Entry handshake + stepwise re-verification + abandon-to-baseline
  (T13; mirror §10 item 11).
- R11. Shadow/live configuration identity (None under DEV, visible under
  V54++) (§19).
- R12. Determinism + hand alignment (B5, §6). R12-a: `align_hands`-
  compatible emission.
- R13. Bounded compute: frozen sim/proposal caps + `planning_ms`
  telemetry (T18).
- R14. Overlay ordering: H1 unit overlay applies downstream of
  `_TERMINAL_UNITS`; any H1 718 market rule applies downstream of the
  outer `_TERMINAL_MARKET` (§1.1 pipeline; T7).

## §24. Verdict

`ISOLATION PASS — suitable for ARCH-002 preregistration`

Meaning, precisely: (1) the repository establishes the baseline's
terminal behavior exactly (§1, §4–§6, §11–§20); (2) all 20 audit items
are either established with line-level citations or converted into
numbered protocol decisions (D1–D8) and verification gaps (U9–U11) with
repo-grounded option sets; (3) the adversarial trace (§21, T1–T18) finds
no structural contamination pathway and no unclosable ambiguity — every
threat is BLOCKED by source fact or CLOSED-BY-REQUIREMENT (§23, R1–R14),
each requirement review-verifiable (several by static grep); (4) all
failure modes fail safe (abandon → emit the baseline action), so the
worst case of modeling error is non-activation (cf. DEV-007 pattern C),
never a corrupted treatment.

What PASS does not claim: that H1 will activate at any particular rate
(U10), gain money, reduce tails, or move Elo; that any H1 design choice
(D1–D8) is made (deliberately not — protocol work); or that the ARCH-002
baseline (D8) is selected. The next artifact is the preregistration
protocol, which must freeze D1–D8 + R1–R14 + seed range + analysis plan
before any implementation or execution.

## Appendix A — files inspected (all read in full unless noted)

Baseline stack: `candidates/compiled_v54_plus_residual.py` (targeted:
`:1637–1645,1801–1805,1976,2292–2299,3648–3656,3887–3924,4053–4125,
4126–4349,4340–4491` + full-function greps); `candidates/v54_plus_macro.py`,
`candidates/v54_plus_residual.py`, `candidates/v54_plus_shop.py` (full);
`scratch/bundled_modules/scripts.v19_terminal.py` (full),
`v49.residual_controller.py` (full), `v50.hybrid.py` (full),
`v23.policy_library.py` (full); embedded dumps of `v21/v22/v23/v24/v44/
v48/v50.suffix` (full, byte-compared to repo copies, §0);
`forensic_verification/extracted_sources/v49_modules/
v49_residual_controller.py` (hash-compared);
`research/compiled_semantic_equivalence.md` (full).
DEV: `candidates/closed_loop_architecture/dev_004_joint_macro_scheduler.py`,
`dev_005_confirmed_shop_scheduler.py`, `dev_006_horizon_guard_scheduler.py`
(all full). Dmitrii: `extracted_agents/dmitrii_lb2800/terminal_planner.py`,
`policy.py`, `router_parent.py` (all full); `unit_model.py` (grep +
targeted semantics); ARCH-001 `TERMINAL_PLANNER_ANALYSIS.md`,
`REACTIVE_OVERLAY_ANALYSIS.md`, `SOURCE_MAP.md`, `SHOP_ROUTER_ANALYSIS.md`
(partial, router counts), `TRANSFERABILITY_MATRIX.md` (items 7, 12),
`HYPOTHESES.md` (H1–H8), `README.md` (boundary record). Engine:
`experiments/EXP-DEV-006_HORIZON_KILLTEST/port/kagsim_py/sim.py`
(targeted: `:138–152,316–337,364–390,403–473,720–834`);
`external_repos/kaggriculture-cppsim/sim/sim.hpp` (targeted:
`:142,145,264,359,554`); `env_backup_1_30_1/kaggriculture.py` (grep only;
1.30.1, non-authoritative per `SOURCE_MAP.md:7–12`).

## Appendix B — static verification methods (reproducible, no execution)

1. Recursive bundle unwrap: `_V51_BASE_SOURCE` → `_V50_BASE_SOURCE` →
   `_V50_MODULES`/`_V49_MODULES` JSON dicts (15 modules); SHA-256 compared
   modulo line endings against `scratch/bundled_modules/` — 15/15 match
   (§0). Working probes in session temp space (not repo artifacts).
2. Route decode: `json.loads(zlib…)` blobs for the 6 live routes; op/market
   census over steps 700–718 (§1.2); all lengths 719.
3. Dead-code grep: `terminal_liquidation|plan_sell_quantities` (0 callers);
   `v44|v48|suffix_router` importers (0 in live path); `horizon`
   case-insensitive (§20); `_V58_STATES` writers (`:3626` init + `:3794`
   dead-path only).
