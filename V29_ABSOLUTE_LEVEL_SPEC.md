# V29 — ABSOLUTE-LEVEL SPEC (A7vA7 vs V3vV3; CREATE vs EXTRACT)

Preregistered BEFORE the first holdout match. This is the first and
only operationalization of "A7vA7 vs V3vV3 absolute-level
decomposition" and "CREATE vs EXTRACT" in the program: a full-text
search of all `V27_*.md` / `V28_*.md` finds NO prior definition — the
sole antecedent is `V28_FINAL_REPORT.md` §14 ("This does NOT decompose
value-creation vs zero-sum price extraction (A7vA7 vs V3vV3 absolute
levels unmeasured)"). Nothing below is inherited; everything is defined
here, from the four arms, with exact equations.

## 1. Data per seed (all four arms, same seed, same engine/config)

For each holdout seed `s`, V29 records six terminal-cash numbers
(`env.steps[-1][seat]["reward"]`, the same "terminal cash" V28 used):

| Symbol | Meaning | Source match |
| :--- | :--- | :--- |
| `a0(s)` | A7 cash at seat 0 vs V3 at seat 1 | Arm 1 (A7@0 vs V3@1) |
| `v1'(s)` | V3 cash at seat 1 vs A7 at seat 0 | Arm 1 (same game) |
| `a1(s)` | A7 cash at seat 1 vs V3 at seat 0 | Arm 2 (V3@0 vs A7@1) |
| `v0'(s)` | V3 cash at seat 0 vs A7 at seat 1 | Arm 2 (same game) |
| `A0(s)`, `A1(s)` | seat-0 / seat-1 cash | Arm 3 (A7 vs A7, ONE match yields both) |
| `V0(s)`, `V1(s)` | seat-0 / seat-1 cash | Arm 4 (V3 vs V3, ONE match yields both) |

Match count: 40×2 (Arms 1+2) + 40×1 (Arm 3) + 40×1 (Arm 4) = **160
matches**. Self-play arms need one match per seed: both seats' cash
comes from that single game (a mirrored re-run would be bit-identical
by determinism — verified, not assumed, by the determinism test).

## 2. Primary differential (promotion endpoint; Arms 1+2 only)

Per-orientation paired deltas and the seed mean:

```
d0(s) = a0(s) - v1'(s)        (orientation 0)
d1(s) = a1(s) - v0'(s)        (orientation 1)
m(s)  = (d0(s) + d1(s)) / 2   (seed-level head-to-head edge)
```

`m(s)` is the seed-clustered unit of the six promotion gates (same
construction as V28 Gate 5). Grand mean `M = mean_s m(s)`.

## 3. Absolute levels (Arms 3+4 only)

```
L_A(s) = (A0(s) + A1(s)) / 2   (A7 self-play absolute level)
L_V(s) = (V0(s) + V1(s)) / 2   (V3 self-play absolute level)
C(s)   = L_A(s) - L_V(s)       (absolute-level delta = CREATE, per seed)
```

Grand CREATE `Cbar = mean_s C(s)`. Seat averaging cancels farm
asymmetry to first order (each level averages the poor and rich farm
of the same seed). Reported with: median, SD, quantiles (q05/q25/q75/
q95), min/max, and a seed-clustered 95% t-CI computed EXACTLY as V28
Gate 5 (`mean ± t(0.975,df=39)·SD/√40`) — labeled secondary,
non-gating.

Seat-level CREATE diagnostics (secondary):

```
C_0(s) = A0(s) - V0(s)         (same-seat absolute delta, seat 0)
C_1(s) = A1(s) - V1(s)         (same-seat absolute delta, seat 1)
```

`C(s) = (C_0(s) + C_1(s))/2` exactly. Sign agreement of `mean C_0`
vs `mean C_1` answers "does the answer change under seat reversal".

Farm-gap controls (diagnostic, same construction as V28 §24):

```
G_V(s) = V0(s) - V1(s)         (program-independent farm asymmetry)
G_A(s) = A0(s) - A1(s)
```

## 4. CREATE vs EXTRACT (the decomposition; all four arms)

Definitions (per seed):

```
CREATE(s)  = C(s)              = L_A(s) - L_V(s)
EXTRACT(s) = E(s)              = m(s) - C(s)
```

Identity (exact by construction; enforced by test):

```
m(s) = CREATE(s) + EXTRACT(s)  for every seed s; hence M = Cbar + Ebar.
```

Semantics:

- **CREATE** = how much richer the average seat is when EVERYONE plays
  A7 rather than everyone playing V3. `Cbar > 0` means A7 raises its
  own absolute economic level under self-play ("remains superior when
  facing itself").
- **EXTRACT** = the residual head-to-head edge that exists ONLY
  because the opponent is V3. It is exactly the advantage that
  "disappears when the opponent is also A7".

Calibration (exact, no convention):

- Pure creation (A7 adds +X to its own cash in every game, opponent
  untouched): `m = X`, `C = X`, `E = 0`.
- Pure zero-sum extraction (A7 gains +X iff its V3 opponent loses −X,
  totals fixed): `m = 2X`, `C = 0`, `E = 2X = m`.
- Predation (`C < 0 < m`): A7 wins head-to-head while LOWERING absolute
  level — the catastrophic-weakness pattern OUTCOME B exists to catch.

EXTRACT sub-split (exact, secondary): with `Abar_AV(s) = (a0+a1)/2`
(A7's own mean cash vs V3) and `Vbar_AV(s) = (v0'+v1')/2` (V3's mean
cash vs A7):

```
O_A(s) = Abar_AV(s) - L_A(s)   (what A7 gains from facing V3, not A7)
O_V(s) = L_V(s) - Vbar_AV(s)   (what V3 loses from facing A7, not V3)
E(s)   = O_A(s) + O_V(s)       exactly.
```

Pie diagnostics (secondary, raw — no even-split convention imposed):

```
P_AA(s) = A0+A1,  P_VV(s) = V0+V1,
P_AV0(s) = a0+v1',  P_AV1(s) = a1+v0'.
```

Pie expansion `P_AV· − P_VV` and `P_AA − P_VV` are reported per seed;
they corroborate CREATE without entering it.

## 5. Reported shares and stability (all secondary, non-gating)

- Extractive share `Ebar / M` and creative share `Cbar / M`
  (reported only if `M > 0`; else reported as undefined with the raw
  components).
- Per-seed distributions of `C(s)`, `E(s)`: median, quantiles, SD,
  seed-positive rates, Pearson/Spearman correlation of `C(s)` vs `m(s)`.
- Seat-reversal stability: `mean C_0` vs `mean C_1`; `mean d0` vs
  `mean d1` (V28 §21 construction); within-seed seat-diff distribution.
- Variance comparison: `SD(L_A)` vs `SD(L_V)` (does A7 stabilize or
  destabilize absolute outcomes?); lower-tail quantiles of each level.

## 6. Interpretation rules (preregistered; no forcing)

1. `Cbar > 0` with seed-CI excluding zero → A7 creates absolute value.
2. `Ebar ≈ 0` (small vs `M`, CI covering zero or either sign) →
   head-to-head edge is approximately all creation.
3. `Ebar` large positive share of `M` (≥ 50%) or `Cbar ≤ 0` while
   `M > 0` → OUTCOME-B pattern: competitive response, not general
   economic dominance (exact promotion mapping in the preregistration).
4. `Cbar < 0` materially → catastrophic weakness: head-to-head wins
   come at the expense of absolute output; blocks OUTCOME A even if
   all six gates pass (preregistered veto, §9 of `V29_PREREGISTRATION.md`).
5. If `C(s)`/`E(s)` scatter without a stable sign pattern across
   seeds, the report states the separation is UNCLEAN and refuses to
   force a "create" or "extract" label — per brief §22.

## 7. Auditability

Every quantity in §§2–5 is a closed-form function of the six
per-seed cash numbers in §1, themselves traceable to individual raw
records via `(seed, arm, seat)` keys. The analyzer emits
`results/v29_decomposition.csv` (one row per seed, all intermediate
quantities) so any auditor can recompute the decomposition by hand.
`test_v29_decomposition.py` asserts the §4 identity and the §3 seat
identity on the frozen outputs.
