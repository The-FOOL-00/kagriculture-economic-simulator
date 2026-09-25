# V32 P2 REPRESENTATION CHECK (§13 diagnostic, offline only)

Probe: multinomial logistic on FROZEN normalized Groups A–D features,
fit on BC-train legs, evaluated on BC-val legs (seeds 249647–249649).
Targets are offline labels only — never policy inputs.

| Bin | cash-5 (acc/maj) | win | pair-level | own-wash |
| :--- | :--- | :--- | :--- | :--- |
| 0–24 | 0.32/0.67 | 0.79/0.51 | 0.41/0.75 | 0.87/0.26 |
| 25–100 | 0.34/0.67 | 0.74/0.50 | 0.39/0.75 | 0.55/0.25 |
| 101–200 | 0.34/0.67 | 0.71/0.50 | 0.77/0.75 | 0.39/0.25 |
| 201–300 | 0.44/0.67 | 0.69/0.50 | 0.82/0.75 | 0.31/0.25 |
| 301+ | 0.50/0.67 | 0.60/0.50 | 0.96/0.75 | 0.25/0.25 |

## OBSERVED FACT

- Pair-economy level: no signal early (0.41), rising through 101–300
  (0.77→0.82), strong post-resolution (0.96). Mechanism-consistent.
- Own-wash sanity: 0.87 early (GROUP C plumbing works), fading as the
  8/32-step windows age it out. Expected.
- Win: 0.79 early FALLING to 0.60 — own-wash identity signal (W72-wash
  wins in these pairs) fading from GROUP C, not lottery signal.
- Cash bucket: below-majority throughout (coarse quintiles + n=3 val
  seeds; linear probe). Weak; not a stop (level target resolves).

## INTERPRETATION → PROCEED

The representation exposes the emerging economic path increasingly
through the R1 resolution window. §13 gate passes on the level target.
No stop-and-redesign triggered.
