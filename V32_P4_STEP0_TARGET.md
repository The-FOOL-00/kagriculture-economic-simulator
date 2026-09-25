# V32 P4 STEP-0 TARGET SPECIFICATION & SEMANTICS

## 1. Native Action Object at Step 0

Across all 120 recorded expert legs (240 seat-trajectories), step 0 actions for all four teachers have been audited directly from `results/v32_p2_bc_legs.jsonl`.

### 1.1 State Identicality
At step 0, both players start with:
- `money = 1000.0`
- `hands = []` (0 hired hands)
- `shed = {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0, "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 0, "GOOSE": 0, "COW": 0, "SHEEP": 0}` (empty shed)
- `seeds = {"WHEAT": 1, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0}`
- Normalizer output feature vector `feat`: maximum absolute difference across all 240 step-0 samples is **0.0000** (bit-identical inputs across all legs, seeds, and seats).

### 1.2 Expert Action Ground Truth at Step 0

Every teacher at step 0 emits:
- `farmer`: `["PASS"]` (all 4 teachers match: 240/240)
- `hands`: `[]` (no hands spawned yet: 240/240)
- `market`: exactly 2 active orders, followed by empty slots (all 4 teachers match: 240/240):
  - Slot 0: `["BUY_PRODUCT", "WHEAT", n]`
  - Slot 1: `["SELL", "WHEAT", m]`
  - Slots 2..9: `[]` (NOOP)

Specific teacher parameter literals:
| Teacher | Slot 0 Order | Slot 1 Order | Remaining Slots (2..9) | Farmer Action | Hands Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **E2_A7** | `["BUY_PRODUCT", "WHEAT", 30]` | `["SELL", "WHEAT", 30]` | `[]` (NOOP) | `["PASS"]` | `[]` |
| **E0_V3** | `["BUY_PRODUCT", "WHEAT", 50]` | `["SELL", "WHEAT", 50]` | `[]` (NOOP) | `["PASS"]` | `[]` |
| **E7_W2015** | `["BUY_PRODUCT", "WHEAT", 20]` | `["SELL", "WHEAT", 15]` | `[]` (NOOP) | `["PASS"]` | `[]` |
| **E6_W72** | `["BUY_PRODUCT", "WHEAT", 7]` | `["SELL", "WHEAT", 2]` | `[]` (NOOP) | `["PASS"]` | `[]` |

Unanimous structure across all 240 step-0 expert actions:
```python
action = {
    "farmer": ["PASS"],
    "hands": [],
    "market": [
        ["BUY_PRODUCT", "WHEAT", qty_buy],
        ["SELL", "WHEAT", qty_sell]
    ]
}
```

## 2. Simulator Semantics: Why Slot Reversal is CATASTROPHIC, Not Equivalent

In Kagriculture (`kaggriculture.py` `_process_market`, lines 544–560), market orders are executed sequentially by slot index $s \in \{0, \dots, 9\}$ across players:

### 2.1 Canonical Execution `[BUY, SELL]`
1. **Turn Start (Step 0)**:
   - Player shed has **0 WHEAT**.
   - Money = $1000.
2. **Slot 0 Execution (`BUY_PRODUCT WHEAT 30`)**:
   - Player purchases 30 wheat at base market quote.
   - Shed inventory increases: `shed["WHEAT"] = 30`.
   - Money decreases: `money = 1000 - cost`.
   - Market price of wheat increases due to demand.
3. **Slot 1 Execution (`SELL WHEAT 30`)**:
   - Player sells 30 wheat from the shed.
   - Because `shed["WHEAT"] == 30`, the order is valid and executes at the newly inflated post-buy price!
   - Money increases: `money += revenue`.
   - Player nets cash profit or locks in the opening wash liquidity.

### 2.2 Reversal Failure Mode `[SELL, BUY]` (Observed in P3 BC)
1. **Turn Start (Step 0)**:
   - Player shed has **0 WHEAT**.
2. **Slot 0 Execution (`SELL WHEAT 30`)**:
   - Player attempts to sell 30 wheat.
   - Simulator checks shed inventory: `inventory.get("WHEAT", 0) == 0`.
   - Under simulator partial-fill / clamp rules (`_apply_market_order`), quantity is clamped to available inventory: $\min(30, 0) = 0$.
   - **Result**: Exactly **0 units sold**, $0 cash received. The order is a complete void no-op!
3. **Slot 1 Execution (`BUY_PRODUCT WHEAT 30`)**:
   - Player executes `BUY_PRODUCT WHEAT 30`.
   - Opponent (e.g. A7) executed `BUY_PRODUCT` in slot 0, inflating prices.
   - Player buys 30 wheat at high inflated prices, spending ~$750 capital.
   - Player is left with depleted cash ($~250) and 30 wheat that was NEVER washed.
   - Terminal economics: Drift and collapse ($467 vs $91k).

### 2.3 Verdict on Reversal
`[SELL30, BUY30]` is **NOT** an equivalent encoding. It is a fatal operational error caused by slot-order confusion.
Slot ordering in the market array is strictly causal and sequential.
The required critical market configuration is:
- **Slot 0**: `BUY_PRODUCT` on `WHEAT`
- **Slot 1**: `SELL` on `WHEAT`
- **Slots 2–9**: `NOOP`
