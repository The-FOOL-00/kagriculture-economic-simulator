# V28 — COUNTERFACTUAL AUDIT (exact-state probes)

Method: `scripts/v28_counterfactual.py` → `results/v28_counterfactual.json`.
V26 backbone-aware snapshot/restore as a diagnostic instrument only
(no AEC, no mechanisms, no candidate change). Two methodological notes:
(1) the replay passes `env.configuration` exactly as `env.run` does —
V3's agent reads configuration (98 references) and passing None
silently diverges late reactive play; (2) probe steps are game-steps
(branch action taken AT the probe step from obs[probe]).

## CF-V28-1: the 249534/seat-1 expansion gate (game-step 289)

| Probe | Cash | Market action | Sheep |
| :--- | ---: | :--- | ---: |
| Live V3 (own state) | $9,916 | SELL FERT 17, SELL WOOL 3 | 0 |
| Live A7 (own state) | $11,948 | + BUY WHEAT 6, BUY_LAND, BUY SHEEP×6, HIRE×2 | 6 |
| V3-brain on A7-state | $11,948 | identical expansion bundle | 6 |
| A7-brain on V3-state | $9,916 | sells only | 0 |
| V3 + $521.73 injection | $10,437.73 | sells only (silent) | 0 |
| V3 + $522.35 injection | $10,438.35 | FIRES the bundle | 6 |

- Gate threshold bisected to <$1: **$10,438.35** — the same $10,438
  reactive sheep branch V27 characterized on 249463 ($10,438.02).
  Second independent observation of the same gate.
- V3 misses by $522; A7 clears by $1,510. Butterfly ≈ 23×
  ($12,087 consequence / $522 miss).
- Brain swaps prove the tip is 100% state-driven: either policy on
  the rich state fires; either policy on the poor state is silent
  (unsurprising — A7 ≡ V3 code after step 0 — but verified with
  exact active states rather than assumed).
- Fidelity: restore-and-continue reproduces the frozen terminal
  EXACTLY (108580, 120667); independent re-run bit-identical
  (threshold, bundle, terminals).
- Predicted (branch fires under injection): CONFIRMED. Realized
  terminal effect (+$12,087): observed in the frozen trajectory,
  reported separately, never equated.

## CF-V28-2: the typical-seed melon budget (game-step 17, 249530)

| Probe | Cash | MELON seed qty |
| :--- | ---: | :--- |
| Live V3 (own state) | $158 | 1 |
| Live A7 (own state) | $266 | 2 |
| V3 + $5.94 injection | $163.94 | 1 (silent) |
| V3 + $6.53 injection | $164.53 | 2 (fires) |

- The ×2 seed-budget gate sits at ≈$164.50. A7's wash savings clear
  it by ≈$101.50; V3 misses it by $6.53. The ENTIRE typical +$1,286
  effect pivots on this $6.53 miss — quantitatively tight, which is
  why the effect is both large and seed-stable (the wash arithmetic
  is deterministic, so the gate outcome is deterministic).
- Fidelity: restore-and-continue reproduces the frozen terminal
  EXACTLY (106557, 105271).
- Predicted (V3 buys ×2 under injection): CONFIRMED. Realized
  consequence (+1 melon plant → +$1,258 harvest → +$1,286): observed
  in the frozen trajectory.

## Causal-fidelity statement (§27)

Exact initial state ✓ (replay verified action-identical to env.run
through the probe step, terminals exact after restore). Exact
active-policy state ✓ (V26 snapshot/restore of V3 globals + chassis).
Exact planner state ✓ (adapter step counters restored; the double-call
invariant guard tripped once during development and was fixed by
restoring both adapters — the guard works). Deterministic ✓
(independent re-run identical). Independent reconstruction ✓
(fresh processes, frozen bytes, `assert_frozen` at startup).
