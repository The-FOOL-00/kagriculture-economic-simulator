# V31R2 A8 SPEC — PRICE-GATED SELLING (A8-GATE)

Status: SPEC BEFORE CODE (V31R2 §19). No A8 code exists yet.
Date: 2026-09-22. Evidence: 82 A7 + 237 V22R1 live public episodes, all replays retrieved.

## 1. Actual live failure

A7 loses to low-volume ("trickle") sellers by large margins while
out-producing them by ~40x:

| Game | Opp (LB) | Opp sell vol | A7 sell vol | Delta |
| ---- | -------- | -----------: | ----------: | ----: |
| ep111876058 | shawenher (2320) | 2,889 | 118,368 | −$10,395 |
| ep111886277 | Fedor (1834) | 1,571 | 85,793 | −$14,189 |
| ep111863520-class | Marlubie (2003) | 85,787 | 85,645 | −$4,307 |
| V22R1 ep111906269 | JR (2431) | ~1,900 | ~90,000 | −$13,785 |

9 of A7's 32 public losses are vs opponents selling <4k units lifetime
(mean −$5.8k, total −$52k). A further ~17 flood-vs-flood losses
(mean ~−$1.6k) share the same root cause (below). Only ~6 losses are
flat wash-ledger mirrors (−$34..−$205).

## 2. Affected opponent family

V3-clone programs (identical seeds/animals/hires/timing to V3 within
±2%) with small-quantity sell policies, concentrated in washes
20/15, 7/2, 5/5, 5+seed, 10/10, at live ratings 1800–2450.
Same family beats V22R1 (AEC) identically — AEC's market timing does
NOT address this.

## 3. Exact mechanism (engine-verified)

`kaggriculture.py` (1.32.7, live-confirmed): SELL fills immediately at
`market_price(item, shared_inventory)`; each sold unit raises shared
inventory; town drains on 4/24-step ticks; FERTILIZER has NO town drain.
Above-I0 shapes are brutal (MELON sq×3.6 T=300: +300 units → $1).

A7/V3/V22R1 dump ~85–130k units/game: every dump crashes its pool to
~$1 and A7 sells INTO its own crashes. Realized live prices (A7):
$0.1–$1.8/unit across all products. Trickle opponents sell 1–17
units/step into town-recovered pools at $26–$162/unit (50–400x).
Revenue efficiency: A7 ~$1.2/order-unit vs trickler ~$55/order-unit.

## 4. Why A7 fails

V3's market policy ranks WHICH product to dump but never asks WHETHER
to dump. Against flood-mirrors (V3-regime, naren_v-type) both sides
split crashed pools evenly and A7's +$1,286 wash-ledger edge decides
(confirmed live 4–6x). Against tricklers, the ledger is irrelevant:
A7's own floods destroy its revenue while the trickler skims recovered
prices. 26 of 32 A7 losses are second-half collapses (ahead or tied at
step 252, e.g. +$2,823 → −$6,319 vs carbonapi).

## 5. Proposed change (ONE mechanism)

A8-GATE = frozen A7 + price gate on SELL orders:

- For each SELL order (product P, step t>0): emit iff
  `market_prices[P] >= BASE[P] * F`, else drop the order (goods wait
  in shed for a later window).
