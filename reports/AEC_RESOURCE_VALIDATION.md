# AEC-RESOURCE: Validation & Verification Report
## Architectural Development Phase 002

### Executive Validation Summary

AEC-RESOURCE was subjected to rigorous micro-validation, symbolic/simulator parity analysis, adversarial stress testing, and latency benchmarking. 

- **Total Test Suite**: 233 passing tests (42 resource-specific tests, 191 regression/baseline tests).
- **Adversarial / Micro-Validation Suite**: 20/20 test cases passing (Cases A through T).
- **Symbolic vs. Simulator Parity**: 100% agreement across all verified conversion and feed pathways.
- **Fail-Closed Verification**: Zero false approvals on capacity overflow, starvation risk, cash liquidity holes, or unresolvable trajectories.
- **Performance**: Sub-0.1ms mean latency per complete resource evaluation.

---

### 1. Test Architecture & Coverage

The validation suite is divided into 6 modular test files under `tests/aec/`:

| Test Module | Tests | Focus Area | Status |
|:---|:---:|:---|:---:|
| `test_resource_dag.py` | 8 | DAG nodes, edges, conservation laws, double-allocation, overflow, closures | PASSED |
| `test_resource_feed_security.py` | 5 | Multi-species feed extraction, starvation escape mechanics, feed trajectory | PASSED |
| `test_resource_conversions.py` | 5 | Recipe catalog, bounded search, cash hole detection, terminal pruning | PASSED |
| `test_resource_parity.py` | 3 | Symbolic DAG vs exact counterfactual simulation parity & divergence detection | PASSED |
| `test_resource_micro_validation.py`| 20 | Adversarial Cases A through T spanning all boundary failure modes | PASSED |
| `test_resource_benchmarks.py` | 1 | Microsecond latency profiling across all four core engines | PASSED |
| **Total AEC-RESOURCE** | **42** | **Full compiler pass coverage** | **100% PASS** |

---

### 2. Adversarial Micro-Validation (Cases A through T)

The 20 adversarial cases mandated by the architectural specification were implemented deterministically and evaluated:

| Case | Scenario | Invariant / Boundary Tested | Observed Outcome | Evaluation |
|:---|:---|:---|:---:|:---:|
| **Case A** | Simple valid conversion | Acquired wheat transformed to hay within capacity & budget | Committed & verified | PASS |
| **Case B** | Insufficient input | Conversion requires 5 wheat when only 2 exist | Abstained (InsufficientInput) | PASS |
| **Case C** | Delayed arrival | Input arrives at $t=5$ but conversion attempted at $t=3$ | Abstained (TemporalAvailability) | PASS |
| **Case D** | Feed security violation | Patch attempts to sell 2 Hay needed for Cow on turn 3 | Abstained (FeedSecurityCheck) | PASS |
| **Case E** | Feed purchase rescue | Patch purchases feed early to avert future starvation | Recognized & verified | PASS |
| **Case F** | Capacity overflow | Producing 10 items into a shed with 2 remaining slots | Abstained (CapacityOverflow) | PASS |
| **Case G** | Cash deadlock | Multi-stage conversion profitable eventually but dips cash $< 0$ | Abstained (CashLiquidityHole) | PASS |
| **Case H** | Downstream production | Feed acquisition unlocks milk production; causal link verified | Closure expanded to milk node | PASS |
| **Case I** | Terminal infeasibility | Conversion requires 5 turns when only 2 remain | Abstained (TerminalDistance) | PASS |
| **Case J** | Terminal valid conversion | Short conversion (1 turn) completes and liquidates prior to $T$ | Certified & verified | PASS |
| **Case K** | Multi-stage conversion | Wheat $\to$ Hay $\to$ Milk across sequential turns | Temporal order preserved | PASS |
| **Case L** | Broken middle stage | Wheat $\to$ Hay $\to$ Milk where Hay $\to$ Milk fails (no cow) | Entire candidate rejected | PASS |
| **Case M** | Double allocation | 5 Hay units allocated to two obligations requiring 4 each | Abstained (ReservationConflict) | PASS |
| **Case N** | Same-turn ordering | BUY $\to$ CONSUME vs CONSUME $\to$ BUY evaluated | Exact order preserved; no commute| PASS |
| **Case O** | Worker/resource coupling| Hay pickup requires worker route diversion | AEC-RECONNECT invoked | PASS |
| **Case P** | Worker cannot reconnect | Worker diverted to impassable or blocked tile | Abstained (ReconnectFailure) | PASS |
| **Case Q** | Multi-worker operation | Worker 0 resource movement respects Worker 1 reservation | Collision-free routing verified | PASS |
| **Case R** | Stale backbone | Resource shift invalidates downstream baseline action | Adaptive escalation triggered | PASS |
| **Case S** | Local false positive | Local $H=1$ shows positive cash, but $H=3$ shows starvation | Local candidate rejected | PASS |
| **Case T** | Broad false optimism | Extended horizon valid symbolically, but simulator hits overflow| Abstained (SimulatorMismatch) | PASS |

