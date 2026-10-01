# V24 Challenger Specification — C2: Clustered Livestock & Cow Scaling

## 1. Hypothesis & Empirical Grounding
- **Empirical Observation**: In the Top 10 meta-x-ray, Cluster A agents (DSM, Vadim Vasilenko) purchase **10.2 to 13.0 Cows** and construct tight pasture rings adjacent to the farmhouse, generating $119k–$123k terminal revenue. V3 targets only ~6.8 Cows.
- **Hypothesis**: Increasing the early target Cow inventory from 6 to 10 on Days 0–3 whenever cash runway allows, while clustering pastures within 1 tile of spawn, will increase daily milk compounding.
- **Target Bottleneck**: Ranked #2 in `V24_COMPETITIVE_BOTTLENECK_MATRIX.md`.

## 2. Policy Transformation Architecture
- **Component**: Animal Purchase & Pasture Sizing Controller.
- **Intervention Condition**:
  - Evaluated on Days 0–3 when bank balance $> \$200$ and owned cows $< 10$.
  - Adds `['BUY_ANIMAL', 'COW', 1]` to market orders when affordable.
  - Prioritizes placing new pastures on empty tiles adjacent to existing pastures.

## 3. Preregistered Test Protocol
- Test `Challenger C2 standalone vs V3 standalone` across fresh CRN pilot cohort (`249400..249409`, 20 mirrored matches).
- Gate: Must achieve $\Delta \ge 0$ and $W > L$.
