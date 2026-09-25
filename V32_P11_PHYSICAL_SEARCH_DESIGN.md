# V32 P11 — SPECIFICATION REPORT: PHYSICAL SEARCH DESIGN & SYSTEM ARCHITECTURE
**Phase:** V32 P11  
**Date:** 2026-09-23  
**Status:** ARCHITECTED, IMPLEMENTED & VERIFIED  
**Package:** `candidates/v32_p11_terminal/`  

---

## 1. Architectural Overview & Surgical Splice

The P11 terminal physical search was designed as an optional, fail-closed terminal overlay wrapping the protected incumbent `A7`:

```text
                  +-----------------------------------+
                  |             Game Loop             |
                  +-----------------------------------+
                                    |
                    [Step < 712]    |    [Step >= 712]
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+-----------------------+                       +-----------------------+
|  A7 Incumbent Passthrough  |                   |   Terminal Observer   |
| (100% Bit-Identical)  |                       |   & State Extraction  |
+-----------------------+                       +-----------------------+
                                                            |
                                                            v
                                                +-----------------------+
                                                | Target & Path Feasibility |
                                                |  Cone (Horizon <= 718) |
                                                +-----------------------+
                                                            |
                                                            v
                                                +-----------------------+
                                                | Exact Shadow Rollout  |
                                                |  (Budget: 16-128)     |
                                                +-----------------------+
                                                            |
                                           +----------------+----------------+
                                           |                                 |
                                    [Fails Gates]                     [Passes All Gates]
                                           v                                 v
                                +-----------------------+         +-----------------------+
                                |  A7 Baseline Fallback |         | Terminal Spliced Plan |
                                +-----------------------+         +-----------------------+
```

---

## 2. Component Design Specifications

The implementation is partitioned into modular, isolated files within `candidates/v32_p11_terminal/`:

### 2.1 `incumbent.py` — Protected Baseline Isolation
- Loads `E9_AST` (`candidates/v30_a7_standalone/main.py`) read-only.
- Verified SHA-256 digest: `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f`.
- Preserves all behaviors outside the terminal window without mutation.

### 2.2 `terminal_state.py` — Physical Reachability & Realizable Value
- Maps all 10x10 farm tiles, animal structures, and worker positions.
- Pinpoints the four authoritative shed-access tiles on a 10x10 board: `(4, 4), (5, 4), (4, 5), (5, 5)`.
- Defines the **Physical Realizability Invariant**:
  $$\text{Steps Required} = \text{dist}(\text{worker}, \text{target}) + 1 + \text{dist}(\text{target}, \text{shed}) + 1$$
  $$\text{Realizable If: } \text{step} + \text{Steps Required} \le 718$$
  Any target whose path cannot complete the final `DROP` by step 718 has a realizable economic value of **$0.00**.

### 2.3 `target_generator.py` — Feasible Pairing & Cargo Guard
- Filters candidate map targets by harvestability, time-to-shed, and net liquidation value.
- **Cargo Protection Guard:** Strictly forbids detours for any worker currently holding cargo with valuation $\ge \$10.00$ (e.g. carrots, milk, wool). Such workers must proceed directly to the shed.

### 2.4 `path_generator.py` — Exact Action Sequencer
- Computes deterministic Manhattan navigation paths using unit operations: `NORTH`, `SOUTH`, `EAST`, `WEST`.
- Appends the physical target operation: `HARVEST` or `COLLECT_FERTILIZER`.
- Appends return navigation to the nearest shed-access tile.
- Emits `DROP` into shed and pads with `PASS` until horizon end.

### 2.5 `simulator.py` — Exact Shadow Forward Simulator
- Replicates the official Kaggle environment transition semantics for unilateral evaluation:
  1. `_apply_unit_action`: position updates, inventory collection, and shed drops.
  2. `_process_market`: executes baseline market orders (712–717) and terminal liquidation (718).
  3. `_decay_plants`: accurately tracks plant lifecycle.
  4. Returns penny-exact projected final cash.

### 2.6 `acceptance.py` — Strict Invariant Gates
Enforces four mandatory criteria before any candidate plan can be adopted:
1. **Strict Cash Dominance:** $\text{Final Cash}(\text{Candidate}) > \text{Final Cash}(\text{A7}) + \$0.50$.
2. **Zero Stranded Cargo:** $\sum \text{Carried Inventory at Step 718} == 0$.
3. **Solvency Invariant:** No negative intermediate cash or blocked baseline transactions.
4. **No-Theft Invariant:** Zero interaction with unowned or rival tiles.

### 2.7 `telemetry.py` & `main.py` — Agent Lifecycle & Telemetry Logging
- Records evaluation timestamps, candidate budgets, win/loss deltas, and acceptance reasons.
- Emits pure baseline actions whenever the planner abstains.

---

## 3. Strict Pre-E Purity & Verification

Purity tests (`candidates/v32_p11_terminal/tests/test_p11_terminal.py`) verified:
- For steps $0 \le t \le 711$, candidate output matches baseline A7 **bit-for-bit** across 100% of tested steps.
- The candidate introduces **zero** external dependencies and operates entirely within stdlib and official engine boundaries.
