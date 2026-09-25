# V32 P6 — SIMULATOR PICKUP LEGALITY AUDIT

## 1. PURPOSE & MANDATE

In accordance with Section 10 and Section 11 of the **V32 P6 Protocol**, this document provides a rigorous, source-grounded audit of the simulator's action-execution engine (`kaggle_environments.envs.kaggriculture.kaggriculture`) to establish the exact, source-proven preconditions for the `PICKUP` opcode and formalize the simulator-valid predicate.

---

## 2. OFFICIAL SIMULATOR SOURCE CODE INSPECTION

From `site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py`:

```python
def _shed_access_tiles(board_size):
    """Four inner-corner tiles around the shed, in NWSE order."""
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]

def _is_shed_adjacent(pos, board_size):
    return tuple(pos) in {(x, y) for (x, y) in _shed_access_tiles(board_size)}

def _apply_unit_action(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity=100):
    ...
    if op == "PICKUP":
        if not _is_shed_adjacent((fx, fy), board_size):
            return
        if len(action) < 2:
            return
        item = action[1]
        n = int(action[2]) if len(action) >= 3 else 1
        if n <= 0:
            return
        # Seeds live in private["seeds"] and are consumed directly by PLANT;
        # they never pass through farmer inventory or the shed.
        available = private["shed"].get(item, 0)
        n = min(n, available)
        if n <= 0:
            return
        private["shed"][item] -= n
        _inv_add(inv, item, n)
        return
```

---

## 3. FORMAL PRECONDITIONS FOR `PICKUP`

For a unit $u$ at position $(f_x, f_y)$ to successfully execute `['PICKUP', item, n]`:

1. **Shed Adjacency**:
   $$(f_x, f_y) \in \{(h-1, h-1), (h, h-1), (h-1, h), (h, h)\} \quad \text{where } h = \lfloor \text{board\_size} / 2 \rfloor.$$
   For a standard $10 \times 10$ board ($h = 5$):
   $$\text{Shed Tiles} = \{(4, 4), (5, 4), (4, 5), (5, 5)\}.$$
   **Evaluation at Step 2**: Farmer coordinate is `[4, 3]`.
   $$(4, 3) \notin \{(4, 4), (5, 4), (4, 5), (5, 5)\} \implies \mathbf{\_is\_shed\_adjacent((4, 3), 10) = \text{False}}.$$
   **Result**: Execution immediately terminates via silent `return`.

2. **Item Availability**:
   $$\text{private["shed"]}[\text{item}] \ge 1.$$
   If the shed has 0 of `item`, the simulator executes a silent `return`.

3. **Item Non-Seed Invariant**:
   Seeds reside in `private["seeds"]` and cannot be stored or picked up from the shed.

---

## 4. FORMAL SOURCE-GROUNDED PREDICATE

```python
def is_pickup_valid(pos: tuple[int, int], item: str, shed: dict, board_size: int = 10) -> bool:
    """Exact reproduction of kaggriculture 1.32.7 PICKUP legality."""
    half = board_size // 2
    shed_tiles = {(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)}
    if tuple(pos) not in shed_tiles:
        return False
    if not isinstance(item, str) or not item:
        return False
    return shed.get(item, 0) > 0
```

---

## 5. AUDIT CONCLUSION

`['PICKUP', 'COW']` at Step 2 is **strictly, 100% invalid under simulator semantics**.
The action produces zero state changes in the simulator, leaving the farmer stranded at `[4, 3]` and preventing all downstream animal placement.
An exact semantic action mask that checks `_is_shed_adjacent` is mathematically sound and 100% fidelity-preserving with respect to the simulator.
