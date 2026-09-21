# V25 Labor Planner Specification

## 1. Objective
Eliminate structural, unexplained worker `PASS` / idle turns. In V3, workers suffered up to 28% early idle turns due to fixed-horizon padding `route += [['PASS']] * (horizon - offset - len(route))` and tape starvation. The V25 Labor Planner provides continuous, reactive task generation to ensure every worker turn is economically productive.

## 2. Worker Task Priority Queue

At each turn $t$, for each available worker $w \in \{0, \dots, N_{workers}-1\}$, the labor planner evaluates all accessible tiles within distance $D_{max}$ and assigns the highest-utility valid task:

| Priority | Task Type | Precondition | Economic Utility / Turn |
|---|---|---|---|
| **P1** | **Critical Livestock Care** | Animal hungry or pending milk/wool | Prevents animal health degradation & captures high-margin milk/wool (60-120/action). |
| **P2** | **Harvesting Mature Crops** | Crop at full maturity | Frees land tile and deposits harvest value into inventory. |
| **P3** | **Crop Hydration / Watering** | Soil dry on growing crop | Prevents growth stall; maintains harvest turnover schedule. |
| **P4** | **Planned Planting** | Tilled soil clear, seed in bag/shop | Deploys active working capital into biological compound growth. |
| **P5** | **Land Preparation / Tilling** | Cleared untilled tile, planting planned | Expands productive arable acreage. |
| **P6** | **Feed Delivery / Barn Restock** | Barn trough empty or low | Ensures animal automated feeding buffer. |
| **P7** | **Repositioning / Hub Transit** | No immediate task | Moves toward central farm transit node rather than remaining frozen. |

## 3. Idle Elimination Mechanics
1. **Dynamic Horizon Extension**:
   * Instead of padding routes with passive `PASS`, if a primary route completes early, the worker immediately draws from the local opportunist task pool (P3 watering, P5 tilling, P7 repositioning).
2. **Anti-Collision Coordination**:
   * Shared tile reservation grid prevents two workers from moving into the same cell or competing for the same crop/animal.
3. **Strict Fallback Policy**:
   * A worker only executes `PASS` if literally zero valid actions or moves exist on the map (e.g. boxed in or completely depleted energy/resources), never as an intentional wait state.
