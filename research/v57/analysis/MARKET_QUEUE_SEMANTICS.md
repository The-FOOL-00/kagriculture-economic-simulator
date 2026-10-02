# V57 Market Queue Processor Semantics: kaggle-environments 1.32.7

## Executive Summary

This document establishes the exact mathematical and operational semantics of the shared market transaction queue in official `kaggle-environments` 1.32.7 (`kaggle_environments.envs.kaggriculture.kaggriculture`), specifically `_process_market`, `_parse_order`, and `_commit_unit`.

---

## 1. Official Implementation Source Code Analysis

The authoritative implementation from `kaggle-environments/envs/kaggriculture/kaggriculture.py` (lines 544–680):

```python
def _process_market(state, env):
    """Per-unit lockstep: at each step, quote both players' current-unit prices, then commit both."""
    obs0 = state[0].observation
    market = obs0.market
    farms = obs0.farms
    privates = [s.observation.private for s in state]
    board_size = int(get(env.configuration, "boardSize", 10))
    max_orders = max(1, int(get(env.configuration, "maxMarketOrdersPerTurn", 10)))
    hire_mult = int(get(env.configuration, "farmHandCostMult", FARM_HAND_COST_MULT))
    shed_capacity = int(get(env.configuration, "shedCapacity", 100))

    queues = []
    for s in state:
        action = s.action if isinstance(s.action, dict) else {}
        m = action.get("market", []) if isinstance(action, dict) else []
        q = list(m) if isinstance(m, list) else []
        queues.append(q[:max_orders])

    max_len = max((len(q) for q in queues), default=0)
    for i in range(max_len):
        order_states = []
        for player_id, q in enumerate(queues):
            ostate = None
            if i < len(q):
                ostate = _parse_order(q[i])
            order_states.append(ostate)

        # Atomic orders (HIRE, BUY_LAND): handle once, in player order.
        for player_id, ostate in enumerate(order_states):
            if ostate is None:
                continue
            op = ostate["type"]
            if op == "HIRE":
                _do_hire(farms[player_id], privates[player_id], board_size, hire_mult)
                order_states[player_id] = None
            elif op == "BUY_LAND":
                _do_buy_land(farms[player_id], board_size)
                order_states[player_id] = None

        # Per-unit lockstep loop for SELL / BUY_*.
        idx_esc = 0
        while True:
            idx_esc += 1
            if idx_esc >= 100_000:
                print("WARNING: kaggriculture market loop exceeded 100k iterations; aborting")
                break
            quoted = [None, None]
            for player_id, ostate in enumerate(order_states):
                if ostate is None or ostate["remaining"] <= 0:
                    continue
                op = ostate["type"]
                item = ostate["item"]
                if op == "SELL" and item in PRODUCTS:
                    quoted[player_id] = ("SELL", item, market_price(item, market["inventory"][item], market.get("params")), ostate)
                elif op == "BUY_PRODUCT" and item in ("WHEAT", "FERTILIZER"):
                    quoted[player_id] = ("BUY_PRODUCT", item, market_price(item, market["inventory"][item] - 1, market.get("params")), ostate)
                elif op == "BUY_SEED" and item in CROPS:
                    quoted[player_id] = ("BUY_SEED", item, CROPS[item]["seed"], ostate)
                elif op == "BUY_ANIMAL" and item in ANIMALS:
                    quoted[player_id] = ("BUY_ANIMAL", item, ANIMALS[item]["cost"], ostate)
                else:
                    order_states[player_id] = None  # malformed sub-op; abort

            if all(q is None for q in quoted):
                break

            # Both players see the same pre-commit inventory for this unit.
            committed_any = False
            for player_id, q in enumerate(quoted):
                if q is None:
                    continue
                op, item, price, ostate = q
                ok = _commit_unit(op, item, price, farms[player_id], privates[player_id], market, shed_capacity)
                if ok:
                    ostate["remaining"] -= 1
                    committed_any = True
                else:
                    order_states[player_id] = None  # can't continue this order

            if not committed_any:
                break

        _refresh_prices(market)
```

---

## 2. Answers to Eleven Authoritative Market Processor Semantics Questions

### 1. How order index `i` from player 0 interacts with order index `i` from player 1
The market processor iterates synchronously over indices `i` from `0` to `max_len - 1`. At order index `i`, order `q[0][i]` and order `q[1][i]` are parsed into `order_states[0]` and `order_states[1]`. If both orders are non-atomic (e.g. `SELL` or `BUY`), the engine enters a unit-by-unit while loop. 
- In each unit iteration, prices are quoted for both active players simultaneously against the *pre-commit* market state.
- Then both units are committed: player 0's unit first, then player 1's unit.
- If both players are selling the exact same commodity at index `i`, they receive identical prices for unit 0, both increase the inventory by 1, and in unit 1 they both receive the identical lower price (inventory + 2).
- If they are selling different commodities, their order execution proceeds in unit-by-unit lockstep without cross-contaminating price quotes.

