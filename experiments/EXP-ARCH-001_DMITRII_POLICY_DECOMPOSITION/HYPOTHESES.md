# HYPOTHESES — classified, independently testable, no design

Discipline: "exists in a high-performing submission" ≠ "causes the
high performance". Every item states OBSERVED / HYPOTHESIS /
CONFIRMATION REQUIRED (smallest discriminating experiment). No item
may be combined into a candidate design in this phase.

## 1. DIRECTLY TRANSFERABLE (interface-clean, isolated test this week)

### H1. Dominance-gated 712–718 terminal reaper

OBSERVED: Dmitrii reaps +$X in the last 7 turns via exact sim with a
row-wise unit-dominance certificate, abstaining on any guard failure;
never changes markets 712–717 or the 718 rule.
HYPOTHESIS: our heuristic recall strands carried cargo and mature
yield that a dominance-gated reaper would convert with no-harm safety.
CONFIRMATION REQUIRED: audit OUR 712–718 stranded cargo/mature yield
on past replays (no new sims); then graft reaper-vs-recall on a fresh
Discovery cohort, backbone frozen.

### H2. Advance/subtract one-turn sales overlay

OBSERVED: Dmitrii pulls next-turn SELLs one turn early (excl.
WHEAT/FERT, price≥2, tick/unlock guards), conserving 2-turn totals.
HYPOTHESIS: sale latency + shed relief without deficit modeling beats
our preemption complexity on identical routes.
CONFIRMATION REQUIRED: same frozen backbone, advance/subtract vs V54
preemption, fresh Discovery cohort.

### H3. Unit-dominance veto on checkpoint entry

OBSERVED: Dmitrii's terminal adopts plans only under physical
dominance; our DEV-006 §14 shows the valuation model overvalues late
entry by ~$14k/seed.
HYPOTHESIS: a veto (enter only if projected terminal units dominate
backbone's) removes model-overvaluation losses without touching wins.
CONFIRMATION REQUIRED: DEV-006 vs DEV-006+veto on fresh seeds; count
vetoed entries + their counterfactual outcomes.

### H4. Fertilizer collect-and-drip-sell

OBSERVED: 17 free fertilizers/day fund Dmitrii's first revenue
(step 30) and most frequent SELL line (108 turns).
HYPOTHESIS: we leave fertilizer money uncollected (no FERTILIZER
reference in dev_004).
CONFIRMATION REQUIRED: audit OUR collect/sell rates + realized
fertilizer prices first; if collection <80% or sales ~0, run
backbone vs backbone+collect-drip on fresh seeds.

## 2. PROMISING BUT REQUIRES EXPERIMENT (needs modeling/work first)

### H5. Single checkpoint {144} vs four checkpoints

OBSERVED: one irreversible choice at 144; zero late-transition losses
by construction.
HYPOTHESIS: our 216/288 checkpoints add more cascade risk than
information value.
CONFIRMATION REQUIRED: DEV-006 capped to {144} vs full DEV-006, fresh
cohort. (Prior: our step-216 wins argue AGAINST — test decides.)

### H6. Forced 648 terminal-regime convergence

OBSERVED: all games converge to one shared 648–718 tail.
HYPOTHESIS: late-route divergence hurts more than plan-specific tails
help once planting windows close.
CONFIRMATION REQUIRED: DEV-006 with forced backbone tail from 648 vs
unforced, fresh cohort.

### H7. Registry pruning to {BACKBONE, YARN}

OBSERVED: Dmitrii conditions only on YARN; all 184 of our DEV-006
specializes were YARN_SPECIALIZED.
HYPOTHESIS: non-YARN routes add variance, not value.
CONFIRMATION REQUIRED: pruned vs full registry, fresh cohort; audit
non-YARN activations across all past cohorts first.

### H8. Wool cadence: drip vs clear-100 on YARN cohorts

OBSERVED: YARN plans clear wool x100 + x1000 bursts; default drips.
HYPOTHESIS: YARN's 2x sink absorbs bursts that would crash the thin
(T=105, sq) open wool market.
CONFIRMATION REQUIRED: fixed backbone+YARN herd, lots {drip-8,
clear-100}, YARN-heavy fresh cohorts (cohort must be YARN-dense to
have power — pre-register the filter).

### H9. Late carrot wave (days 24–27)

OBSERVED: 24–31 carrots on freed tiles, sold from step 670.
HYPOTHESIS: converts dead tile-time into cash.
CONFIRMATION REQUIRED: backbone vs backbone+fixed-carrot-wave, fresh
cohort; audit our days-24–27 tile/labor use first.

### H10. Day-0 deployment intensity

OBSERVED: 94.7% of starting cash deployed day 0.
HYPOTHESIS: earlier compounding beats our liquidity caution (or
reveals our optimal point).
CONFIRMATION REQUIRED: 3 fixed day-0 spend variants, fresh cohort.

### H11. Goose-diversified non-YARN herd (8C/6S/3G)

OBSERVED: default plan keeps 3 geese; YARN plans drop them.
HYPOTHESIS: eggs diversify non-YARN worlds where wool crashes.
CONFIRMATION REQUIRED: our baseline vs goose variant on pre-filtered
non-YARN fresh cohorts.

### H12. Tomato strip from PIZZA route

OBSERVED: zero tomato everywhere in 13 tapes.
HYPOTHESIS: tomato's joint-production burden (cows+wheat+daily
harvest+rot) exceeds its pizza-world value; milk+wheat-only pizza
keeps the upside.
CONFIRMATION REQUIRED: PIZZA-tomato vs PIZZA-no-tomato on
pre-filtered pizza-heavy fresh cohorts.

