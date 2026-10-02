# V32 P3 CLOSED-LOOP REPORT (mixture BC → P3-SCREEN; LR3e-3 arm appended)

Runner: `scripts/v32_p3_evaluate.py` (deterministic argmax).
Panel: {E0_V3, E2_A7, E3_V25P3, E6_W72, E7_W2015, E8_DMITRII} (P2's 6).

## 1. Mixture BC @3e-4 on P3-SCREEN (249675–249684 × 6 opps × 2 seats, n=120)

Records: `results/v32_p3_eval_screen.jsonl`.

| Stat | P3 mixture-BC | P2 mixture-BC (P2-SCREEN) | A7 (P3-SCREEN ref) |
| :--- | ---: | ---: | ---: |
| mean terminal cash | $467 | $31 | $90,965 |
| median | $448 | $0 | $88,470 |
| stdev | $405 | — | — |
| min–max | $0–$1,243 | $0–$138 | $59,603–$142,499 |
| wins | 0/120 | 0/138 (seat 0) | — |

By opponent (mean): W72 $678, W2015 $658, A7 $448, V25P3 $432, DMITRII $315,
V3 $269. By seat: seat0 $485, seat1 $448 (no seat effect).

Step-0 market on all 120 legs: `[[SELL,WHEAT,30],[BUY_PRODUCT,WHEAT,30]]`
(the reversed wash — void M0 SELL on empty shed + M1 BUY at inflated prices).

## 2. Interpretation

Closed-loop economics are ~15× P2 BC ($467 vs $31) but still ~0.5% of expert
level ($467 vs $91k) with zero wins. The representation repair (market fidelity
0.80) converts into an order-of-magnitude economic lift but NOT nontrivial
stable economics: the step-0 slot-order error destroys the wash mechanism at
the first causally relevant decision (see first-divergence). G4 as prereged
("materially above P2 BC on majority of seeds") is MET numerically ($467 ≫
$138 on most legs) but the §29 spirit ("not explained by luck", "mechanism-
consistent") FAILS — the behavior is a broken wash, not a weak wash.

## 3. LR 3e-3 arm (P3-AMEND-1): higher fidelity, WORSE economics

Same 120-leg screen (`results/v32_p3_eval_lr3e3.jsonl`): mean $60, median $0,
stdev $322, max $2,829 (vs A7), 0 wins. By opp: A7 $204, W72 $78, V25P3 $55,
W2015 $16, DMITRII $5, V3 $0. Same reversed step-0 wash. Despite strictly
better supervised fidelity on every head (m_op-nn 0.90 vs 0.80, farmer 0.535
vs 0.468), closed-loop economics collapsed to P2-BC level — fidelity≠economics
when the critical pattern is wrong. This arm kills "more optimization of the
same kind fixes it" as a cheap hope: the wrong equilibrium is stable and LR
deepens it.