### 2. What happens when one player's list is shorter
When Player A submits fewer orders than Player B (e.g. `len(q_A) < len(q_B)`), for every index `i >= len(q_A)`:
- `order_states[A]` is initialized to `None`.
- `quoted[A]` is `None`.
- Player B's order at index `i` executes completely alone, uncontested, unit-by-unit until completion.
- Once Player B's order finishes, `_refresh_prices` runs and the loop moves to `i + 1`.

### 3. What an empty `[]` entry does
In `_parse_order(order)`:
```python
def _parse_order(order):
    if not isinstance(order, list) or not order:
        return None
```
An empty list `[]` parses directly to `None`. 
In `_process_market`:
- For order index `i`, `order_states[player_id]` becomes `None`.
- `quoted[player_id]` is `None`.
- That player takes zero market actions during order slot `i`.
- The opposing player's order at index `i` executes as if the player submitted nothing for that slot (executes alone).

### 4. Whether an empty entry consumes a market-order slot
**YES.**
The list `queues.append(q[:max_orders])` preserves all elements of `q` up to `max_orders` (10). Index `i` advances one step for every element in `q`. Therefore, `[]` consumes exactly one order index slot in the turn's order array.

### 5. Whether empty entries affect max-10 truncation
**YES.**
`maxMarketOrdersPerTurn` is capped at 10 via `q[:max_orders]`. If an agent submits 10 entries where 1 is `[]` and 9 are valid orders, all 10 entries are retained. If an agent submits 11 entries (e.g. 1 padding + 10 orders), the 11th entry is sliced off and completely dropped.

### 6. Whether quantities are processed one unit at a time
**YES.**
The inner while loop quotes 1 unit per active order and commits 1 unit per active order (`ostate["remaining"] -= 1`), decrementing remaining quantity by 1 each iteration until exhaustion or constraint violation.

### 7. Whether both players receive the same pre-commit price
**YES.**
In the quotation phase:
```python
for player_id, ostate in enumerate(order_states):
    ...
    quoted[player_id] = ("SELL", item, market_price(item, market["inventory"][item], ...), ostate)
```
Both quotes are generated before either player's `_commit_unit` is called. Therefore, if both players are selling the same item at the same unit iteration, both players receive the exact same price.

### 8. When market inventory is modified
Market inventory is modified immediately inside `_commit_unit`:
```python
if op == "SELL":
    if private["shed"].get(item, 0) <= 0:
        return False
    private["shed"][item] -= 1
    farm["money"] += price
    if price > 1:
        market["inventory"][item] += 1
    return True
```
When player 0 commits, `inventory[item]` increments. When player 1 commits, `inventory[item]` increments again. Thus, between unit iterations within the same order slot, inventory changes by the total units committed across both players in that iteration.

### 9. What happens when one order completes before the paired order
If Player 0 orders 2 units and Player 1 orders 5 units:
- In iterations 1 and 2, both players execute 1 unit.
- At iteration 3, Player 0's `ostate["remaining"] <= 0`. Thus `quoted[0]` is `None`.
- Player 1 executes iteration 3, 4, and 5 alone.
- **CRITICAL**: Player 0 does **NOT** advance to order `i + 1` while Player 1 is finishing order `i`! Player 0 remains idle at index `i` until Player 1's order at index `i` is completely finished.

### 10. Whether remaining orders from one player become unpaired
- As long as the slower order at index `i` is executing, the other player is idle.
- When index `i` finishes for both players, the engine increments `i` to `i + 1`.
- If both players have an order at `i + 1`, they pair at `i + 1`.
- If one player has run out of orders (`i + 1 >= len(q)`), the other player's remaining orders become completely unpaired and execute in single-player isolation.

### 11. Whether list padding can change the economics without changing our actual sale quantities
**YES.**
Because order slot pairing is strictly determined by list index `i`:
- Inserting a padding slot `[]` before an order shifts all subsequent orders by +1 index.
- If Player 0 submits `[[], SELL X 5]` and Player 1 submits `[SELL Y 5, SELL X 5]`:
  - At index 0: Player 1 sells Y alone. Player 0 does nothing.
  - At index 1: Player 0 sells X, while Player 1 sells X! They pair on X.
- Conversely, if Player 0 submitted `[SELL X 5]`:
  - At index 0: Player 0 sells X, while Player 1 sells Y! Player 0 sells X *before* Player 1 ever sells X at index 1! Player 0 gets the pre-depression price of X!
- This demonstrates that list padding, order splitting, and positional slot alignment can profoundly alter transaction sequence and market pricing **without changing total economic quantities sold or the turn of execution**.
