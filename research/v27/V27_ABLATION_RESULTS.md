# V27 — ABLATION RESULTS (exploratory, consumed seeds)

Design: V27_ABLATION_PLAN.md (plus A7, added to complete the qty ×
init square — see §5). 1080 matches, hermetic adapters, 60 consumed
seeds × 2 seats. Data: `results/v27_ablation_matches.jsonl`;
stats: `results/v27_ablation_stats.json`; action-stream deep-dive:
`results/v27_ablation_deepdive.json`. All claims EXPLORATORY
(consumed seeds); nothing here promotes any variant.

## 1. Sanity gate: PASS

V3S-vs-V3 reproduces `v27_farm_gaps.jsonl` **120/120 EXACTLY**
(per-seat rewards). The variant harness is validated: A1–A3/A7 reads
are causal for their flags.

## 2. Full table (§29: complete, no cherry-pick)

Seed-clustered 95% CIs (n=60 seeds). Δ = variant − V3 (or variant − P3
for direct).

| Config | Mean | Median | SD | Seed CI | W/L/T |
| :--- | ---: | ---: | ---: | :--- | :--- |
| A1-vs-V3 (V3 open+disp) | +7.2 | 0.0 | 897 | [+1.7, +14.0] | 16/6/98 |
| A2-vs-V3 (50-bypass+disp) | −1,543.0 | −1,477.5 | 1,350 | [−1,784, −1,316] | 5/115/0 |
| A3-vs-V3 (30-bypass, no disp) | +49.6 | +213.5 | 2,081 | [−397, +632] | 69/51/0 |
| A7-vs-V3 (30-call, no disp) | **+1,450.8** | +1,286.0 | 1,607 | [+1,181, +1,896] | **119/1/0** |
| V3S-vs-V3 (= V3) | 0.0 | 0.0 | 896 | [0, 0] | 6/6/108 |
| A1-vs-P3 direct | −49.6 | −213.5 | 2,081 | — | 51/69/0 |
| A2-vs-P3 direct | −1,450.4 | −1,286.0 | 1,626 | — | 1/119/0 |
| A3-vs-P3 direct | −7.2 | 0.0 | 989 | [−13.9, −1.8] | 6/16/98 |
| A7-vs-P3 direct | +1,543.0 | +1,477.5 | 1,350 | [+1,316, +1,776] | 115/5/0 |
| P3-vs-V3 (reference) | +59.9 | — | 2,126 | [−397, +632]-ish | 69/51/0 |

Paired variant-minus-P3 (common V3 baseline, same seed/seat):
A1 −$53 [−650, +402]; A2 −$1,603 [−2,161, −1,145]; A3 −$10 [−18, −4];
A7 +$1,391 [+1,113, +1,687]; V3S −$60 [−647, +385].

## 3. The additive decomposition (fits all 9 cells, residuals <$100)

| Factor | Estimate | Evidence |
| :--- | ---: | :--- |
| 30-qty (vs 50) | **+$1,500 ± $100** | P3−A2 +1,603; A7−A1 +1,444 |
| step-0 init (call vs bypass) | **+$1,450 ± $100** | A1−A2 +1,550; A7−P3 +1,391 |
| dispatch (12 late waters) | **−$10..+$7 (≈ $0)** | A3−P3 −10 [−18,−4]; A1−V3S +7 [+2,+14]; A3-P3 direct 98/120 exact ties |
| farm | 0 (54/60; two outliers) | V3S 108/120 exact ties |

- P3 (30/bypass) vs V3 (50/call) = qty(+1,500) − init(−1,450) + disp(0)
  ≈ **+$60** ✓. P3's bypass throws away $1,400 of step-0-init value
  while its 30-wash gains $1,500. Net ≈ zero by cancellation, not by
  absence of effects.
- A2 (50/bypass) = −init(−1,500) ≈ **−$1,543** ✓. The 50-wash without
  V3's step-0 processing is toxic (loses 96%).
