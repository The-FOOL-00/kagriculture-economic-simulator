# V32 P3 GENERALIZATION (§30) — NOT RUN (correctly)

§30 gates the unseen-seed check on BC passing development checks ("Once BC
passes development checks, evaluate on a clean unseen seed set"). P3 BC did
NOT pass: G3 (step-0 wash) fails on all three checkpoints and G4 shows
mechanism-broken economics ($467/D1, $60/D2). Evaluating a known-broken policy
on single-touch seeds would burn irreplaceable virginity for no information.

## Preserved virginity (verified at P3 exit)

- P3-CONFIRM `249685–249694`: ZERO executions (no P3 result file references
  these seeds; quarantine never disabled).
- V32-CONFIRM `249695–249734`: ZERO executions.
- Protected holdouts (GATE0 `214200–249`, V29 remainder `340090–199`): ZERO.
- P3 executed ONLY: P3-SCREEN `249675–249684` (prereged), consumed P2 seeds
  (`249635` T5/probes; `249635–249649` training rows — no new execution),
  and offline training (no seeds).

## What a follow-up inherits

A future phase with a wash-capable checkpoint may single-touch P3-CONFIRM
`249685–249694` for the §30 screen under a new preregistration. The seeds,
panel, and eval harness (`scripts/v32_p3_evaluate.py`) are ready.
