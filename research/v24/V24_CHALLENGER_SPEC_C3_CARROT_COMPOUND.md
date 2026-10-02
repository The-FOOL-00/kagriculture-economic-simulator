# V24 Challenger Specification — C3: Carrot-Pipelined Compounding

## 1. Hypothesis & Empirical Grounding
- **Empirical Observation**: 7 of 10 elite agents (including DSM, Majkel, Vadim, Orbital) select **Carrot** as their primary secondary crop (33–85 Carrots planted), exploiting its fast 3-day turnaround and low water sensitivity. V3 defaults heavily to Strawberry.
- **Hypothesis**: Redirecting secondary crop seed purchases on Days 2–12 from STRAWBERRY to CARROT will accelerate cash compounding during the critical mid-game phase (Days 5–15).
- **Target Bottleneck**: Ranked #3 in `V24_COMPETITIVE_BOTTLENECK_MATRIX.md`.

## 2. Policy Transformation Architecture
- **Component**: Secondary Crop Selection Controller.
- **Intervention Condition**:
  - Whenever market orders on Days 2–12 specify `['BUY_SEED', 'STRAWBERRY', qty]`, convert to `['BUY_SEED', 'CARROT', qty]`.
  - Planting dispatcher plants CARROT seeds on available tilled plots.

## 3. Preregistered Test Protocol
- Test `Challenger C3 standalone vs V3 standalone` across fresh CRN pilot cohort (`249400..249409`, 20 mirrored matches).
- Gate: Must achieve $\Delta \ge 0$ and $W > L$.
