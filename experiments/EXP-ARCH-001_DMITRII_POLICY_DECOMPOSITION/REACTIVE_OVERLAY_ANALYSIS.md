# REACTIVE OVERLAY ANALYSIS

Code: `router_parent.py` `repair_weeds`, `advance_sales`,
`subtract_advanced_sales`, `projected_shed`, `liquidate`;
`terminal_planner.terminal_action` / `_recover_observed`;
`policy._resume_parent`.

## 1. repair_weeds

- Exact trigger: per worker, each turn: the head of that worker's
  same-day queue is PLANT/BUILD_COOP/BUILD_PASTURE AND the tile the
  worker currently stands on is WEED.
- Exact modification: emit DIG for that worker this turn; the blocked
  command STAYS queued (head preserved); all other workers pop and
  emit normally. Current-day queue persists across turns; cleared at
  dawn (day change) — "unfinished work never spills into tomorrow".
- Safety condition: none beyond the trigger (DIG on WEED always
  succeeds: DIG clears any non-animal dict tile; no-op otherwise).
- Baseline guarantee preserved: macro op SEQUENCE per worker (the
  queue only inserts DIGs and delays, never drops or reorders within
  the day). Note: it does NOT preserve TIMING — a weed-blocked worker
  slips all subsequent same-day commands by the DIG turns.
- Possible downside: (a) dawn wipe can strand a worker's remaining
  queue (lost work, including HARVESTs that rot); (b) worker slip
  desynchronizes multi-worker rendezvous the tape assumed (e.g. a
  PICKUP/PASS chain); (c) DIG on a tile the tape expected EMPTY
  destroys nothing but costs the turn; on a tile holding a CROP the
  trigger cannot fire (crop tiles aren't WEED) — safe.

## 2. advance_sales

- Exact trigger: a next-step tape SELL (any product except WHEAT/
  FERTILIZER, not already selling this turn, projected shed covers
  it, public price >= 2), AND next<=718 AND next%72!=0 AND step%4!=0
  AND market has a free slot (<10 orders).
- Exact modification: append `SELL item qty` (qty = min(projected
  stock, planned next qty)) to THIS turn's market; record
  `advanced_sales[item]=qty`, `sale_due_step=next`.
- Safety condition: price floor (>=2 avoids dumping into a crashed
  market one turn early... note it uses CURRENT price, not next);
  slot cap; WHEAT/FERTILIZER excluded (feed and fertilizer-input
  protection — never accelerate what the farm consumes); unlock-step
  exclusion (demand regime changes at unlocks); 4-step exclusion
  (shop/center consumption ticks refresh prices every 4 steps —
  selling INTO the tick rather than before it).
- Baseline guarantee preserved: total SOLD per product per 2-turn
  window is unchanged in expectation (see subtract); only TIMING
  moves (one turn earlier). Shed-capacity pressure is relieved, not
  added.
- Possible downside: (a) selling at today's price vs tomorrow's is a
  bet — systematically wrong if prices trend up into the tape's sale
  turn (e.g. shop demand ticks); (b) consumes order slots (10 cap)
  that the tape's own orders may need — mitigated by truncation
  order (tape orders first, advanced appended, truncate keeps tape's...
  actually truncate keeps FIRST 10, so ADVANCED orders are the ones
  dropped on overflow — safe direction); (c) interacts with the
  terminal dominance proof: markets 712..717 must equal baseline
  exactly at runtime — advance into 712..716 from 711..715 WOULD
  break `markets_712_717_unchanged`... EXCEPT the shadow guard
  `_fixed_market` + `terminal_action` mismatch detection treat any
  deviation as abandonment. Hmm — precisely: `advance_sales` runs
  inside `parent.act`, so it also shapes the BASELINE the planner
  compares against (`plan['baseline']` was built by `shadow.act`
  which includes advance/subtract). Both sides include it; the
  mismatch detector compares parent-live vs parent-shadow effective
  actions, so consistent advance behavior cancels out. Safe by
  construction, as long as shadow and live see the same obs (they do
  until deviation).

## 3. subtract_advanced_sales

- Exact trigger: `state.sale_due_step == step` (exactly one turn
  after an advance).
- Exact modification: for each SELL order, decrement qty by the
  matching advanced amount (floored at 0 — CAN produce `SELL x 0`,
  inert in the engine); then clear `advanced_sales`/`sale_due_step`
  unconditionally.
- Safety condition: `min(order_qty, remaining)` — never negative.
- Baseline guarantee preserved: no double-selling; the 2-turn total
  per product is conserved.
- Possible downside: `x0` orders consume market slots (10 cap) for
  one turn; evidence suggests the TAPES themselves contain such
  leftovers (generation artifact — tapes passed through this logic).

## 4. Recovery / callback handling (terminal)

- `_resume_parent` (pre-deviation abandon): restore the EXACT
  pre-callback logical parent state for this step index, run parent
  once, forget the plan. Safe because no physical deviation has
  occurred — live and shadow coincide.
- `_recover_observed` (post-deviation): abandon positional commands
  forever; per loaded worker, walk the shortest path to the nearest
  shed tile and DROP (or PLACE the dearest fitting product if DROP
  would overflow-discard); keep parent's market (recompute at 718
  from actual stock). Bounded, state-free, never resumes the plan.
- Trigger: any physical-state or effective-baseline mismatch, or
  non-consecutive callback.
- Guarantee preserved: NO guarantee of matching baseline value —
  recovery explicitly sacrifices the plan to salvage carried cargo.
  The guarantee is instead: never issue a command predicated on a
  false position/inventory belief.

## 5. General pattern?

YES — all three overlays instantiate one pattern: **preserve the
macro route's WHAT/ORDER while repairing the WHEN/WHERE against live
state**. Weeds: same ops, shifted turns. Sales: same quantities,
shifted one turn earlier. Terminal: same markets 712–717, re-routed
workers; on surprise, same markets, position-free salvage. None of
them re-plans the economy; all of them absorb local physical
violations the open-loop tape cannot see. The pattern's price is
timing slip (weeds), price bets (sales), and total plan forfeit
(terminal recovery) — each bounded: one day, one turn, carried cargo.