- A7 (30/call) = qty(+1,500) + init(kept) ≈ **+$1,451** ✓✓. The
  discovery of V27: V3's processing + 30-wash keeps both.
- Direct cells confirm: A1−P3 = −qty+init ≈ −$50 ✓; A2−P3 = −qty ≈
  −$1,450 ✓; A7−P3 = +init ≈ +$1,543 ✓.

## 4. Mechanism anatomy (action streams + timing)

- **Init does NOT change the route.** A3-vs-A7 unit streams identical
  all 719 turns; init's +$1,400 flows entirely through LATE REACTIVE
  MARKET decisions (first market divergence t=433 at 30-qty, t=252 at
  50-qty). V3's step-0 processing calibrates market-state (reservations/
  horizons); starting cold post-wash misfires late sells. (V3's step-0
  market is exactly [BUY50, SELL50] on all 200 trajectories — no
  frontload orders exist at step 0, so the init effect is purely
  internal-state calibration, not skipped orders.)
- **Qty flows through market-path + fills.** A1-vs-A7 (qty only):
  market differs at t=0 (wash), units part at t=153, post-wash market
  ORDERS identical — yet $1,286 apart: same orders FILL differently
  (inventory/price cascade from the wash path).
- **Dispatch fires 92% late** (WATER gap by phase: early 0.0 / mid +1.3
  / late +11.0 over 120 matches; first fire ~t=340 on 249431). Late
  waters on decided yields = inert (±$10). V25's "early in-place labor"
  narrative is refuted on timing alone. DIG net 0 (tape digs on
  schedule).
- **249463 tip needs the opening, not dispatch:** A1 0/0 (no tip),
  A3 +13,053/+13,026 (tip intact), P3 tips. Combined with CF-1's $31-
  miss gate: P3's opening-induced trajectory clears the gate; A1's
  does not. (Opening NECESSARY here; the $881 lead is trajectory-
  reshaping, not +$108 additive.)
- **P3's opening is a lottery ticket:** A1-vs-P3 direct = −$50 overall
  but +$171/leg excluding 249463 (V3's opening wins 118/120 legs;
  P3's wins $26k on 2 legs). Typical value −$170; tip value +$13k
  (1/60 seeds). Net ≈ $0 ± lottery.
- **249450 farm invariance holds:** all variants show the ±$7k farm
  pattern (A1 +6,977/−6,809; A2 +6,438/−8,497; A3 +202/−5,090; V3S
  ±6,893). A3/P3 mitigate the bad farm by ~$1.8k (opening cash);
  A2 worsens it by $1.6k (qty story in all contexts).

## 5. A7 addendum (post-plan variant, fully documented)

A7 (30-call: V3 called at step 0, wash orders resized 50→30 under an
exact-shape assertion) was added after A1/A2/A3 to complete the qty ×
init square — the plan's 2×2 had an empty cell and the A2 toxicity
demanded the control. Coherence: V3's step-0 processing runs
naturally; only two order quantities change; downstream state evolves
from true engine observations (same coherence class as P3's bypass).
Rewrite fired on all 240 A7 matches (money1 = 3054/2946 everywhere;
no unexpected-shape flags). A7 is a V27 DISCOVERY (exploratory,
consumed seeds, post-hoc selected): it must NOT be promoted without a
fresh-seed V28 confirmation. It is, however, the single
highest-information next experiment (7σ on 60 seeds cannot be luck;
mechanism systematic with 119/120 wins).

## 6. Brief-ID resolution (§15)

A1 RUN (opening → V3: kills the tip, −$53 net); A2 RUN (qty → 50:
−$1.6k, toxic); A3 RUN (dispatch → V3: −$10, null); A4/A5/A6 NOT
APPLICABLE (no such P3 code — evidence: ledger §4; A1+A3=V3S covers
"remove everything"). A7 ADDED (completes square; +$1,451 discovery).
"No single mechanism explains it" is REJECTED: two large mechanisms
(qty, init) + one null (dispatch) explain everything additively.
