# V24 Challenger Specification — C1: Labor Dispatch & Idle-Zeroing

## 1. Hypothesis & Empirical Grounding
- **Empirical Observation**: In the Top 10 meta-x-ray, elite agents (Vadim Vasilenko, Orbital Terraformer, Majkel1337, DSM) maintain worker idle rates of **0.8% – 5.1%**, while V3 / V22R1 wastes **8.2% overall (and up to 38.4% in early days)** on `['PASS']` actions.
- **Hypothesis**: Replacing idle `['PASS']` worker turns with opportunistic local productive actions (watering unwatered plants on/adjacent to the worker, harvesting ripe crops, feeding/caring for adjacent livestock) will directly eliminate ~20% of wasted labor, accelerating crop maturation and revenue yield.
- **Target Bottleneck**: Ranked #1 in `V24_COMPETITIVE_BOTTLENECK_MATRIX.md`.

## 2. Policy Transformation Architecture
- **Component**: Worker Action Dispatcher (Standalone Backbone Challenger).
- **Intervention Condition**:
  - Evaluated on every turn $t \in [1, 718]$ for each farmhand $i \in [0, N-1]$.
  - Triggers **if and only if** the base action for hand $i$ is `['PASS']`.
- **Opportunistic Action Priority Ladder**:
  1. **Immediate Tile Harvest**: If current tile has ripe crop (`yield_units > 0`), execute `['HARVEST']`.
  2. **Immediate Tile Watering**: If current tile has an unwatered growing plant (`watered_today == False`), execute `['WATER']`.
  3. **Immediate Tile Care/Feed**: If current tile has pasture with unfed animal and worker carries feed, execute `['FEED']`; if uncared, execute `['CARE']`.
  4. **Orthogonal 1-Step Neighbor Assist**: Check 4 orthogonal neighbors (North, South, East, West). If an adjacent tile has an unwatered crop or ripe crop, step toward it.
  5. Otherwise, remain `['PASS']`.

## 3. Preregistered Test Protocol
- Test `Challenger C1 standalone vs V3 standalone` across fresh CRN pilot cohort (`249400..249409`, 20 mirrored matches).
- Gate: Must achieve non-negative mean paired delta ($\Delta \ge 0$) and positive win rate ($W > L$).
