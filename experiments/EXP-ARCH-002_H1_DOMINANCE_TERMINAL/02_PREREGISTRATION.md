# EXP-ARCH-002 H1 — PREREGISTRATION PROTOCOL

**Experiment**: `EXP-ARCH-002_H1_DOMINANCE_TERMINAL`
**Document**: `02_PREREGISTRATION.md`
**Date**: 2026-09-15
**Status**: PROPOSED PREREGISTRATION (this turn) — implementation, runner,
execution, and freeze commit are all future work gated by §24.
**Authority**: `01_ISOLATION_AUDIT.md` (same directory; verdict
`ISOLATION PASS — suitable for ARCH-002 preregistration`) is the binding
boundary document. Every §/R/D/G citation below refers to it unless noted.
**Governance**: Zero-Leakage; Questions A (DEV-007/H=500) and B (ARCH/H1)
stay separate — no H=500 logic in either ARCH-002 arm (§3, §5).
**Objective**: Test whether the isolated H1 terminal-control mechanism
causally improves the best appropriate current development architecture.

## §0. Decision freeze table (D1–D8)

Each row: the frozen selection + where it is fully specified. Selections
among repo-supported options carry their justification in the cited section;
nothing below was tuned against results (no ARCH-002 results exist; no
parameter was swept; no seed was executed).

| ID | Decision | Frozen selection | Spec |
|---|---|---|---|
| D1 | Worker-command whitelist/schema | Unit ops {N,S,E,W,HARVEST,COLLECT_FERTILIZER,DROP,PASS}; DROP-only (no PLACE); COLLECT included under reap-only-flagged-at-E (R8); markets verbatim E–717, 718 per D3; hand-aligned emission | §5, §7 |
| D2 | Entry step E | **E = 712** (7-turn window 712–718, Dmitrii-comparable) | §6 |
| D3 | Step-718 market rule | **Verbatim baseline passthrough** (H1 market rule = identity downstream of outer `terminal_market`); live-recompute variant recorded as future experiment H1b, NOT authorized | §5, §8 |
| D4 | Candidate generation + sim + budget | Mirror Dmitrii `_proposals`/`plan_terminal` at live settings (128 sims, 1 pass, ≤8 proposals/worker); offsets 0–6; carry-closure + top-6 singles + top-3×top-3 pairs; walk→ops→nearest-shed→DROP, PASS-padded; 2 direct reserves; worker-by-worker single pass; frozen entry prices; engine-exact sim validated per §11 | §7, §11 |
| D5 | Dominance predicate | Row-wise prefix dominance (pre-market shed ⊇, sold ⊇, per-actor deposits ⊇; overflow ⇒ fail) + strict value gain at frozen entry prices + two no-steal gates + acceptance conjunction + markets-verbatim certificate; BUY_PRODUCT modeled with entry-money coverage gate ($125/unit worst case); all other market-op types ⇒ abstain | §8 |
| D6 | Tolerances / tie-breaking | Strict `>` everywhere (no epsilon); integer ⊇; frozen sort keys (bundles, proposals); last-strictly-improving wins; fixed worker/offset order; fixed float expression order, no parallel reduction | §9 |
| D7 | Abstention procedure | 8 entry guards (G0–G7: pins, validity, window-slice admissibility, BUY coverage, entry handshake, budget, adoption gates) + stepwise re-verification + non-consecutive abandonment + abandon-to-baseline (unconditionally safe: baseline is closed-loop) + frozen 15-code reason enum + per-seed×seat telemetry | §10 |
| D8 | Baseline identity | **`candidates/compiled_v54_plus_residual.py`** (SHA-256 `18402ec6…`, Sub 56146971) — V54++ residual. Full adversarial analysis in §3 | §3 |

## §1. Research question

Does grafting a dominance-gated, reap-and-ferry terminal optimizer (window
712–718, abstain-by-default, markets untouched E–717) onto the frozen V54++
residual baseline change expected terminal money, and — when the optimizer
activates — does it do so without physical-degradation tails? Performance
(§15–§17) and mechanism exposure (§18) are reported separately and never
collapsed into one score (audit §24; DEV-007 PROTOCOL.md §5 precedent).

## §2. Falsifiable hypothesis

**H1-ACT**: Among prospectively defined activation-exposed episodes (plan
accepted at E in ≥1 seat, §18), the conditional paired contrast
(H1 − baseline) has positive mean with zero exposed-seed harm
(contrast ≥ 0 on every exposed seed) and zero H1-attributable damage
anywhere (contrast min ≥ 0 across all N). Falsified by: k ≤ 2
(untestable, §21 pattern C — a distinct outcome from falsification);
conditional mean ≤ 0; any exposed-seed harm; or any forensically
confirmed H1-attributable severe failure (§21 pattern B/F).
**H1-OVERALL** (separate): the unconditional paired mean over all N
seeds is nonzero (§15; two-sided test, §19). The experiment can support
H1-ACT while H1-OVERALL is neutral (pair A+E, §21) — coherent, not
contradictory.

Causal-language rule (mirrors DEV-007 PROTOCOL.md §5): activation is
endogenous to game state (physical positions, shed, guard outcomes).
The conditional contrast is reported ONLY as "the conditional paired
effect among prospectively defined activation-exposed episodes." The
words "causal treatment effect" are forbidden for it; the unconditional
estimand (§15) is the experiment's causal contrast (randomized by design:
treatment assignment is the arm label, seeds fixed).

## §3. Baseline (D8 + adversarial analysis)

**Frozen baseline**: `candidates/compiled_v54_plus_residual.py`, SHA-256
`18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`
(frozen live submission 56146971). Read-only; hash re-verified at
implementation freeze and at launch (§22).

### §3.1 Adversarial baseline analysis (V54++ vs DEV-005 vs DEV-006)

Candidate 1 — V54++ residual (SELECTED).
Standing: the frozen live submission; the only architecture with
deployment standing and the largest evidence base (live Elo ~1499 is
observational, but deployment status is governance fact).
One-factor fit: H1 is the ONLY difference between arms; no unproven
mechanism hides in the control.
Question separation: neither arm contains H=500 or checkpoint logic
beyond the baseline's own, so ARCH-002 cannot disturb DEV-007/Question A
(master prompt §17).
Terminal richness: backbone-route games keep spending worker-turns on
WATER/CARE late (audit §1.2) — a real reap/ferry opportunity surface.
Risk admitted: the result generalizes to "H1 on V54++" only; transfer to
specialized architectures needs its own experiment (§24 interpretation
rule I-5).

