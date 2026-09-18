# Walkthrough: AEC Phase 003 — Multi-Worker Logistics Coordination

## 1. Overview & Architectural Milestone

AEC Phase 003 introduces the **Multi-Worker Logistics Coordination Layer**, resolving the primary structural bottleneck in the Adaptive Economic Compiler (AEC): **labor cannibalization**.

Previous physical deviations (such as `RESOURCE_CONVERSION` and `EMERGENCY_FEED_PURCHASE`) suffered severe economic regression when evaluated on offline replay because they diverted the primary worker (Farmer) away from high-value harvesting and planting duties. Phase 003 provides the architectural capability to:
1. Identify when baseline worker obligations are at risk of cannibalization.
2. Formulate deviations as discrete, dependency-constrained `WorkerTask` sets.
3. Optimally allocate tasks to available auxiliary workers (Hand 1, Hand 2, etc.) while preserving the Farmer's baseline schedule.
4. Derive exact marginal labor opportunity costs without arbitrary hourly wages ($hire\_cost / 24$).
5. Coordinate space-time paths and resource ownership without collision or contention.

---

## 2. Core Implementation Components

### 2.1 Multi-Worker Coordination Package (`aec/coordination/`)
- `worker_model.py`:
  `WorkerType` (`FARMER`, `HAND`), `WorkerCapability`, `WorkerState`, and `extract_farm_workers` factory.
- `task_model.py`:
  `WorkerTask`, explicit 8-tier `TaskPriority` hierarchy, and `TaskDependencyGraph` DAG.
- `assignment.py`:
  `WorkerAssignment`, `WorkerSchedule`, `DisplacementOutcome`, and exact `compute_marginal_labor_cost`.
- `dominance.py`:
  `MultiWorkerDominancePruner` enforcing Pareto-dominance over candidate assignments.
- `scheduler.py`:
  `MultiWorkerLogisticsCoordinator` bounded deterministic assignment and routing compiler.
- `__init__.py`:
  Unified module exports.

### 2.2 Reconnection & Space-Time Extensions (`aec/replanning/reconnect.py`)
- Extended `SpacetimeReservationTable` with:
  - Task exclusivity reservations (`reserve_task`, `is_task_available`)
  - Resource locking (`reserve_resource`, `is_resource_available`)
  - Building site reservations (`reserve_building`, `is_building_available`)
  - Full trajectory collision checking (`reserve_trajectory`, `is_trajectory_collision_free`)

### 2.3 Safety Invariant Battery Extensions (`aec/safety/checks.py`)
- Integrated 9 formal multi-worker invariants:
  - `worker_assignment_consistency`
  - `worker_capability_validity`
  - `worker_task_exclusivity`
  - `worker_spacetime_collision`
  - `worker_resource_ownership`
  - `worker_task_deadline`
  - `worker_route_continuity`
  - `worker_handoff_validity`
  - `worker_baseline_obligation_preservation`

### 2.4 Task Decomposition Integrations
- `feed_security.py`:
  `decompose_feed_rescue_to_tasks` (shed pickup $\to$ animal feed delivery).
- `conversions.py`:
  `decompose_conversion_to_tasks` for multi-worker conversion execution.

---

## 3. Adversarial Micro-Validation Matrix (`MW-01` to `MW-20`)

All 20 predeclared adversarial scenarios passed with 100% compliance in `tests/aec/test_phase003_multiworker.py`:

| Scenario | Description | Key Mechanism Tested | Verdict |
| :--- | :--- | :--- | :---: |
| **MW-01** | Two workers, urgent feed + crop harvest | Non-critical worker assigned feed; harvest preserved | **PASSED** |
| **MW-02** | Only primary worker can reach feed | Primary worker assigned; remaining schedule preserved | **PASSED** |
| **MW-03** | Simultaneous impossible obligations | Conflict detected; fail-closed abstention | **PASSED** |
| **MW-04** | Farmer diverted from harvest | Hand 1 absorbs feed task, preventing cannibalization | **PASSED** |
| **MW-05** | Route swap collision | Space-time reservation table detects and reroutes | **PASSED** |
| **MW-06** | Direct worker-to-worker handoff | Physically illegal handoff rejected (must use shed) | **PASSED** |
| **MW-07** | Local gain destroying market sale | Dependency closure catches deadline failure | **PASSED** |
| **MW-08** | Two feasible assignments | Dominance pruner selects obligation-preserving plan | **PASSED** |
| **MW-09** | Emergency feed safe with Hand 1 | Safe 2-worker configuration discovered | **PASSED** |
| **MW-10** | Resource conversion with Hand 1 | Multi-worker execution ready without cannibalization | **PASSED** |
| **MW-11** | Building tile contention | Space-time table enforces single-worker exclusivity | **PASSED** |
| **MW-12** | Resource double-allocation | Resource locking prevents second worker pickup | **PASSED** |
| **MW-13** | Worker unavailable mid-route | Escalates and abstains to backbone | **PASSED** |
| **MW-14** | Terminal task cannot complete | Rejection due to horizon deadline breach | **PASSED** |
| **MW-15** | Optional baseline task replacement | Optional weed dig superseded by high-value duty | **PASSED** |
| **MW-16** | Mandatory baseline task displacement | Rejection certified when no peer can absorb | **PASSED** |
| **MW-17** | Cash timing dependency | Task DAG enforces prerequisite funding order | **PASSED** |
| **MW-18** | Shed arrival overflow | Capacity check rejects cargo exceeding shed cap | **PASSED** |
| **MW-19** | 5 consecutive identical runs | Bit-exact deterministic reproducibility | **PASSED** |
| **MW-20** | 3 active workers | Deterministic bounded assignment across 3 workers | **PASSED** |

---

## 4. Performance & Latency Benchmarks

Measured on the development environment across 500–1000 trials (`scratch/benchmark_phase003.py`):

```
Task Graph Construction (1000 trials):  mean=0.0059ms, med=0.0053ms, p95=0.0087ms
Dominance Pruning (1000 trials):        mean=0.0007ms, med=0.0007ms, p95=0.0008ms
Route & Spacetime Pathfinding (500):    mean=0.0712ms, med=0.0607ms, p95=0.1167ms
Coordinator E2E (1 Worker, 500 trials): mean=0.3539ms, med=0.3275ms, p95=0.5400ms
Coordinator E2E (2 Workers, 500 trials):mean=0.3736ms, med=0.3489ms, p95=0.4905ms
Coordinator E2E (3 Workers, 500 trials):mean=0.6720ms, med=0.6189ms, p95=0.9983ms
```

---

## 5. Full Repository Regression Status

```powershell
pytest tests/ -q
319 passed in 1.93s
```
- Total test count: **319 passed** (0 failures, 0 regressions).
- Prospective matches run: **0**.
- Live quarantine status: `RESOURCE_CONVERSION` and `EMERGENCY_FEED_PURCHASE` remain strictly **QUARANTINED**.
