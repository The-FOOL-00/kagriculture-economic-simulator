# V32 P3 STEP-0 WASH REPORT (G3)

Runner: `scripts/v32_p3_step0.py` → `results/v32_p3_step0_report.json`.
Population: all 240 step-0 seat-rows (60/teacher; inputs bit-identical across
legs — verified `maxdiff=0.0`; labels = 4 teacher wash qty-literals).

## 1. Probe results (dedicated step-0-only training, 600 epochs, LR 3e-4)

| Probe | wash shape | exact literal | detail |
| :--- | ---: | ---: | :--- |
| A7-only (60 samples, 1 label) | 60/60 | 60/60 | full-action 100% from ep475 (sudden flip after plateau; LR 3e-3 fits by ep75 — LR-scale slowness, not unlearnability) |
| Mixture (240 samples, 4 labels) | 240/240 | 60/240 | consistent single-pattern choice (V3's [BUY50,SELL50]) from ep125; exact=60/240 is the UNIDENTIFIABLE-input optimum (one output can match only one teacher). Stable plateau; one argmax flicker at ep599 (full 0.25→0.0 for one eval) — reported, not hidden. |

Metrics: wash-shape = M0/M1 are `[BUY_PRODUCT,WHEAT,n>0],[SELL,WHEAT,m>0]`;
exact = decoded market literals equal targets (don't-care slots excluded —
fixed during P3 after a metric bug compared unsupervised NOOP-slot item/qty).

## 2. G3 verdict: PASS (representation can express and learn the opening wash)

- P2's pointer NEVER memorized 60 identical step-0 samples (argmax stuck
  all-NO-OP). P3's head memorizes them fully (A7 60/60 exact) and learns a
  valid consistent wash under mixture (240/240 shape).
- The mixture exact-literal ceiling (60/240) is information-theoretic
  (identical inputs, 4 labels), not a representation failure.

## 3. Full-BC checkpoint eval (G3 on the trained BCs)

| Checkpoint | wash-shape | exact | step-0 argmax (all 240 inputs) |
| :--- | ---: | ---: | :--- |
| mixture @3e-4 | 0/240 | 0/240 | `[SELL,WHEAT,30],[BUY_PRODUCT,WHEAT,30]` (reversed wash, A7's qty) |
| mixture @3e-3 (AMEND-1) | 0/240 | 0/240 | identical reversed wash (slot-0 P(SELL)=0.81) |
| A7-only @3e-4 | 0/240 | 0/240 | `[],[]` (all-NOOP — underfit) |

G3 on full BC: FAILS. All BC variants miss the opening wash in closed loop
(the dedicated-probe PASS in §1 shows the representation CAN express and learn
it in isolation — the failure is rare-sample joint-training dynamics, §22
market error class). G3-overall: PARTIAL (representational PASS, BC FAIL).
