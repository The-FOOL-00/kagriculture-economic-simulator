# V25 Livestock Planner Specification

## 1. Objective
Establish a rigorous, net-present-value (NPV) based livestock acquisition and maintenance model. Avoid under-investment (V3 baseline maintained only 3 cows) while preventing over-investment that crowds out critical crop labor.

## 2. Unit Economic Model

For animal species $a \in \{\text{Cow}, \text{Sheep}, \text{Chicken}\}$:
* $Cost_{buy}(a)$: Initial capital expenditure (Cow = 1000, Sheep = 600, Chicken = 100).
* $Rev_{daily}(a)$: Daily yield value (Milk = 60/turn, Wool = 120/every 2 turns $\approx$ 60/turn, Egg = 15/turn).
* $FeedCost_{daily}(a)$: Hay / grain consumption cost per turn ($\approx 10$/turn).
* $Labor_{care}(a)$: Worker actions required per turn ($\approx 0.5$ actions/turn for feeding/milking).
* $Margin_{daily}(a) = Rev_{daily}(a) - FeedCost_{daily}(a) - (Labor_{care}(a) \times ShadowWage)$.

### Break-Even Horizon:
$$T_{breakeven}(a) = \frac{Cost_{buy}(a)}{Margin_{daily}(a)}$$
For cows:
$$Margin_{daily} \approx 60 - 10 - 20 = 30 \implies T_{breakeven} \approx \frac{1000}{30} \approx 33.3 \text{ turns}$$

## 3. Livestock Scaling Policy
* **Target Herd Size**: Scale from initial 3 cows up to 8–10 cows during turns $50 \le t \le 300$.
* **Prerequisites for Purchase**:
  1. $T_{remaining} \ge 120$ turns (ensures $>3\times$ break-even horizon).
  2. $Cash_{available} \ge Cost_{buy} + 10 \times FeedCost_{buffer}$.
  3. Stable feed supply: Barn hay inventory $\ge 5 \times (N_{cows} + 1)$.
  4. Labor capacity: Total active workers $N_{workers} \ge 2 + \lceil 0.3 \times N_{cows} \rceil$.
* **Pasture Clustering**:
  * Keep livestock restricted to designated pasture boundary adjacent to barn.
  * Eliminates wandering delay and bounds milking/care transit costs.
