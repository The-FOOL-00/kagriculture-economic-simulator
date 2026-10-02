# PHASE018 — STAGED/DEFERRED REPRESENTATION AUDIT (§24–§25)

**Status**: COMPLETE
**Date**: 2026-09-19

---

## 1. The seven audit questions

### Q1. How often would staged execution be required?

Blocked-promising tranche candidates (local > $50, macro-escalated, uncommitted,
safety-passing) in B2-S1: 43 instances / 20 matches (≈2/match), dominated by
`LIVESTOCK_FEED_RISK` wheat sales. "Required" (would flip the outcome): **0/6**
in the preregistered diagnostic sample — none.

### Q2. Are these states profitable under long-horizon continuation?

No. Staged variants (2 splits × 2 delays × 6 states = 24 counterfactuals) under
the frozen Phase016 evaluator: best staged ≤ lump in 5/6 states; the one
improvement (−52→−29) stays negative. Preregistered verdict rule (material
improvement in ≥3/6) → **0/6, FAIL**.

| State | Lump margin | Best staged | Verdict |
|---|---|---|---|
| 249323/0@290 WHEAT q13 | +16.0 | +13.0 | worse |
| 249323/0@290 WHEAT q5 | +12.0 | +6.0 | worse |
| 249322/1@251 WHEAT q12 | −52.0 | −29.0 | still negative |
| 249322/1@251 WHEAT q10 | −30.0 | −29.0 | same |
| 249322/1@291 WHEAT q8 | −3.0 | −5.0 | worse |
| 249322/1@291 WHEAT q5 | −4.0 | −5.0 | worse |

(Lump margins reproduced the ledger to the dollar — harness fidelity confirmed.)
The feed-hole economics are invariant to splitting: the wheat still leaves, the
terminal deficit persists. Negative results come from the opportunity, not from
lump-sum execution. `ORDER_QUEUE_ALTERATION` blocked cases were excluded by
mechanism mismatch (atomicity, not sizing — staging cannot help).

### Q3. Minimum state/action representation required?

Moot (diagnostic negative). Would-be: legs `[(q1,t1),(q2,t2),…]` + per-leg
preconditions (inventory/price/schedule gates) + explicit WAIT semantics.

### Q4. Can existing CoupledPatch express the intermediate state?

**Yes, structurally**: `actions[]` (per-turn joint actions), `steps[]` (per-step
market orders), `get_action_at_offset()`, pre/postconditions,
`shed_before/after`, `inventory_before/after`. Multi-step trajectories are
representable today.

### Q5. Does the executor support delayed commitments?

**Partially**: in-flight patch replay (`actions[offset]`) exists but is
worker-trajectory-oriented: market preconditions (inventory still held, price
still favorable) are never re-verified during replay, and there is no
deferred-leg scheduler. A staged market patch would replay blindly.

### Q6. Would staged execution interfere with V3 continuation state?

**Yes — two gaps**: (a) the macro probe covers only the step-0 mutation;
deferred legs would need multi-point boundary probing (else silent gate
crossings at t+k); (b) live in-flight replay can diverge from the simulated
continuation when between-leg V3 behavior shifts. Both gaps are load-bearing for
safety certification.

### Q7. Smallest representation extension?

`StagedMarketPatch`: legs list + per-leg precondition gates + multi-point probe
+ in-flight leg gating with abort. **NOT RECOMMENDED** — the diagnostic gives no
economic justification for building it.

## 2. Decision (§25 rule)

> "If staged candidates remain negative, do not build the machinery."

Staged candidates remained negative (0/6). **No staged-execution machinery will
be built. Outcome D rejected.** Representation is not the binding constraint;
single-step expression is sufficient for the opportunities that exist, and the
blocked opportunities are uneconomic in every temporal arrangement tested.