Candidate 2 — DEV-005 confirmed-shop scheduler (REJECTED as baseline).
For: it is the development track's most advanced mechanism by face
validity (confirmed-shop gating sharply cut DEV-004's loss rate on its
fresh cohort); testing H1 "on the best development architecture" has
surface appeal.
Against (decisive): DEV-005's superiority over V54++ is NOT established
— its +$797.76 rests on ONE fresh cohort (247000–247049) with no
independent replication and no reserved-cohort qualification on record
(`experiments/EXP-DEV-005/` contains no qualification artifact, unlike
`experiments/EXP-DEV-006/QUALIFICATION/`). Adopting it as the control
would bake an unproven macro mechanism into the baseline, so any H1 win
could be an H1×specialization interaction rather than the isolated
terminal mechanism — exactly the confounding §5 forbids. It also stacks
two development mechanisms before either is independently replicated.

Candidate 3 — DEV-006 horizon-guard scheduler (REJECTED as baseline).
For: latest in the DEV line.
Against (decisive): H=500 is affirmatively UNPROVEN (formal
qualification inconclusive, p=0.0849, zero guard firings) AND under
active frozen investigation (EXP-DEV-007, unexecuted). Using DEV-006 as
either arm's foundation merges Questions A and B (forbidden, §5) and
risks a future where DEV-007 retires H=500 while ARCH-002's baseline
contains it — invalidating the control retroactively.

### §3.2 Why V54++ is not baseline-shopping

The selection criterion was fixed before any ARCH-002 outcome exists
(none can exist: no implementation, no runner, no execution): the
control must be the architecture with the strongest settled standing
under one-factor discipline. That criterion selects V54++ uniquely. Had
DEV-005 been qualified on a reserved cohort, or DEV-007 resolved, the
criterion could have selected differently — the protocol records this
counterfactual explicitly so the choice is auditable, not convenient.
A future integration experiment (H1 × surviving DEV architecture) is the
named vehicle for any combined claim (§24, next artifacts); no combined
deployment is licensed by ARCH-002 alone.

## §4. Treatment

**Treatment**: the frozen V54++ baseline (§3) + the H1 terminal overlay
frozen in §5–§12 (whitelist D1, entry E=712, 718 passthrough, Dmitrii-
mirrored search/dominance/tolerances/abstention). One-factor difference:
worker commands on steps 712–718 when a plan is accepted; step-718
markets may differ between arms ONLY through stock differences ordered
by the IDENTICAL baseline collision rule (D3). The H1 implementation
does not exist yet; §24 lists exact implementation prerequisites, and
§22 gates freeze the implementation (own commit + hash) before any
execution. No other file, parameter, or mechanism differs between arms.

## §5. Intervention boundary

H1 operates STRICTLY inside the audit-defined terminal boundary (audit
§2/B1–B5). Frozen prohibitions (each review-verifiable by static grep at
implementation freeze; any violation fails §22 gate G-IMPL):

- P1. No macro route changes: no route-table edits, no route additions,
  no `_select_route`/registry/checkpoint interaction of any kind.
- P2. No shop-router changes: no reads of shop state beyond what the
  baseline already passes through; no shop-conditioned branches.
- P3. No crop/animal strategy changes: whitelist (§5.1) excludes
  PLANT/WATER/FEED/CARE/BUILD/FERTILIZE/BUY/HIRE; validator rejects them.
- P4. No checkpoint architecture changes: zero references to DEV
  checkpoint/valuation/registry symbols (audit R7).
- P5. No H2 advance/subtract sales overlay: H1 emits baseline markets
  verbatim on 712–717 (B1); no SELL adds/removes/quantity/order changes;
  no due-ledger writes (audit R3/R6).
- P6. No H4 fertilizer logic: COLLECT permitted ONLY for tiles flagged
  `fertilizer_available` at entry E (flags set at the last dawn, step
  696; unrefreshable in-window, audit §4/§15); no collection-policy,
  drip-sell, or valuation changes beyond the frozen terminal price
  vector (audit R8). Telemetry counts fertilizer units reaped per
  exposure (§18) so H4-overlap is auditable post hoc.
- P7. No H5 changes: checkpoint grid untouched (none exists in-window).
- P8. No new H=500 logic: zero references to `HORIZON_GUARD_THRESHOLD`,
  `REJECT_HORIZON`, `remaining_horizon` (audit §20/Test F). Neither arm
  contains H=500 (D8 selects V54++), so Test F passes structurally and
  Question A/B separation holds.
- P9. No cross-step state except one per-seat accepted-plan record
  created at/after E and discarded on step 0 or non-monotonic step
  (audit R1; mirrors `policy.py:122–126`).
- P10. Overlay ordering frozen (audit R14): H1 unit overlay applies
  downstream of baseline `_TERMINAL_UNITS`; the (identity) H1 market rule
  applies downstream of the outer baseline `terminal_market`.

### §5.1 Whitelist and emission schema (D1)

Emitted unit ops, per worker per step, drawn ONLY from
{NORTH, SOUTH, EAST, WEST, HARVEST, COLLECT_FERTILIZER, DROP, PASS}.
DROP-only (no PLACE in proposals; abandonment resumes baseline, never
salvages — safe because the baseline is closed-loop, §10.4).
Emission schema `{farmer: [...], hands: [[...] × live_count], market:
[...]}` with hands padded/truncated to the live unit count exactly as
`align_hands` does (`scripts.v19_terminal:52–65`; audit R12-a).
Justification for including COLLECT (recorded per the selection rule):
H1 tests the OBSERVED Dmitrii reaper, whose generator reaps flagged
fertilizer (`terminal_planner.py:271–273`); excluding it would test a
different, weaker mechanism and forfeit transfer inference, while R8/P6
contain the H4 boundary exactly. Either choice was isolatable; this one
preserves mechanism identity.

## §6. Exact terminal horizon (D2: E = 712)

