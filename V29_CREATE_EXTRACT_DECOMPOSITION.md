# V29 — CREATE/EXTRACT DECOMPOSITION (four arms, same seeds)

Math: `V29_ABSOLUTE_LEVEL_SPEC.md` (frozen d818fb1). Data:
`results/v29_decomposition.csv` (40 per-seed rows, all intermediate
quantities) + `results/v29_decomposition_stats.json` (emitted by
`scripts/v29_analyze.py`).

## 1. Headline numbers

| Quantity | Value |
| :--- | ---: |
| Head-to-head seed-mean edge `M` | +$1,289.18 (95% CI [+$1,284.38, +$1,293.97]) |
| A7 self-play level `L_A` (mean) | $94,574.78 |
| V3 self-play level `L_V` (mean) | $94,574.78 |
| **CREATE `Cbar = L_A − L_V`** | **$0.00** (SD $0.00, 95% CI [$0, $0]) |
| **EXTRACT `Ebar = M − C`** | **+$1,289.18** (95% CI [+$1,284.38, +$1,293.97]) |
| Creative share `Cbar/M` | 0.0% |
| Extractive share `Ebar/M` | 100.0% |
| Catastrophic-weakness veto (`Cbar<0`, CI fully <0) | NOT triggered (C = 0 exactly) |
| OUTCOME-B pattern (`Cbar≤0` or `E/M≥50%`) | TRIGGERED (both clauses) |

Identity check: `m = CREATE + EXTRACT` holds to <1e-6 on all 40 seeds;
`E = O_A + O_V` and `C = (C_0+C_1)/2` likewise (asserted by the
analyzer and `test_v29_decomposition.py`).

## 2. The six decomposition questions (brief §22)

1. **Does A7 create more absolute economic output?** NO — to the
   dollar. `L_A == L_V` on all 40 seeds (SD $0.00); per-seat
   `C_0 = C_1 = $0` on all 40 seeds.
2. **Does A7 mainly exploit V3?** In the operational sense: ENTIRELY.
   100% of the head-to-head edge is opponent-specific (extract share
   1.0). "Exploit" here means positional redistribution, not
   mistake-farming (see §4).
3. **Does A7 remain superior when facing itself?** NO. A7vA7 ≡ V3vV3
   exactly — not just terminally: full 720-step money trajectories
   and structural series are identical on 40/40 seeds.
4. **How much advantage disappears when the opponent is also A7?** ALL
   of it: $1,289.18 of $1,289.18 (100%).
5. **Are those quantities stable across seeds?** Perfectly: `C(s) = 0`
   and `E(s) = m(s)` on every seed; `m(s)` itself has seed-SD $15.
6. **Does the answer change under seat reversal?** NO: `C_0 = C_1 = 0`
   exactly; head-to-head medians +$1,286 both seats.

The separation is CLEAN (spec §6 needs no unclean-separation refusal):
pure extraction, zero creation, on every seed.

## 3. Self-play absolute levels

| Metric | A7vA7 | V3vV3 |
| :--- | ---: | ---: |
| Mean terminal cash | $94,574.78 | $94,574.78 |
| Seat-gap nonzero seeds | 6/40 (|G|≤$219) | 6/40 (identical gaps) |
| Full-trajectory identity | — | 40/40 money series identical |

A7vA7 actions differ from V3vV3 ONLY at step 0 (the wash: 40/40 seat-0
action digests differ). Everything downstream — all 720 money steps,
all structures, both terminals — is bit-identical. The symmetric wash
size (30/30 vs 50/50) is a complete downstream no-op.

## 4. What "extract" means here (audited, not hand-wavy)

The wash P&L ledger, measured at obs[1] on all arms:

| Matchup (own wash vs opp wash) | Own wash P&L |
| :--- | ---: |
| 30 vs 50 (A7 head-to-head) | +$54 |
| 50 vs 30 (V3 head-to-head) | −$54 |
| 30 vs 30 (A7vA7) | $0 |
| 50 vs 50 (V3vV3) | $0 |

The wash is ZERO-SUM between the washers: the smaller washer extracts
+$54 from the bigger washer; symmetric washers net $0 regardless of
size. A7's entire game is unilateral wash-reduction: it keeps V3's full
step-0 calibration (unlike P3's bypass) while taxing V3's bigger wash
+$54, then rides the deterministic cascade (melon gate → +$1,258
harvest → +$1,286). When both wash 30, nobody is taxed and the
downstream paths coincide with the 50/50 world to the dollar — the
extra-melon production has $0 marginal value under symmetric supply
(supply/price absorption), so CREATE = $0 exactly.

Corroborating common-mode evidence: head-to-head games reach very
different absolute wealth than self-play games on the SAME seed (both
players ±tens of thousands together, either direction — e.g. 340054:
$164,649/$163,363 vs $86,474/$86,474), while the differential stays
pinned at ≈+$1,286. Absolute wealth is regime-dependent (symmetric vs
asymmetric opening); the differential is rigid. A7's edge lives purely
in the differential.

## 5. Stability and variance

- `SD(L_A) = SD(L_V)` exactly (identical series); A7 neither
  stabilizes nor destabilizes absolute outcomes — it reproduces them.
- `C(s)` seed-positive rate 0/40 (all exactly zero); `E(s)` 40/40
  positive. Correlation of `C` vs `m`: undefined (C constant) —
  reported as such, not forced.
- No farm-gap confounding: levels average both farms per seed; gaps
  are tiny (≤$219) and policy-independent (`G_A == G_V` on all 6).

## 6. Decomposition verdict

A7 is a PURE POSITIONAL EDGE with ZERO absolute-value creation under
the tested protocol. The preregistered OUTCOME-B pattern triggered on
both clauses. A7 is therefore a CONFIRMED COMPETITIVE RESPONSE to V3,
not a general economic-dominance candidate. This does not diminish the
head-to-head result (80/80 holdout wins): it precisely characterizes
it.
