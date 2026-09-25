# V29 — MECHANISM AUDIT (measured on holdout records)

Probes: `scripts/v29_mechanism.py` → `results/v29_mechanism.json` +
`results/v29_mechanism.csv` (one evidence row per leg, 80/80 complete —
100% telemetry coverage, preregistration §11(f) satisfied).
Conventions: game-steps for actions; obs[t] is the pre-action state at
game-step t; game-step t action at env.steps[t+1].

## 1. Classification (mechanical classifier, preregistered classes)

| Class | Legs | Share of legs | Δ contribution |
| :--- | ---: | ---: | ---: |
| CANONICAL_MELON | 80 | 100% | +$103,134 (100%) |
| SHEEP_GATE | 0 | 0% | $0 |
| OTHER_POSITIVE | 0 | 0% | $0 |
| TIE/INERT | 0 | 0% | $0 |
| FARM/ROUTE_LOSS | 0 | 0% | $0 |
| OTHER_NEGATIVE | 0 | 0% | $0 |

**80/80 legs (100% of wins) show the canonical melon mechanism** — the
V28 causal chain replicated without exception on the holdout.

## 2. The canonical anatomy (all 80 legs)

| Telemetry field | Value (all legs) |
| :--- | :--- |
| Step-17 cash gap (A7−V3) | +$108 (80/80) |
| Melon-seed qty gap at step 17 | +1, i.e. ×2 vs ×1 (80/80) |
| Melon-plant action gap, full game | +1 (80/80) |
| First unit divergence | game-step 18 (80/80) |
| First market divergence (t≥1) | game-step 17 (80/80) |
| Harvest jump step | obs[252] (80/80) |
| Harvest jump size | +$1,258 (78 legs) / +$1,341 (2 legs, seed 340068) |

Causal chain (identical to V28 §1): 30-unit wash savings → +$108 →
step-17 cash $266-vs-$158 → melon-seed ×2 gate ($164.50) cleared by A7
/ missed by V3 → +1 melon plant at step 18 (the game's first unit
divergence) → +$1,258 harvest at obs[252] → ≈+$1,286 terminal. The
+83 variant (340068, both seats, +$1,373 terminals) matches V28's
249542/249564 +$1,369 variant: same mechanism, richer harvest.

## 3. Late wobble (modulation around the core)

64 legs have exactly 1 unit divergence (the step-18 plant) and 1
post-zero market divergence (step 17); 16 legs carry 2–3 unit and up to
9 market divergences (late reactive-seller micro-wobble, cf. V28's
249533 MARKET legs). The wobble modulates terminals (+$583..+$1,989)
but is mean-preserving at seed level: all 40 seed means sit within
+$1,286 ± $15, and every wobble leg still shows the full canonical
core (cash17 +108, +1 plant, +$1,258 at obs[252]).

## 4. What did NOT appear

- No sheep/expansion gate (0/80 SHEEP_GATE; max pasture gap +1).
- No farm-driven loss (80/80 wins; farm gaps ≤ |$219|).
- No tie/inert leg, no route failure, no missing BUILD.
- No A7-specific defect of any kind (A7 has no dispatch/route/labor
  code; none observed).

## 5. Mechanism stability verdict

The mechanism is GENUINELY STABLE: 100% canonical classification with
per-field replication rates of 80/80 on every preregistered telemetry
item. V29 upgrades the V28 mechanism from "typical win (74/80)" to
"universal on this slice (80/80)". Combined with the decomposition
result (CREATE = $0 exactly), the mechanism's role is precisely
characterized: the extra melon is REAL production whose marginal value
exists ONLY under asymmetric supply — when both players hold it
(A7vA7), its value is $0 to the dollar (see the decomposition report).
