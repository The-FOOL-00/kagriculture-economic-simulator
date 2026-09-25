# V32 P6 — SOURCE-GROUNDED SEMANTIC ACTION MASK

## 1. DESIGN SPECIFICATION & ARCHITECTURAL PLACEMENT

In accordance with Section 12 and Section 13 of the **V32 P6 Protocol**, this document specifies the source-grounded semantic action mask layer implemented in [`v32/p6/mask.py`](file:///c:/Users/Sundareswaran/Kagriculture/v32/p6/mask.py).

The mask operates as an exact semantic constraint layer between raw neural logits and categorical action sampling/argmax decoding:

```text
Observable State (Observation / Essentials)
        ↓
Structured Temporal Features & Unit Context
        ↓
Shared MLP Trunk & Factorized Heads
        ↓
Raw Farmer / Unit Opcode Logits z \in R^{18}
        ↓
Semantic Action Validity Mask m \in {0, 1}^{18}
        ↓
Masked Logits: z_i' = z_i if m_i == 1 else -1e9
        ↓
Categorical Argmax / Sampling
        ↓
Simulator-Grounded Action Literal
```

---

## 2. SOURCE-PROVEN VALIDITY RULES

Every predicate is derived strictly from `_apply_unit_action`, `_is_shed_adjacent`, and `_shed_access_tiles` in official `kaggriculture 1.32.7`:

1. **`PASS`**: Always valid ($m_0 = 1$).
2. **Directional Moves (`NORTH`, `SOUTH`, `EAST`, `WEST`)**:
   $$m_{\text{dir}} = 1 \iff 0 \le f_x + dx < \text{board\_size} \text{ and } 0 \le f_y + dy < \text{board\_size}.$$
3. **`DROP`**:
   $$m_{\text{DROP}} = 1 \iff \_is\_shed\_adjacent((f_x, f_y), \text{board\_size}) \text{ and } \sum \text{inventory} > 0.$$
4. **`PICKUP`**:
   $$m_{\text{PICKUP}} = 1 \iff \_is\_shed\_adjacent((f_x, f_y), \text{board\_size}) \text{ and } \sum \text{shed} > 0.$$
5. **Tile Construction / Agriculture Operations**:
   - `BUILD_COOP`, `BUILD_PASTURE`, `PLANT`: Standing on unworked empty tile.
   - `WATER`, `FERTILIZE`: Standing on plant tile.
   - `HARVEST`: Standing on mature crop or livestock with positive yield.
   - `FEED`, `CARE`, `COLLECT_FERTILIZER`: Standing on livestock structure.
   - `PLACE`: Standing on matching livestock structure, or shed-adjacent with animal in inventory.

---

## 3. VERIFICATION & DISCREPANCY AUDIT

Verified via `tests/test_v32_p6_semantic_mask.py`:
- 100/100 grid tiles tested for shed adjacency match: **0 discrepancies**.
- Step 2 farmer coordinate `[4, 3]`: **`PICKUP` strictly masked ($m_{\text{PICKUP}} = 0$)**.
- Step 2 hand coordinate `[4, 4]`: **`PICKUP` allowed ($m_{\text{PICKUP}} = 1$)**.
- Boundary clipping: **100% matched**.
- State mutation equivalence test against simulator `_apply_unit_action`: **0 false positives, 0 false negatives**.