Window: steps 712–718 inclusive (7 turns). E = 712 frozen for three
recorded reasons: (1) exact Dmitrii comparability (same window,
`policy.py:12`); (2) cleanest shadow entry — NO baseline terminal
overlay fires at 712 (recall starts 713; audit §1.1/§3), so the shadow's
first predicted step replays only replay+repair+reorder+controller;
(3) maximum ferry horizon (walk+ops+return ≤ 718 − E) maximizes mechanism
EXPOSURE (more reachable bundles), which is what a mechanism test wants
to maximize; compute stays bounded via §7 caps regardless. Alternative
E = 713 (recall-aligned) was considered and rejected: shorter horizon
with no compensating simplification.
Window statics (frozen premises from audit §4; re-asserted as entry
guards in §10, never assumed): no dawn; no shop unlocks; no RNG; no
yield/flag accrual; shop demand ticks at 712 and 716 only; even-step rot
of expired ongoing crops; last action step 718 (port `sim.py:336–337` +
`sim.hpp:359` + 719-action routes).

## §7. Candidate search space (D4)

Mirroring Dmitrii `_proposals` + `plan_terminal`
(`terminal_planner.py:241–363`) at live settings
(max_simulations=128, passes=1, proposals_per_actor=8;
`policy.py:37–40`, `SOURCE_MAP.md:27`), with these frozen bindings:

- S1. Detailed shadow baseline run over 712–718 per §11 sim; per worker
  (actor order frozen: farmer = actor 0, then hands by live index),
  per start-offset 0–6 from the detailed run's states.
- S2. Bundle sources: standing-yield HARVESTs (mature only — crops with
  `day − planted_day ≥ first_yield_day` per `unit_model.py:12–16`
  [WHEAT 2, CARROT 2, TOMATO 8, STRAWBERRY 10, MELON 10]; any animal tile
  with yield_units > 0) + COLLECT_FERTILIZER on tiles flagged at E.
  No-steal pre-filter: exclude cells/ops owned by another actor in the
  current best run (mirror `:268,271`) — where "owned" is computed over
  the shadow BASELINE's scheduled acquisitions (route HARVEST/COLLECT
  events) union sibling H1 proposals.
- S3. Reachability: `len(walk) + len(ops) + len(return) ≤ 7 − offset`,
  x-first Manhattan walk, return = walk to nearest shed-access tile +
  DROP (mirror `:275–276,286–294`). Engine moves are single-step and
  in-bounds-always-legal (`sim.py:364–371`).
- S4. Variants per (worker, offset): carry-only closure (if loaded) +
  top-6 singles + top-3×top-3 pairs by value/distance at frozen entry
  prices (mirror `:278–285`); each routed and PASS-padded to window end.
  Across ALL offsets of one worker: 2 direct-return variants reserved
  first, then ranked remainder, capped at ≤8 trials per worker (mirror
  `:301–303`: `chosen[:max_per_actor]` with live max 8).
- S5. Outer loop: worker-by-worker single pass; each trial simulated;
  adopt on strict gain + dominance + no-steal (§8); at most 128 sims
  total (+1 detailed re-sim per adopted worker, uncounted — mirror
  `:356`); fixed trial order (worker 0..n−1, proposals in frozen
  ranked order, §9).
- S6. Value term uses FROZEN entry prices: integer public prices read
  from obs at E (missing ⇒ 1, mirror `:317`).

## §8. Dominance definition (D5)

### §8.1 Predicate (mirror + adapted)

`DOMINATES(candidate, baseline)` ⟺ ALL of:

1. `candidate.overflow_units == 0` (DROP-destroyed units counted exactly
   as `terminal_planner.py:174–176`; engine destroys over-cap DROP units,
   `sim.py:375–390`).
2. For EVERY row t in 712–718: pre-market shed ⊇ baseline's AND
   cumulative sold ⊇ baseline's AND per-actor cumulative deposits ⊇
   baseline's (integer ⊇ per product; mirror `:209–220`).
3. Strict value gain: `Σ(sold + final_shed) × priceE > baseline_value`
   (mirror `:223–225,341`; prices = §7/S6 frozen integers).
4. No-steal adoption gate: every HARVEST/COLLECT acquisition by OTHER
   actors in the current best run still occurs (same cell, same op,
   same actor, ≥ quantity) in the trial (mirror `:342–353`).
5. Acceptance conjunction: changed-workers non-empty AND some actor
   deposited strictly more of some product AND every product's sold
   delta ≥ 0 AND some product's sold delta > 0 AND final re-sim
   dominates (mirror `:364–391`).
6. Markets-verbatim certificate: the plan's 712–717 markets equal the
   shadow baseline's element-wise (adapts `:391` to our sparse markets;
   transplant hazard H1 — sparse markets are ADMITTED, never assumed
   into the 9-product clearing shape, cf. audit G1).

### §8.2 Market modeling inside the shadow (transplant hazards H1–H4)

- H1 (sparse markets): admitted as-is; no `_fixed_market` analogue.
  Validator asserts only op-type admissibility (§10/G3).
- H2 (BUY orders): `BUY_PRODUCT` (WHEAT/FERTILIZER) admitted and modeled
  EXACTLY per engine (`sim.py:589–593,642–652`: per-unit quote at
  `price(inventory−1)`, requires money ≥ price AND shed room).
  Opponent-dependence of quotes/money is closed by the ENTRY-MONEY
  COVERAGE GATE: let U = total window BUY units in the shadow baseline
  markets; abstain unless `money_at_E ≥ 125 × U`, where $125 = WHEAT
  curve maximum derived from `MARKET_PARAMS` WHEAT
  `(25,10000,400,"sqrt",0.80,…)`: `25 + (0.8×25/√400)×√10000 = 125`
  (`v23.simulator:19,51–65`). Shed room at each BUY step is physical and
  shadow-exact; SELL revenue can only add money. Coverage ⇒ all window
  BUYs succeed deterministically regardless of opponent ⇒ shadow-exact.
  (Recorded: yarn-family routes place BUY WHEAT at 712 (18–29u) and 716
  (32u) — the abstain-on-BUY alternative would zero YARN exposure and is
  therefore REJECTED.) Any market op outside {SELL, BUY_PRODUCT} ⇒
  abstain (reason ABSTAIN_MARKET_OP).