## 3. TOO COUPLED TO DMITRII (do not port without their substrate)

- H13. Route-permutation ensembles: requires their search harness
  generating 11 path-variants of one economy + tape executor. Our
  substrate is closed-loop routes; the port is "generate timing
  variants of our backbone" (see matrix §4) — a different, bigger
  project. CONFIRMATION would first need the variant generator.
- H14. t12 bulk seed buying: timing-coupled to t12's exact cash
  curve; copy-pasting quantities into our economy is meaningless.
- H15. Exact pair→plan map (e.g. (Y,PIZ)→6 sharing with (ICE,Y)):
  coupled to their route set; the portable content is "YARN-only
  conditioning" (H7), not the indices.

## 4. LIKELY OVERFIT (search residue; do not port)

- H16. Step-0/1 wheat round-trip, dead TOMATO/EGG/CARROT x1000s,
  `SELL x0`, `[]` slots, day-28 BUILD_COOP, pair-specific micro-diff
  blocks (e.g. t1/t5's 17 scattered steps). OBSERVED as bytes;
  HYPOTHESIS: search noise with ~zero effect (dead orders sell
  min(stock,·)=0). CONFIRMATION (if ever wanted): ablation deleting
  dead orders from a tape — but there is no reason to port them.
- H17. (YARN,YARN)→12 specifics: a 1/64 event's bespoke plan; the
  bulk-buying + 14-sheep/17-pasture mismatch smells of
  small-sample search. Treat t12's deltas as unconfirmed even
  within Dmitrii's own results.

## 5. NOT WORTH PORTING

- H18. Ignoring shops 3–8: contradicted by OUR step-216 wins
  (+$5.8k/+$8.7k); Dmitrii's 144-only rule forfeits them.
- H19. Hour-0 empty hands: forced by day-labor mechanics, not a
  portable choice.
- H20. Rewrites of history/awards: no version of "be more like the
  tapes" without the search that made them (see H13).

## Priority order for review (opinion, not design)

First: H4-audit (cheapest — replay audit, no sims), H1-audit (same),
then H2, H3, H8. Second: H5, H6, H7 (architecture simplifications
with real downside if wrong). Third: H9–H12 (economy tweaks).
Never in current form: H13–H20.
