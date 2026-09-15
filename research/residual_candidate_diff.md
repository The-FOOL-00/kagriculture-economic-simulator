# Source Diff Audit: V54++ vs V54+ Residual Candidate

**Audit Protocol**: Championship Experiment — Residual Candidate Independent Replication Audit  
**File 1 (Baseline)**: `candidates/v54_plus_shop.py` (SHA256: `592f0ba31b3b20b5a3aad409a753b5e6bdeb29a9eb2381342b1cd527509fa9e8`)  
**File 2 (Candidate)**: `candidates/v54_plus_residual.py` (SHA256: `5b2d5080ba38287812d137a21c7b09071e1f66a10c32d7c3ec4bb61be4520e80`)  

---

## 1. Unified Diff

```diff
--- candidates/v54_plus_shop.py
+++ candidates/v54_plus_residual.py
@@ -68,2 +56,8 @@
-# Configuration & Candidate Routes
-_CONFIG = copy.deepcopy(mod_v62._V54_CONFIG)
+# Configuration with exactly ONE proven residual modification
+_CONFIG_DICT = copy.deepcopy(dict(mod_v62._V54_CONFIG.__dict__))
+_CONFIG_DICT["preempt_money_deficit"] = 2000.0
+_CONFIG_DICT["preempt_minimum_delta"] = 4.0
+_CONFIG_DICT["preempt_maximum_batch"] = 12
+_CONFIG = mod_v54._V51ResidualConfig(**_CONFIG_DICT)
```

---

## 2. Invariant Verification

| Component | Status | Verification Detail |
| :--- | :---: | :--- |
| **Route Prior Selection** | **IDENTICAL** | `_select_route` logic, step boundaries (72, 144), shop names (`YARN_STORE`, `BAKERY`) identical. |
| **Macro Route Arrays** | **IDENTICAL** | `_V56_BACKBONE_ROUTE`, `_V56_YARN_ROUTE`, `_V58_BAKERY_YARN_ROUTE` identical. |
| **Strawberry Seed Trim** | **IDENTICAL** | Calls `_v60_seed_trim(obs, action, step)` identically. |
| **Hour-23 Shed Guard** | **IDENTICAL** | Calls `_v60_shed_guard(obs, action, capacity)` identically. |
| **Terminal Unit Recall** | **IDENTICAL** | Steps 713–716 `_route_loaded_units` identical. |
| **Terminal Home Convergence** | **IDENTICAL** | Steps 717–718 `_TERMINAL_UNITS` identical. |
| **Terminal Market Liquidation**| **IDENTICAL** | Step 718 `_TERMINAL_MARKET(rule="collision", replace=True)` identical. |
| **Deficit Fronting** | **IDENTICAL** | `front_money_deficit = 4500.0`, `front_on_near = True` identical. |
| **Opponent State Classifiers** | **ABSENT** | Zero opponent models, zero wallet tracking, zero replay fingerprinting. |

---

## 3. Semantic Code Modification Analysis

* **File**: `candidates/v54_plus_residual.py`
* **Target Symbol**: `_CONFIG`
* **Old Behavior**:
  - `preempt_money_deficit = 4000.0`
  - `preempt_minimum_delta = 8.0`
  - `preempt_maximum_batch = 8`
* **New Behavior**:
  - `preempt_money_deficit = 2000.0`
  - `preempt_minimum_delta = 4.0`
  - `preempt_maximum_batch = 12`
* **Causal Rationale**:
  Expands preemption sensitivity by lowering the required revenue delta threshold from $\$8.0$ to $\$4.0$, lowering the deficit threshold from $\$4,000$ to $\$2,000$, and allowing up to 12 units to be preempted per batch. This allows the agent to lock in strawberry and milk prices 1 tick earlier when market competition emerges.