- H3 (ledgers): shadow clones readable controller ledgers at E
  (`due`, `pending`, `opponent_supply`, `last_market_net`,
  `last_inventory`, `last_shops`, `near_*`, `mirror_*`;
  `v49:369–386` via `agent.controller.states`) and replays `_repay`
  with due-carry (`v49:476–503`), `_release_pending` (assert-empty at E;
  `pending` is always empty with defer disabled, audit §18.2),
  fronting reorder (`v49:784–797`), `_update_flow` (`v49:394–474`), and
  the step-718 baseline `terminal_market` — then the audit-§1.3 no-op
  overlays are SKIPPED by proof (seed-trim/shed-guard no-op on 700–718;
  the skip is re-verified by the handshake, not trusted blindly).
- H4 (money/flow-dependent fronting): modeled exactly each simulated
  step (deterministic pure functions, audit §18.3 paths 1–2). Residual
  misprediction (opponent-driven quotes) is caught by handshake +
  stepwise re-verification and abandons safely (never a corrupted plan).
  Shared-price effects are confined to the VALUE term; legality is
  certified in units only (audit R5).

## §9. Tie-breaking (D6)

Frozen exactly (mirror `terminal_planner.py:278,299,353`, `:205–206`):

- T1. All comparisons strict: value `>` (no epsilon), ⊇ on integers,
  `> 0` / `≥ 0` on sold deltas. No floating tolerance anywhere.
- T2. Bundle rank key: `(-value/distance, -value, (x, y))` with
  value/distance computed in frozen entry-price units; xy ascending.
- T3. Proposal rank key: `(-net_value, offset, route)` with route
  compared as a tuple-of-tuples lexicographically.
- T4. Per worker, the winner is the LAST strictly-improving trial in
  ranked order (reassignment on strict improvement only).
- T5. Two direct-return (carry-closure) variants are always ranked first
  (mirror `:301`); the ≤8 cap applies after reservation.
- T6. Fixed enumeration order: workers 0..n−1, offsets 0..6, variants in
  ranked order. Float arithmetic in fixed expression order; no parallel
  reduction; same code path in every sim (§12).

## §10. Abstention / fail-safe behavior (D7)

### §10.1 Entry guards (evaluated at E, in order; first failure abstains)

- G0. Config pins: boardSize 10, turnsPerDay 24, episodeSteps 720,
  shedCapacity 100, maxMarketOrdersPerTurn 10 (mirror
  `terminal_planner.py:28–37`, `policy.py:50–54`).
- G1. Shed validity: non-negative integer quantities, total ≤ 100
  (mirror `policy.py:81–82`).
- G2. Supported items: shed + carried inventories contain only the 9
  products (mirror `:85–91`); inventory list length == worker count ≤ 32
  (mirror `terminal_planner.py:132–134`).
- G3. Window-slice admissibility: shadow baseline unit ops over 712–718
  contain no PLANT/BUILD/BUY/HIRE-family ops (adapts the weed-guard,
  `policy.py:73–79`, to our replay ledger); shadow baseline markets over
  712–717 contain only SELL/BUY_PRODUCT (adapts `_fixed_market`, §8.2/H1);
  `pending` ledger empty at E (audit §18.2).
- G4. BUY coverage gate (§8.2/H2): `money_at_E ≥ 125 × U`.
- G5. Entry handshake: live baseline action at E deep-equals the shadow
  baseline action at E after `align_hands` normalization on both sides
  (mirror `policy.py:159–163`; equality = element-wise list equality on
  farmer/hands/market). Any inequality ⇒ abstain (covers weed-repair
  replay tails, audit §12.2/R10).
- G6. Search completes within the §7/S5 budget; budget exhaustion with
  no adoption ⇒ abstain (mirror `:327–328,364–368`).
- G7. Adoption gates §8.1(3–6) all pass; else abstain with the specific
  reason (§10.3).

### §10.2 Stepwise re-verification and abandonment

Before emitting the planned action at each step t in 712–718: assert
live physical state == plan's expected state for t AND live baseline
action == shadow baseline action for t (same equality as G5). On ANY
mismatch, or on non-consecutive callback (mirror `policy.py:130–131`):
abandon — emit the LIVE baseline action for t, forget the plan, record
ABANDON_MISMATCH_T / ABANDON_NONCONSECUTIVE. No re-planning within the
game after abandonment (single planning episode per game, at E).

### §10.3 Frozen reason-code enum (telemetry, §18)

`OK_ACTIVATED`, `ABSTAIN_CONFIG`, `ABSTAIN_SHED`, `ABSTAIN_ITEMS`,
`ABSTAIN_WINDOW_OPS`, `ABSTAIN_MARKET_OP`, `ABSTAIN_BUY_COVERAGE`,
`ABSTAIN_HANDSHAKE`, `ABSTAIN_BUDGET`, `ABSTAIN_NO_GAIN`,
`ABSTAIN_DOMINANCE`, `ABSTAIN_NOSTEAL`, `ABSTAIN_ACCEPT`,
`ABANDON_MISMATCH_T` (with t), `ABANDON_NONCONSECUTIVE`. Exactly one
code per game; histogram is a mechanism-exposure endpoint (§18). No
code may be added, split, or redefined after execution begins (§23).

### §10.4 Why abandon-to-baseline is unconditionally safe (no salvage mode)

Unlike Dmitrii's open-loop tape + day-queues (which need `_resume_parent`
vs `_recover_observed` distinguished by deviation,
`terminal_planner.py:402–470`), our baseline re-derives EVERY action
from live obs each turn (replay-by-step + live-position weed repair +
live-state overlays; audit §1/§12). Resuming it at any live state is
therefore exactly "the baseline acting" — no stale-position hazard
exists by construction. H1 implements NO salvage mode; post-acceptance
abandonment always emits the live baseline action. This is a structural
safety advantage of grafting onto a closed-loop baseline, and it is why
T13/T15 fail safe (§21 of the audit).

## §11. Simulator-equivalence requirements

The H1 shadow sim (implementation prerequisite P-SIM, §24) must satisfy,
BEFORE any experimental seed executes:

- Q1. Engine-exact transitions: unit actions, decay, deposits (DROP
  destructive / PLACE capped), SELL/BUY execution, town-consume ticks,
  shed-capacity and order-cap rules per `sim.py` + `unit_model.py`
  (SHA `bc8a5487…`, engine 1.32.7). Micro-state unit tests vs the port
  step function on HAND-CONSTRUCTED states (no game seeds involved):
  PASS bar = 100% agreement on the frozen unit-test battery (battery
  frozen with the implementation).