- F = 0.5 pilot value (ONE knob; no per-product tuning in E1).
- EXEMPT: step-0 wash (keep A7's +$1,286 signature exactly);
  FERTILIZER (no town drain → gate would clog shed with unsellable
  stock; always sell as A7 does).
- No unit/labor/route/crop/livestock/land/market-buy change.

## 6. Why it should address the failure

The gate converts A7 from flooder to trickler: sells only into
recovered pools, automatically times post-drain windows, dodges
opponent floods (skip while crashed), and keeps per-unit prices near
base instead of ~$1. Expected to recover most of the −$5.8k mean
trickle deficit and part of the flood-vs-flood deficit.

## 7. Why it should not destroy validated behavior

- Step-0 wash untouched → +$1,286 vs 50-wash preserved structurally
  (E1 verifies GATE vs V3 margin).
- Gate only DROPS sell orders; buys/hires/units/crops identical, so
  production paths match A7 until shed-pressure diverges.
- Risk noted: shed cap 100 + holding → DROP-overflow destruction of
  held goods; fertilizer exempted to bound clog; E1 measures net.

## 8. Expected live benefit

If E1 replicates live scale (GATE beats A7 by ~+$5–15k locally):
flips most trickle-losses to wins (+9 games ≈ +11% win rate) and
narrows flood-losses. Rating effect directionally positive; no
numeric 3000 claim (V31R2 §25).

## 9. Falsification criterion

E1 (preregistered below) FAILS A8-GATE if, on virgin seeds
249591..249600 mirrored (20 legs) vs A7: W ≤ L, or mean delta ≤ $0,
or GATE-vs-GATE collapses (both-clog pathology), or GATE loses A7's
vs-V3 signature by >$1,286 (i.e. GATE vs V3 mean < +$1k).
Any fail → no A8 packaging; fall back to OPTION 1/2/4 per evidence.

## 10. E1 preregistration (fast validation) — EXECUTED, FAILED

E1 ran 2026-09-22 on preregistered seeds (50 + 8 legs):
- GATE vs A7: 0-20, mean −$36.9k
- GATE vs V3: 0-20, mean −$32.3k
- GATE vs GATE: 1-0-9 at $52–75k absolute (BELOW V3 self-play $101.6k)
- GATE vs V22R1: 0-8, mean −$34.1k

Verdict: A8-GATE FALSIFIED per §9. Price-gating destroys value: holding
goods pins the shed at cap 100 and subsequent DROP overflows are
DESTROYED by the engine (`del inv[item]` unconditional). Local fill
instrumentation further showed A7's 130k-unit SELL orders are 99%
phantom (1,608 real fills/mirror at $62/unit) — pools are NOT
flood-crashed; the "flood" premise was wrong.

## 11. E2 amendment — SPLIT (within-order erosion hypothesis)

Revised mechanism: A7's TAIL of 1000-qty SELL orders self-erodes price
WITHIN the order (unit-by-unit lockstep over full shed drains), while
tricklers' 1–17-qty orders capture top-of-pool. E2 tests truncation
WITHOUT price-holding: each SELL order qty capped at K=10 units
(remainder stays in shed but drains continuously — mild holding only).
Step-0 wash exempt (keeps +$1,286). ONE knob K.
- Seeds: virgin 249605..249614 mirrored.
- Legs: SPLIT vs A7 (20), vs V3 (20), vs SPLIT (10).
- PASS bar: SPLIT vs A7 ≥ 14/20 W with mean > +$3k.
- RESULT (E2, 50 legs 249605..249614): SPLIT vs A7 0-20 (−$3.1k);
  vs V3 0-20 (−$1.7k); self-play ties at $71–72k (below V3 $101k).
  E2 FAILED. Sell-side 0-80 across GATE+SPLIT. Shed-clog/destruction
  dominates any erosion benefit. SELL-SIDE ABANDONED.

## 13. E3 amendment — wash-size matrix (opening-cash-cascade hypothesis)

Revised mechanism: trickle families' SMALL washes (20/15, 7/2, 10/10,
5/5) commit less opening cash → different seed-buy thresholds
(shawenher +12 carrot seeds; carbonapi +2 tomato/+4 carrot/+1 goose) →
late-game production gaps of $2–14k. Same family as V29's melon chain,
opposite direction, larger scale. V29 NEVER tested 30-vs-small.
- E3: wash variants W72/W2015/W10/W5 (±SPLIT10) vs A7, 20 legs each,
  virgin 249615..249624 mirrored.
- PASS bar: a wash variant beats A7 ≥ 14/20 with mean > +$3k.
- RESULT (E3, 160 legs): W10 20-0 (+$594 mean, +$140 med); W2015 18-2
  (+$181); W5 18-2 (+$189); W72 18-2 (+$5). ALL below +$3k bar.
  wash+SPLIT: 0-80, −$6.5k..−$14k (catastrophic clog). E3 FAILED.
- E3b full 6x6 wash matrix (280 legs, 249625..249634): fully transitive
  W5>W10>W72>W2015>A7(30)>V3(50) but magnitudes $3–$307 (ledger crumbs).
  W5-vs-50 = +$140 (sacrifices A7's +$1,286 vs 50-wash). NO dominant wash;
  net live effect of any switch ≈ neutral-negative. MATRIX FAILS A8 bar.
- E6 (fert-cap) CONSIDERED AND SKIPPED: predicted E1-style shed-clog
  catastrophe (fert would pin shared shed-100); fert pattern confounded
  (wen: equal fert, −$9k via sheep-mix instead). Mechanism unproven.
- FAIL → OPTION 4 (sim-to-live mismatch) or OPTION 1/2; no A8.

## 14. A8 VERDICT — NO-BUILD (2026-09-22)

E1 (GATE 0-48, −$35k) + E2 (SPLIT 0-40, −$3k) + E3/E3b (wash crumbs,
no dominance) exhaust the one-line hypothesis space motivated by live
evidence. Remaining live gaps (livestock-mix, fert/feed micro,
sell-execution micro, Fedor-archetype crop strategy) each require
V3-internal policy changes (frozen bytes) with interacting
pasture/feed/cash/structure effects — banned by §21/§31 as A8.
NO A8 SHALL BE PACKAGED in V31R2. Decision: OPTION 1 (KEEP A7).

## 12. E1 preregistration record (kept for audit)

- Seeds: 249591..249600 (virgin; V30 remainder starts 249591).
  Protected 340090..340199, 214200..214249 untouched.
- Legs: GATE vs A7 (20), GATE vs V3 (20), GATE vs GATE (20),
  GATE vs V22R1 (8; slow agent). Both seats, mirrored.
- Primary: head-to-head W/L. Secondary: mean/median delta,
  realized-price ratio, flood volume.
- Harness: scripts/v31r2_gate_pilot.py (new; pool mode, 9 workers).
- PASS bar: GATE vs A7 ≥ 14/20 W with mean > +$3k.
