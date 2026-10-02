# V27 — COUNTERFACTUAL ANALYSIS (CF-1/CF-2)

Method: exact active-backbone state (hermetic V3 adapter snapshot at the
branch step), doctored-observation probes with restore between probes,
bisected cash gate, falsification controls, restore-and-continue fidelity
plus an independent re-run. No mechanisms, no market timing, no AEC —
continuation as an analysis tool only (§23). Script:
`scripts/v27_counterfactual_tip.py`; data:
`results/v27_counterfactual_tip.json`.

## CF-1: the 249463 t=289 sheep-branch gate (both seats + repro)

Reconstruction: live (undoctored) V3 action at t=289 contains no sheep
buy on either seat — the replay reproduces the recorded trajectory
(base cash $10,407 both seats, = recorded).

| Probe | Injection | V3 market action | Sheep |
| :--- | ---: | :--- | ---: |
| seat 0, undoctored | $0 | (recorded baseline, no animals) | 0 |
| seat 0, injected | +$31.02 | SELL FERT 17, SELL WOOL 3, BUY WHEAT 6, **BUY_LAND, BUY SHEEP×6, HIRE×2** | 6 |
| seat 1, injected | +$31.02 | identical expansion bundle | 6 |
| seat 0, independent re-run | +$31.02 | identical | 6 |

The branch is a cash-gated EXPANSION MACRO (land + 6 sheep + 2 hires +
funding sells) with threshold $10,438.02 (bisected to <$1; below that:
silent). P3's $11,288 clears it by $850; V3's $10,407 misses it by
$31. A $31 swing (0.3% of cash) decides the ±$13k structural tip —
butterfly coefficient ≈ 400×. Predicted effect (branch fires under
injection): CONFIRMED. Realized terminal effect of the branch: +$13k,
observed in the recorded trajectory (not equated with the probe:
the probe predicts FIRING, the trajectory shows CONSEQUENCE).

Fidelity: restore + continue-live to terminal reproduces recorded
rewards EXACTLY both seats ((118543, 105490) / (106620, 119646));
independent re-run bit-identical (threshold, bundle, terminals).
Probes are non-interfering; snapshot/restore is exact.

## CF-2: non-tip control (249464, t=289, cash $15,935 + up to $2,000)

No firing at any injection level (threshold None); live action has no
sheep. The gate needs (cash ≥ ~$10,438) AND 249463-context (day-12
reactive window armed by that game's state) — cash alone is not
sufficient. This falsifies any simple "cash-at-288 predicts tips" rule
and confirms the regime finding: threshold tips are not predictable
from early observables without V3's full internal state.

## What this does NOT prove

- That P3's +$108 opening caused the tip: the $881 lead's composition
  (opening + mid-game trajectory) is confounded. Necessity is tested by
  ablation A1 on 249463 (real terminal): A1 does NOT tip (0/0 vs V3;
  −$13k vs P3 direct) — P3's opening-induced trajectory is NECESSARY
  for this tip (see V27_ABLATION_RESULTS.md). The CF isolates the GATE;
  the ablation isolates the CAUSE. Together: P3's opening trajectory
  clears a $31-miss gate V3's trajectory misses.
- Long-horizon simulator rollouts were deliberately NOT run: re-
  implemented physics + a modeled opponent over 430 steps is drift
  theater. The ablation provides REALIZED terminal effects instead —
  strictly better evidence for the same question.
- n=1 seed. The gate characterization is exact for 249463 and says
  nothing general about other seeds' reactive branches.