- Q2. Baseline-prediction parity on CONSUMED cohorts only (never the
  experimental cohort, never the holdout): shadow-vs-live baseline
  action agreement over 712–718 reported as a rate with mismatch
  forensics; every disagreement must resolve to abstention (G5/§10.2),
  never to adoption-on-disagreement. No numeric pass bar is set on the
  RATE (it measures exposure, §18/U10-analogue); the PASS bar is on the
  PROPERTY: zero adoptions on disagreeing trajectories.
- Q3. Engine re-validation: the DEV-007 pre-execution battery (port
  manifest, golden 47,520/47,520 traces; DEV-007 PROTOCOL.md §10) is
  re-run in the execution session. Same engine, same port, same proofs.

## §12. Determinism requirements

- Same (seed, seat, obs-history) ⇒ bit-identical plan record and action
  stream. No RNG, no wallclock, no thread/contention dependence, no
  dict/set iteration order dependence in any frozen sort or ledger walk
  (§9/T6; audit R12).
- Validation (implementation prerequisite P-DET): double-run planning on
  consumed-cohort states bit-identical (plan bytes + telemetry equal);
  Python minor version + relevant library versions pinned in the
  implementation-freeze record.
- Float determinism: all value/rank arithmetic in fixed expression
  order within one thread (§9/T6); entry prices are small integers so
  the value term is exact in float64 (products ≤ ~10^2 units × prices ≤
  ~10^3 ⇒ sums < 2^53; stated, not merely hoped).

## §13. Seed provenance

### §13.1 Selection rule (deterministic, outcome-independent)

The cohort is the contiguous block **[B, B+499]** with **B = 320000**,
defined as the smallest multiple of 10000 strictly above every frozen
experimental-cohort upper bound (maximum = 310499, the DEV-007 reserved
cohort) and disjoint from all named conditional-fallback blocks
(410000–410499, 510000–510499; DEV-007 SEED_SELECTION_RULE.md §2).
No game outcome, activation likelihood, shop distribution, or any other
experimental result entered the choice of B — round-number anchoring at
a high, distant location only (mirrors the DEV-007 rule construction).

**Selected cohort: seeds 320000–320499 inclusive (N = 500).**

Fallback chain (provenance-triggered ONLY, mirroring DEV-007 §2):
Fallback 1: B = 420000; Fallback 2: B = 520000; further B += 100000
until a block passes the FULL audit. Fallback triggers ONLY on
provenance failure of the primary block, never on any outcome (no
outcome may exist before the freeze). The primary block PASSED (§13.3),
so no fallback was audited or touched.

### §13.2 Disjointness proof (integer arithmetic)

Selected block [320000, 320499] vs every protected range:

| Protected range | Reason | Overlap |
|---|---|---|
| 214200–214249 | virgin final holdout | none (105,751 below) |
| 310000–310499 | DEV-007 RESERVED (unexecuted) | none (9,501 below) |
| 410000–410499 / 510000–510499 | DEV-007 conditional fallbacks | none (above) |
| 50000–50499, 50150–50199, 50050–50099, 50100–50149 | consumed/benchmark | none |
| 60000–60049 | sweep-contaminated | none |
| 245000–245049 … 248000–248049 | consumed DEV-003/004/005/006 | none |
| 1000–2683 | stride-reachable executions | none |
| 249000–249049, 250000–250049, 255000–255049, 260000–260049, 300000–300049 | named reserved alternatives | none |
| scratch seed grids 920001–970020 | analysis grids | none |

Minimum distance to any protected range: 9,501 seeds (above the DEV-007
reserved block); 105,751 seeds above the final holdout. Simulator
compatibility (static, no execution): integer seed accepted,
deterministic RNG `(seed × 1000003) ^ day` has no modulo folding at
this magnitude; 320499 is 0.015% of the 2^31 Kaggle seed space
(construction mirrors DEV-007 SEED_SELECTION_RULE.md §4).

### §13.3 Provenance audit result (static only; zero seeds executed)

Audit date 2026-09-15, dimensions mirrored from DEV-007
SEED_PROVENANCE.md. No candidate seed was executed, constructed, or
simulated; all checks are file-content, history, and arithmetic
inspection:

| Dimension | Method | Hits | Verdict |
|---|---|---|---|
| Full-tree literals | `grep -rIln -E '\b320[0-4][0-9]{2}\b'`, excl. .git | 3 files, all timestamp artifacts (below) | Clean |
| Tracked files | `git grep -l` same pattern | 1 file (same artifact) | Clean |
| Git history | pickaxe `-S 320000/-S 320499`, regex `-G`, message grep | 1 commit (CSV-add artifact) | Clean |
| Stride / range | all `range()` 6-digit bounds in 310000–329999; seed bases | 0 covering the block | Clean |
| Result DBs (JSON) | `"seed": 320xxx` full-tree | 0 | Clean |
| Result tables (CSV) | `^320xxx,` seed rows | 0 | Clean |
| Execution logs | `Seed 320xxx` / `Game(320xxx` (full-tree grep + bounded search) | 0 | Clean |
| Session stores | execution-pattern grep over Muse sessions | 0 execution contexts | Clean |
| Temp/sandbox | `/tmp` listing + literal grep | clean (own probes only, no seed refs) | Clean |

Classification of every match: `replays/raw/georgymamarin/teams.csv`
(31× `320000`, proved 31/31 timestamp fractions `.320000` in
leaderboard datetime fields, 0 bare); `scratch/
analyzed_episodes_55944418.csv` (1 telemetry timestamp fraction, the
tracked hit); `scratch/kernels_list.json` (`last_run` timestamp
fractions). Sole history hit `07b8f16` is the commit that ADDED the
`analyzed_episodes` CSV (same artifact commit DEV-007's audit
classified). Nearest seed-base literal anywhere: singleton `314159` in
`scratch/run_closed_loop_mutation_audit.py:41`, 5,841 seeds below the
block, unreachable. **Verdict: cohort 320000–320499 CERTIFIED VIRGIN —
zero prior exposure.** Post-execution it becomes CONSUMED per §24/I-7.

