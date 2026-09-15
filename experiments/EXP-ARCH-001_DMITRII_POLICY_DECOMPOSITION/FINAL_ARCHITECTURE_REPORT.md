# FINAL ARCHITECTURE REPORT — EXP-ARCH-001

## 1. What Dmitrii is (one paragraph)

Dmitrii plays ONE agronomic economy — day-0 melon+livestock blast,
wheat feed loop, strawberry waves, 16–17 head with daily feed/care/
collect, land at day 6/11, late carrots — through 12 route/sales
permutations selected once at step 144 by a YARN-only shop-pair map
(49 of 64 pairs share the default), converged forcibly to a shared
harvest tail at step 648, executed open-loop with two micro-repairs
(same-day weed DIG queue; one-turn sale advances with next-turn
subtraction), and closed by a 7-turn exact-simulation optimizer that
adopts worker re-routes only under row-wise physical dominance and
abstains on any of 10+ guard failures.

## 2. Phase 8 verdict: E (B + C + D) — with evidence

Not A ("precompute everything"): the tapes do NOT cover what happens
— repairs fire on live weeds/prices every game (`repair_weeds` queue,
`advance_sales` price/stock checks), the 718 action is recomputed
from live state, and the terminal optimizer re-plans workers from
live physical state. Pure precomputation would have none of this.

B ("select a robust macro plan early, avoid switching") — SUPPORTED:
one write at 144 (`Policy.act`), never revisited despite 6 later
reveals; all 13 tapes share one skeleton so any choice is
"robust" (identical PLANT tables, 16–17 head, same land/workforce);
DEV-005/006's loss class (late-transition cascades) is
structurally impossible here.

C ("reactive local repair around a fixed macro plan") — SUPPORTED:
`repair_weeds` (same WHAT/ORDER, shifted WHEN), `advance_sales`/
`subtract_advanced_sales` (same quantities, shifted one turn),
terminal `_recover_observed` (same markets, position-free salvage).
Each repair is bounded (one day / one turn / carried cargo) and
preserves a stated baseline invariant.

D ("shadow simulation only for short horizons where accuracy is
guaranteed") — SUPPORTED: the optimizer simulates exactly 7 turns
with no RNG, no day boundary, no opponent-dependent physics, fixed
clearing markets, frozen prices — and converts residual price risk
into a units-dominance certificate the opponent cannot break
(`dominates` + no-steal + acceptance conjunction). The 648
convergence exists to feed this window a compatible baseline.

E is the conjunction actually implemented: B chooses WHAT economy to
run, C absorbs physical violations of the open loop, D squeezes the
exactly-modelable tail. Removing any leg breaks the stool: without B
there is no stable baseline to repair/optimize around; without C the
open loop dies on first weed contact; without D the tail leaves
stranded cargo (our Audit: Dmitrii wins pure-Straw seeds there).

## 3. The transfers, ranked (from TRANSFERABILITY_MATRIX + HYPOTHESES)

Interface-clean now: dominance-gated terminal reaper (H1),
advance/subtract sales (H2), dominance veto on entry (H3),
fertilizer cash-crop audit (H4). Architectural simplifications to
test: single checkpoint (H5), forced 648 tail (H6), YARN-only
registry (H7), wool cadence (H8). Economy tweaks: late carrots (H9),
day-0 intensity (H10), goose hedge (H11), tomato strip (H12).
Do not port: their search residue (H16–H17), their exact map (H15),
late-info blindness (H18).

## 4. Strongest single finding

Action-distant tapes are economically identical: pairs differing in
504/504 steps agree to ~90% on daily operation mix with IDENTICAL
planting tables. "13 strategies" is a misnomer — it is 1 economy ×
12 executions. The shop router's entire economic content is: more
sheep + no geese + harder wool clearing when YARN appears early.
Everything else is path variation the search happened to keep.

## 5. Strongest caution

Nothing here proves ANY Dmitrii choice optimal — not 144 over 72/216,
not YARN-only over richer conditioning, not forced-648 over
plan-specific tails. The bot's strength is evidence FOR the bundle
(B+C+D + one good economy), not for any clause. Each transfer needs
its confirmation experiment (HYPOTHESES.md); several (H5, H18) already
face contradicting evidence from OUR wins.

## 6. STOP

Architecture report complete. No hypothesis has been turned into an
experiment. No candidate written. No V54++/DEV/holdout artifact
modified. No Kaggle contact. Awaiting independent review before any
next performance experiment is chosen.
