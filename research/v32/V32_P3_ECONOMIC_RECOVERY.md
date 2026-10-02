# V32 P3 ECONOMIC RECOVERY (§29 analysis)

## 1. Comparison arms (§21; seed sets documented, not silently mixed)

| Arm | Policy | Seeds | Legs | Mean | Median | Max | Wins |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| A (ref) | experts (opp side of P3 eval) | 249675–684 | 240 | ~$150k | $157k | — | — |
| B | A7 frozen (`v32_p3_a7ref`) | 249675–684 | 100 | $90,965 | $88,470 | $142,499 | — |
| C | P2 mixture-BC (P2 evidence) | 249650–672 | 276 | $31 | $0 | $138 | 0 |
| C2 | P2 A7-BC (P2 evidence) | 249650–653 | 16 | ~$2 | ~$0 | $39 | 0 |
| D1 | P3 mixture-BC @3e-4 | 249675–684 | 120 | $467 | $448 | $1,243 | 0 |
| D2 | P3 mixture-BC @3e-3 | 249675–684 | 120 | $60 | $0 | $2,829 | 0 |
| (D3) | P3 A7-BC (not run closed-loop) | — | 0 | — | — | — | — |

Caveat: C ran on P2-SCREEN, D on P3-SCREEN (same 6 opponents). The 15× D1/C
gap cannot be a seed artifact (both ≈0% of expert level; ranges disjoint:
C max $138 < D1 median $448), but paired same-seed C-vs-D was not run —
the decision does not hinge on it (see §3). D3 not run: step-0 all-NOOP +
m_op-nn 0.08 already prove economic failure (P2's better-fidelity A7-BC
replayed $0–39); 120 legs would buy no information.

## 2. Effect sizes

- D1 vs C: +$436 mean (+1400%), median $0→$448. Reproducible (stdev $405,
  both seats, all 6 opps >$0 mean) — not one lucky episode.
- D2 vs C: +$29 mean; median $0. Indistinguishable from C economically
  DESPITE higher fidelity (m_op-nn 0.90 vs P2 0.30) — fidelity≠economics.
- D1/D2 vs B: 0.5% / 0.07% of A7. Zero wins in 240 legs.

## 3. §29 four-way distinction

1. Representation success: YES (codec lossless; market heads learn; dedicated
   wash fits; G1/G2-recalibrated PASS).
2. BC success: PARTIAL (market fidelity 0.80–0.90, unit 0.47–0.54; but the
   critical step-0 pattern systematically wrong → G3 FAIL).
3. Economic success: NO ($467 max-arm mean with broken wash mechanism;
   §29 bars mechanism-consistency, which fails).
4. Generalization success: UNTESTED (correctly — see generalization doc).

## 4. Verdict

Economic recovery INSUFFICIENT. D1's $0→$467 lift is real, reproducible, and
closed-loop, but mechanism-broken (reversed wash); D2 proves further fidelity
gains do not convert. P3 does not demonstrate "learned economic behavior
becomes nontrivial and stable."