## §14. Sample-size rationale (N = 500 seeds, 2 games/seed = 1,000 games)

N = 500 frozen for three recorded reasons (no outcome data exists; no
sweep was run; this section is planning arithmetic only):

1. Precision parity with DEV-007 (same program scale): at cross-seed SD
   1,500/2,000/3,200 (DEV-007 POWER_PLANNING.md observed range),
   N=500 gives SE 67/89/143 and 95% half-widths ~131/175/280. This
   resolves unconditional means of a few hundred coins — the scale of
   every credible development signal on record (DEV-005 +$797.76,
   DEV-006 qual +$517.58).
2. Exposure bracketing across the full activation-uncertainty range
   (audit U10: activation prior unknown; X ~ Binomial(500, p), exact
   `math.comb` arithmetic, no seeds executed):

   | p | E[X] | P(X=0) | P(X≥3) | P(X≥10) | P(X≥25) |
   |---|---|---|---|---|---|
   | 0.02 | 10.0 | 0.000041 | 0.997409 | 0.543336 | 0.000038 |
   | 0.05 | 25.0 | ~0 | 1.000000 | 0.999832 | 0.528649 |
   | 0.10 | 50.0 | ~0 | 1.000000 | 1.000000 | 0.999984 |
   | 0.25 | 125.0 | ~0 | 1.000000 | 1.000000 | 1.000000 |
   | 0.50 | 250.0 | ~0 | 1.000000 | 1.000000 | 1.000000 |

   Even at a pessimistic 2% activation rate, P(k=0) ≈ 0 and P(k≥3) ≈
   99.7% — the mechanism question (§21 pattern A/B vs C) is decidable
   across the entire plausible range. N=250 was considered and rejected:
   at 2% it risks pattern-C ambiguity by luck (P(X<3) ≈ 12%), failing
   the experiment's stated purpose.
3. Operational scale: 1,000 games + forensic replays fits a single
   session at measured engine throughput (~2.2 s/game; DEV-007
   POWER_PLANNING.md §1) plus bounded planning cost (≤128 sims × 7
   steps per H1 game-side at E). Exact H1 runtime is UNKNOWN until the
   implementation exists (prerequisite P-PERF, §24: measure on consumed
   cohorts); the protocol caps WORK (sims, games), never wallclock, so
   no timing assumption can invalidate the design.

Design: 2 games per seed — H1 vs baseline with seats swapped (game a:
H1 = seat 0; game b: H1 = seat 1), identical engine seed/CRN handling
to DEV-007 (same port, same 4-games/seed CRN discipline reduced to the
single paired contrast; no diagnostic arm exists for H1).

## §15. Primary endpoint

ESTIMAND 1 — UNCONDITIONAL PAIRED PERFORMANCE (H1 − baseline, all N).
Per-game delta δ = money(H1 seat) − money(baseline seat) at episode end
(port `reward()`, `sim.py:316–317`). Per-seed paired delta
Δᵢ = 0.5(δᵢ,ₐ + δᵢ,ᵦ). Primary statistic: mean(Δ) with two-sided
Student-t p (df = N−1) and 95% CI (§19). One primary endpoint; α = 0.05.
Tie rule: Δᵢ == 0.0 exactly (mirror DEV-007 §5).

## §16. Secondary endpoints (descriptive; no claim license, §20)

Same battery as DEV-007 Estimand 1 (§5): N, mean, median, SD (n−1), SE,
t, two-sided p, 95% CI, 10% trimmed mean, p01/p05/p10/p25/p50/p75/p90/
p95/p99 (linear interpolation), min, max, W/L/T + rates, nonzero count,
mean-ex-best, mean-ex-top2. Computed on per-seed Δᵢ. Percentile/p-value
conventions frozen: linear interpolation; `scipy.stats.t.sf`, df = N−1.

## §17. Tail-risk endpoints (frozen bars)

- Loss rate = #{Δᵢ < 0}/N; harm count = #{Δᵢ < 0} with forensic
  attribution (§23/F-TRACE).
- Minimum Δᵢ (new minima forensically traced, §23).
- Tail-harm bar (program precedent: DEV-001 stop rule, DEV-007 pattern
  F): TAIL-HARM ⟺ min(Δᵢ) < −$800 OR any forensically confirmed
  H1-attributable severe failure. The −$800 bar is adopted UNCHANGED for
  cross-experiment comparability (recorded selection, not invention).
- Large-excursion census: seeds with |paired Δᵢ| ≥ $2,000 (prospective
  "unusually large" threshold, mirrors DEV-007 §9) + per-seat extremes.

## §18. Mechanism-exposure endpoints

- Activation: a seat-game is activated ⟺ its recorded reason code is
  OK_ACTIVATED (§10.3); a seed is exposed ⟺ activated in ≥1 of its 2
  seat-games.
  k = #{exposed seeds}; activation-rate estimate k/N with exact
  Clopper-Pearson 95% CI (mirror DEV-007 Estimand 2); per-game rate
  secondary.
- Reason-code histogram over the frozen §10.3 enum (all 1,000 games);
  ABANDON_MISMATCH_T further split by t.
- Search telemetry per activated game: proposals generated/capped,
  trials simulated (≤128), adoptions per worker, re-sim result,
  planning_ms (bounded, telemetered — mirror Dmitrii, no wallclock
  gating of correctness).
- Conditional contrast (mirror DEV-007 Estimand 3, same non-causal
  language rule as §2): among the k exposed seeds — mean, median, SD,
  95% CI (Student-t, labeled descriptive when k small), min, max, W/L/T
  of (H1 − baseline); full-prevention count (Δᵢ == 0 exactly on exposed
  seeds is EXPECTED to be ~0 for H1, unlike a veto guard — recorded so
  the metric is not misread); exposed-seed harm count (contrast < 0).
- Fertilizer audit fields per exposure (P6/R8 auditability): fertilizer
  units reaped by H1 proposals, baseline scheduled fertilizer
  acquisitions preserved/violated (must be preserved: no-steal gate).
- Purity property (integrity, §22/P-PURE): Δᵢ ≠ 0 ONLY on exposed seeds;
  pre-E action identity on ALL games; E–717 market verbatim on activated
  games. Any violation ⇒ STOP + investigate as one-factor breach (mirrors
  DEV-007 C1–C4).

