# V32 P7 — ARM 0 BASELINE REPRODUCTION (P6 ARM 2 + SEMANTIC MASK)

## 1. REPRODUCTION VERDICT: EXACT

Checkpoint `results/v32_p6_arm2_rebalanced.npz` (P6 Arm 2) + exact semantic mask,
evaluated with the P7 screen harness (`scripts/v32_p7_eval_screen.py`, same
`MaskedPredictor` inference path as P6) on the identical 120-leg screen
(249675–249684 × 6 opponents × 2 seats) → `results/v32_p7_eval_arm0.jsonl`.

| Metric (120 legs) | P6 reported | P7 Arm 0 | Match |
|:---|:---:|:---:|:---:|
| Step-0 wash (shape) | 100% | 100% | yes |
| Step-0 PASS | 100% | 100% | yes |
| Step-1 NORTH | 100% | 100% | yes |
| Step-1 hires mean | 5.00 | 5.00 | yes |
| Step-2 SOUTH | 100% | 100% | yes |
| Step-2 PICKUP | 0% | 0% | yes |
| Median first action divergence | Step 3 | Step 3 (120/120) | yes |
| Terminal cash mean | $0.07 | $0.07 | exact |
| Terminal cash median | $0.00 | $0.00 | exact |
| Win rate | 0% (0/120) | 0% (0/120) | exact |

## 2. P7-EXTENDED BASELINE METRICS (NEW)

| Metric | Arm 0 value |
|:---|:---|
| Step-0 wash ORDER-correct | **0/120 (0.0%)** — universal SELL-first flip |
| Step-3 PICKUP SHEEP | 0/120 (step-3 op = SOUTH 120/120) |
| Prefix-exact P4 (farmer / full-native) | 0% / 0% |
| Prefix-exact P8 (farmer / full-native) | 0% / 0% |
| Opening-macro survival | 0/120 (all fail at `pickup_sheep@3`) |
| t_act_farmer (median) | 3 (120/120) |
| t_act_full (median) | 0 (wash order/count literals differ at step 0) |
| t_state, P5 money-inclusive (median) | **1** (120/120; wash-bleed cash gap) |
| t_pos, position/hands-only (median) | **4** (120/120; first physical dislocation) |
| t_econ (median) | **1** (120/120) |
| State distance 0–8 (mean) | 0.000 → 0.037 → 0.022 → 0.045 → 0.079 → 0.129 → 0.179 → 0.187 → 0.242 |

## 3. DIVERGENCE-CONVENTION NOTE (P6 vs P7)

P6 reported "t_state = 3, t_econ = 3". P7's paired measurement gives t_state = 1,
t_econ = 1, t_pos = 4. Both are true under different conventions:

- P6's trace table itself shows the cash gap at step 1 ($2,040 vs $3,000+); its
  "step 3" figures use **action-step indexing** (= P7 `t_act_farmer` = 3).
- Under P5's literal money-inclusive state definition (|dMoney| > 1 / 10), the
  wash-order cash bleed forces t_state = t_econ = 1 on all 120 legs.
- Physical dislocation (position/hands) first appears in the step-4 pre-action
  state (consequence of the step-3 action): t_pos = 4.

P7 reports all conventions explicitly; the H1 test tracks t_act_farmer (3 → ?),
t_pos (4 → ?), and the state-distance trajectory.

## 4. NEW FORENSIC FINDING: UNIVERSAL SELL-FIRST WASH (ORDER PATHOLOGY)

The P6 policy emits `[SELL WHEAT 30, BUY_PRODUCT WHEAT 30]` (SELL-first) on all
120 screen legs AND on all training seeds probed (249635/249636/249647):

- P6's own order-sensitive probe on its own checkpoint: **s0_wash = 0/240** (the
  checkpoint's saved `meta.probe` also records `s0_wash: 0`). The 120/120 screen
  wash claim used the order-insensitive shape metric, which passes both orders.
- Causal isolation (fixed step-0 market, seed 249675 vs E0_V3): BUY-first wash →
  cash $3,054 at step 1 with no stranded goods (true wash, +$54); SELL-first wash
  → cash $2,040 with 30 wheat stranded in the shed (−$960 level, **−$1,014 vs
  BUY-first**).
- Paired P6-vs-teacher trace: policy $2,040 vs teacher $3,054 at step 1
  (dM = −$1,014); policy $468 vs teacher $1,106 at step 2 (dM = −$638 after the
  step-1 SELL-13 partially liquidates stranded wheat).

Interpretation: the capital trap has TWO components — (a) a ~$1,014 step-0
wash-order bleed (market-head pathology, order-sensitive market semantics), and
(b) the step-3 livestock skip → wage drain (farmer-trajectory failure). P7 prefix
supervision targets (b); the prefix-4 window also covers step-0 market heads, so
any wash-order side effect will be measured, but P6's λ_crit = 50 market CE
already failed to fix the order (0/240), so no wash repair is assumed.

## 5. CONTROL SUMMARY

Arm 0 = exact P6 reproduction with extended P7 instrumentation. All downstream
P7 arms compare against §1–§2. First-divergence reference: live E2_A7 replay in
the learner seat (valid because all four teachers share the identical 0–24
farmer prefix; see `V32_P7_PREFIX_DATASET.md` §2).