---

### 3. Symbolic vs. Simulator Parity Analysis

The `ResourceParityHarness` (`aec/resource/parity.py`) verifies consistency between the symbolic prediction of the `TemporalResourceDAG` and the exact state trajectory produced by `CounterfactualSimulator`.

#### 3.1 Parity Metrics
- **State Inventory Agreement**: Net commodity balances after action execution must match $\Delta \text{Inventory}_{\text{symbolic}} \equiv \Delta \text{Inventory}_{\text{sim}}$.
- **Cash Flow Agreement**: Cash delta from transaction costs must match to 0 floating point divergence.
- **Capacity Agreement**: Shed occupancy volume after execution must strictly align.

#### 3.2 Divergence Traps
Tests in `test_resource_parity.py` intentionally injected subtle divergence (e.g. unmodeled inventory consumption, hidden transaction fees, unmodeled shed overflow). In 100% of cases, the parity harness detected divergence, flagged the mismatch, and triggered fail-closed abstention.

---

### 4. Determinism & Isolation Verification

- **Seed Repeatability**: Tests executed under identical initial states and random seeds produced byte-identical DAG structures, dependency closures, and rollout trajectories across 1,000 repetitions.
- **No Side-Effects / Silent Mutations**: Neither the DAG nor the simulation passes mutate the backbone action plan or the baseline `EconomicIR`. All candidate modifications remain isolated in immutable `CoupledPatch` and `ShadowRolloutState` structures.

---

### 5. Performance & Latency Benchmarks

Benchmarks executed on AMD64 hardware (Python 3.14.3) across $N = 500$ iterations per subsystem:

| Subsystem Component | Mean Latency | Median Latency | p95 Latency | Memory Allocation |
|:---|:---:|:---:|:---:|:---:|
| **DAG Construction** | 0.0184 ms | 0.0182 ms | 0.0196 ms | Minimal (< 1 KB) |
| **Dependency Closure** | 0.0030 ms | 0.0030 ms | 0.0032 ms | Minimal |
| **Feed Security Engine** | 0.0512 ms | 0.0484 ms | 0.0628 ms | Minimal |
| **Conversion Discovery** | 0.0106 ms | 0.0102 ms | 0.0113 ms | Minimal |
| **Full Combined Pipeline** | **0.0832 ms** | **0.0798 ms** | **0.0969 ms** | **< 4 KB** |

**Conclusion**: The complete resource evaluation pipeline executes in under 0.1 milliseconds (100 $\mu$s), consuming less than 0.1% of the per-turn decision time budget.

---

### 6. Known Architectural Limitations & Boundaries

1. **Labor Shadow Price Integration**: Labor requirements for resource movement are represented as discrete worker availability slots. Continuous marginal labor shadow-price valuation is deliberately out of scope for Phase 002 (remains quarantined as documented in Checkpoint 001).
2. **Opponent Strategic Foreclosure**: The feed security engine models environmental and market feed availability but does not predict deliberate competitive hay buyouts by opponents. It relies solely on existing market regime pressure signals.
3. **Quarantine Enforcement**: While `RESOURCE_CONVERSION` and `EMERGENCY_FEED_PURCHASE` are now architecturally complete and micro-validated, they remain **quarantined** in `aec/config.py` pending an authorized prospective preregistration protocol.