## §19. Statistical analysis

Primary unit: seed (paired over 2 seats). All conventions frozen to
mirror DEV-007 §5 exactly: tie Δᵢ == 0.0; percentiles by linear
interpolation; p-values two-sided Student-t via `scipy.stats.t.sf`
(df = N−1); CIs Student-t, df = N−1; activation-rate CI exact
Clopper-Pearson. No covariate adjustment, no transformation, no
winsorization, no outlier deletion — the trimmed-mean and mean-ex-best/
top2 secondaries (§16) are the ONLY robustness views, and they are
descriptive. No interim analysis: statistics are computed once, after
all 1,000 games complete and the execution manifest is sealed (§23).

## §20. Multiple-testing policy

One primary endpoint (§15) at α = 0.05, one pre-committed analysis —
no multiplicity correction is required and none is applied BECAUSE no
other comparison can license a claim: all §16–§18 batteries are
descriptive/forensic. Forbidden after execution begins: new endpoints,
subgroup claims (by route/shop/reason-code — description allowed, claims
not), redefinition of activation/exposure (§10.3 enum frozen), threshold
shopping on §17/§21 bars, and any analysis conditioned on outcomes
beyond the frozen purity/forensic triggers (§18, §23).

## §21. Success / failure criteria

### §21.1 Mechanism patterns (from §18; purity §22/P-PURE must hold)

- **A. mechanism supported**: k ≥ 3 AND conditional contrast mean > 0
  AND zero exposed-seed harm (contrast ≥ 0 on every exposed seed) AND
  zero H1-attributable damage anywhere (contrast min ≥ 0 across all N).
- **B. mechanism weakened**: k ≥ 3 AND (conditional contrast mean ≤ 0 OR
  any exposed-seed harm OR any H1-attributable damage).
- **C. mechanism untestable**: k ≤ 2 — too few episodes to assess
  consistency. k = 0 is reported verbatim as "mechanism not activated in
  this cohort". (Threshold k ≥ 3 mirrors DEV-007 pattern A/B/C for
  cross-experiment consistency; §14 shows P(C) ≈ 0 even at 2%
  activation.)

### §21.2 Overall patterns (from §15–§17; descriptive bar, NOT a claim)

- **D. overall improved**: two-sided p < 0.05 with mean > 0 AND
  min ≥ −$800.
- **F. overall harmed**: two-sided p < 0.05 with mean < 0, OR
  min < −$800, OR forensically confirmed H1-attributable severe failure.
- **E. overall neutral**: all other outcomes.

The result is reported as a PAIR (e.g. "A + E"). Pattern D + C is
incoherent (overall movement without activation) and triggers integrity
investigation under P-PURE before any interpretation (§22).

### §21.3 SCIENTIFIC SUCCESS vs COMPETITIVE SUCCESS (frozen gates)

