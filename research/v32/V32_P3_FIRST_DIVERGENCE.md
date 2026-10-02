# V32 P3 FIRST DIVERGENCE (mixture BC)

Runner: `scripts/v32_p3_divergence.py` (BC rollout + all 4 teachers queried on
the learner's exact observation each step). Records:
`results/v32_p3_divergence.jsonl` (249675–249676 × E2_A7 × seat 0; pattern
confirmed identical on both legs and consistent with all-240 step-0 argmax).

## 1. First divergence: step 0, market slot-order, vs ALL teachers

| Leg | BC cash | opp cash | div E0_V3 | div E2_A7 | div E6_W72 | div E7_W2015 | novel |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 249675 s0 | $881 | $143,817 | step 0 | step 0 | step 0 | step 0 | step 0 |
| 249676 s0 | $887 | $142,498 | step 0 | step 0 | step 0 | step 0 | step 0 |

Differing slots at step 0 (both legs, all teachers): ONLY
`mkt0-op:SELL-vs-BUY_PRODUCT` and `mkt1-op:BUY_PRODUCT-vs-SELL`.
Farmer and hands actions MATCH every teacher at step 0 (no unit diffs) —
all 4 teachers share identical step-0 unit actions and BC reproduces them.

BC step-0 market: `[[SELL,WHEAT,30],[BUY_PRODUCT,WHEAT,30]]`.
Teacher step-0 markets: V3 [BUY50,SELL50], A7 [BUY30,SELL30],
W2015 [BUY20,SELL15], W72 [BUY7,SELL2].

## 2. Classification (§22): market error (slot-order confusion)

- NOT representation ambiguity (codec exact; heads can express the wash —
  dedicated probe proves it).
- NOT no-op/hand/parameter/temporal-feature error (units match; qty=30 matches
  A7; state features expose step-0 distinctly).
- NOT simulator integration bug (execution identity holds).
- It is an ACTION-HEAD error of slot assignment: the shared market head emits
  the global slot mode (M0≈SELL) instead of the unanimous step-0 supervision
  (M0=BUY ×240/240). Rare-sample + shared-head dynamics, fixable by
  optimization (LR3e-3 arm tests this), not by resampling (forbidden) or
  architecture (not yet indicated).

## 3. Economic consequence

M0 SELL on the empty step-0 shed commits 0 units (void); M1 BUY 30 executes at
post-opponent-buy inflated prices (opponent washes BUY-first). Capital −~$750
into shed wheat with no wash proceeds; the policy never recovers the wash
mechanism and drifts (terminal $881–887 vs $143k). First-divergence forensics
for the LR3e-3 arm to follow if its wash is fixed.