**SCIENTIFIC SUCCESS** ⟺ mechanism pattern **A** (supported: k≥3,
positive conditional contrast, zero harm, zero attributable damage),
reported with its overall pair (A+D, A+E, or A+F — the pair is never
collapsed). Rationale: the experiment's question (§1) is whether the
isolated terminal mechanism works safely when it engages; A answers
exactly that. Pattern B is a valid scientific answer ("weakened/
falsified-as-specified", feeds H1b redesign); pattern C is a valid
answer ("not exposed here").

**COMPETITIVE SUCCESS** ⟺ SCIENTIFIC SUCCESS **AND** ALL of:
(mean ≥ +$500) AND (lower 95% CI of the unconditional mean > $0) AND
(min ≥ −$800) AND (loss rate ≤ 5%) AND (no confirmed H1-attributable
severe failure). Recorded selection rationale for +$500: no validated
coins→Elo transfer function exists in the repository (UNKNOWN — the
mapping from paired-coin deltas vs V54++ to leaderboard Elo is not
established, and this protocol invents none), so the competitive gate
is framed as a MATERIALITY floor for continued investment, not an Elo
prediction. +$500 sits just below DEV-005's +$797.76 — the largest
credible development signal on record — and at the DEV-006 qual point
estimate (+$517.58): below it, even a significant effect is shelved as
scientifically interesting but competitively immaterial; at/above it
with clean tails, H1 earns an integration experiment. A large positive
mean WITH catastrophic tails (pattern F) is explicitly NOT competitive
success and NOT deployable (§24/I-4).

Neither gate licenses deployment: both require a future independent-
replication experiment before any live-submission decision (§24).

## §22. Integrity gates

Pre-execution (all must PASS in the execution session, same-session,
before the first experimental seed; any failure ⇒ STOP):

- G-HASH: recompute SHA-256 of the frozen baseline (`18402ec6…`), the
  frozen H1 implementation (hash pinned at implementation freeze, §24),
  and this protocol file; all match their freeze records.
- G-IMPL: static review of the H1 implementation passes P1–P10 (§5):
  whitelist-only emission, zero forbidden references (DEV checkpoint/
  valuation/registry, HORIZON*, advance/subtract, market-maker,
  defer, PLACE-in-proposals), overlay ordering R14, determinism §12.
- G-SIM: §11/Q1 unit battery 100% + §11/Q2 parity property (zero
  adoptions on disagreeing trajectories) demonstrated on consumed
  cohorts + P-DET double-run bit-identity (§12).
- G-ENG: §11/Q3 engine battery (port manifest + golden 47,520/47,520).
- G-QUAR: runner refuses (hard-abort, exit nonzero) any seed in:
  214200–214249 (virgin final holdout); 50000–50499, 50150–50199,
  60000–60049, 245000–245049, 246000–246049, 247000–247049,
  248000–248049, 50050–50099 (consumed/benchmark/quarantine);
  310000–310499 (DEV-007 RESERVED — unexecuted, must not be touched);
  410000–410499, 510000–510499 (DEV-007 conditional fallbacks);
  249000–249049, 250000–250049, 255000–255049, 260000–260049,
  300000–300049 (named reserved alternatives); and any seed outside
  320000–320499. Quarantine self-test (all listed ranges rejected, two
  in-cohort seeds accepted structurally) runs before the first game.

Per-game (computed by the runner; any violation ⇒ STOP the run and
investigate as a one-factor breach before any interpretation):

- P-PURE: (a) treatment/baseline actions bit-identical for all steps
  0–711 in every game (action-hash compare); (b) on non-activated games,
  bit-identical for all 719 steps (exact abstention); (c) on activated
  games, markets element-identical for all steps 712–717
  (markets-verbatim property); (d) Δᵢ ≠ 0 only on exposed seeds.
  (a)+(b) operationalize audit Tests A/G; (c) polices B1; (d) is the
  coherence check behind §21's D+C rule.

## §23. Stop rules

1. Execute exactly N = 500 seeds (320000–320499), 2 games each, then
   STOP. No more, no fewer.
2. No early stopping for any reason (positive, negative, exposure,
   runtime); no peeking-driven decisions of any kind (§19: statistics
   computed once, post-seal).
3. No seed replacement, resizing, extension, or substitution — including
   after a zero-activation outcome. A follow-up requires a NEW protocol.
4. No parameter, whitelist, guard, threshold, search-budget, sim, or
   treatment change at any point after implementation freeze.
5. Integrity-gate failure (hash mismatch, P-PURE violation, quarantine
   trip, parity failure) ⇒ STOP and investigate before any
   interpretation. Resumption, if ever justified, requires a written
   incident record + a protocol amendment with a new identity — never a
   silent restart.
6. No second experiment is authorized by this protocol (H1b market-rule
   variant, DEV-architecture transfer, and integration tests are named
   future protocols, §24).
7. Forensic plan (post-execution only): trace (money-trajectory replay,
   both arms, both seats) every exposed seed; every nonzero-Δᵢ seed;
   every |paired Δᵢ| ≥ $2,000 seed; every new minimum. Tracer consumes
   fixed seed lists from main-run telemetry and cannot alter cohort
   membership (mirrors DEV-007 §9). (F-TRACE)

## §24. Post-experiment interpretation rules + final section

### §24.1 Interpretation rules (frozen)

- I-1. Report the pair (mechanism pattern §21.1 + overall pattern
  §21.2). Never collapse to one score; never claim more than the pair.
- I-2. Causal language per §2 (activation endogenous; "conditional
  paired effect among prospectively defined activation-exposed
  episodes" only).
- I-3. No Qualification, Top-10, Elo, or Kaggle-superiority claim from
  this experiment under any outcome. This is a single-cohort mechanism
  test; deployment requires independent replication (future protocol).
- I-4. Tails dominate means: pattern F (or competitive-gate tail
  failure) renders any positive mean non-deployable, full stop. Large
  mean + catastrophic tails = scientific finding (B+F), not an asset.
- I-5. Scope honesty: every claim is scoped "H1 on V54++"; transfer to
  DEV-005/DEV-006 (different terminal physical states: 6C/11S herds vs
  9C/5S baselines) is untested and must not be implied.
- I-6. If SCIENTIFIC SUCCESS holds, the licensed next step is an
  integration experiment (H1 × then-surviving architecture), not
  deployment. If pattern B holds with a diagnosed cause, the licensed
  next step is H1b (single-cause redesign, new protocol). If pattern C
  holds, the licensed next step is exposure forensics (reason-code
  histogram diagnosis), not a bigger N with the same design.
- I-7. After execution, 320000–320499 becomes CONSUMED (quarantined for
  all future experiments); the fallback chain (§13) is retired unused or
  consumed per use — recorded in the execution manifest either way.

### §24.2 Unresolved items

- U-SEL detail: the §10.3 reason enum's ABSTAIN_ACCEPT sub-cause
  granularity (which conjunct of §8.1(5) failed) SHOULD be telemetered
  as structured sub-fields; exact sub-field schema is an implementation-
  freeze detail (must be frozen then, enum-stable: no new top-level
  codes ever).
- Audit U10 (activation prior): remains empirically open BY DESIGN;
  resolved by §18 telemetry, not by pre-freeze analysis. Not a blocker.
- Audit U11 (live-env parity): standing program caveat, unchanged.
- H1 runtime: UNKNOWN until implemented (P-PERF measures it); design is
  runtime-independent (§14.3).

### §24.3 Exact implementation prerequisites (all before any execution)

- P-IMPL: H1 implementation (whitelist D1, E=712, D3 identity market
  rule, search D4, dominance D5, ties D6, abstention D7, telemetry
  §10.3/§18) as a NEW file under a NEW path (never touching frozen
  artifacts); own freeze commit + SHA-256 recorded; passes G-IMPL.
- P-SIM: engine-exact shadow sim + frozen unit-test battery passing Q1;
  Q2 parity property demonstrated on consumed cohorts.
- P-DET: double-run bit-identity proof + pinned interpreter versions.
- P-PERF: measured planning/game runtime on consumed cohorts (for
  session planning only; no design dependence).
- P-RUN: execution runner (exact cohort constants, G-QUAR guards,
  2-games/seed CRN, §18 telemetry incl. reason codes, P-PURE checks,
  zero outcome-dependent logic), frozen in its own commit with this
  protocol's hash re-verified — mirroring the DEV-007 runner discipline
  (DEV-007 PROTOCOL.md §13).

### §24.4 Freeze verdict

`FREEZE-READY`

Rationale: D1–D8 are all frozen with recorded justifications; all 24
sections are present with exact values, formulas, bars, enums, and
gates; the cohort rule is outcome-independent with provenance certified
(§13); N is justified by exact arithmetic (§14); no value awaits results
(no results exist); every remaining unknown is either a frozen telemetry
question (U10→§18), a standing program caveat (U11), an implementation-
freeze detail with a fixed schema rule (U-SEL), or a measured-not-
assumed quantity (P-PERF) — none of which can change any frozen value
above. The D8 counterfactual is recorded (§3.2) so the baseline choice
is auditable.

### §24.5 Exact next artifact required

The H1 IMPLEMENTATION + shadow sim + validation battery + freeze record
(§24.3/P-IMPL…P-DET), as new files under new paths, reviewed against
G-IMPL/G-SIM, committed separately. Then the runner (P-RUN). Then
execution. Protocol hash + freeze-commit identity are recorded in the
implementation-freeze manifest (this protocol's SHA-256 is computed at
the freeze commit; the freeze commit must predate all P-* work — any
implementation text predating the freeze commit is disqualified from
the frozen implementation).
