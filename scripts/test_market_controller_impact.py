# SPDX-License-Identifier: MIT
"""
Deterministic Unit Test for Tier-9 Market Controller:
Validating Order Construction, Impact Calculation, Price Sensitivity,
Sell Priority, In-Place Queue Preservation, and Feed-Buy Protection.
"""

import math
import copy

# Engine market parameters (exact from kaggriculture engine)
_I0 = 10000
_PRICE_FLOOR = 1
_MP = {
    "WHEAT": (25, 400, "sqrt", 0.80, "log", 0.20),
    "CARROT": (35, 450, "log", 0.20, "sqrt", 0.70),
    "TOMATO": (60, 200, "linear", 0.40, "sqrt", 0.60),
    "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON": (250, 300, "log", 0.20, "sq", 3.60),
    "EGG": (50, 332, "linear", 0.40, "log", 0.20),
    "MILK": (160, 122, "sqrt", 0.60, "linear", 1.60),
    "WOOL": (200, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40),
}

def _mshape(func, x):
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return math.sqrt(x)
    if func == "log10":
        return math.log10(1.0 + x)
    return math.log(1.0 + x)

def _mprice(item, inventory):
    base, throughput, below_f, below_t, above_f, above_t = _MP[item]
    if inventory < _I0:
        amp = below_t * base / _mshape(below_f, throughput)
        value = base + amp * _mshape(below_f, _I0 - inventory)
    else:
        amp = above_t * base / _mshape(above_f, throughput)
        value = base - amp * _mshape(above_f, inventory - _I0)
    return max(_PRICE_FLOOR, int(round(value)))

def calculate_impact(item, qty, inv=10000):
    p_before = _mprice(item, inv)
    p_after = _mprice(item, inv + qty)
    impact = qty * (p_before - p_after)
    return p_before, p_after, impact

def test_market_controller():
    print("=" * 80)
    print("DETERMINISTIC MARKET CONTROLLER MECHANICS AUDIT")
    print("=" * 80)

    # 1. Price Sensitivity & Impact Gradient for Realistic Batch Sizes
    print("\n--- 1. Impact Gradient for Typical Production Batch Sizes ---")
    batch_sizes = {
        "MILK": 12,
        "WOOL": 10,
        "STRAWBERRY": 20,
        "MELON": 24,
        "TOMATO": 15,
        "EGG": 10,
        "CARROT": 15,
        "WHEAT": 10
    }
    impacts = []
    for item, qty in batch_sizes.items():
        p0, p1, imp = calculate_impact(item, qty, _I0)
        impacts.append((imp, item, qty, p0, p1))
        print(f"Item: {item:12s} (Batch: {qty:2d}) | P_initial: {p0:4d} | P_after({qty:2d}): {p1:4d} | Impact Metric: {imp:6.1f} coins")
    
    impacts.sort(reverse=True)
    print("\nDerived Priority Queue Ranking (Highest Impact First):")
    for rank, (imp, item, qty, p0, p1) in enumerate(impacts, 1):
        print(f"  Slot {rank}: {item:12s} (Impact Metric: {imp:6.1f})")

    # High-impact production (Milk, Strawberry, Wool, Melon) strictly outrank staple wheat
    assert impacts[-1][1] == "WHEAT", "Wheat must have the lowest impact rating!"
    print("\n[VERIFIED] Livestock & high-value crop goods dominate earlier queue slots over staple wheat.")

    # 2. In-Place Queue Preservation & Feed Buy Protection
    print("\n--- 2. In-Place Replacement & Feed Buy Priority Simulation ---")
    raw_tape = [
        ["SELL", "WHEAT", 10],          # Slot 0: Non-promotable sell (preserves high wheat price for rival)
        ["BUY_PRODUCT", "WHEAT", 4],     # Slot 1: CRITICAL FEED PURCHASE
        ["SELL", "WOOL", 6],            # Slot 2: Promotable sell (lower impact than milk)
        ["SELL", "MILK", 12],           # Slot 3: Promotable sell (higher impact than wool)
        ["BUY_ANIMAL", "COW", 1],       # Slot 4: Animal purchase
    ]
    
    _PROMOTE = ('MILK', 'WOOL', 'STRAWBERRY', 'MELON', 'EGG', 'TOMATO', 'CARROT', 'FERTILIZER')
    def is_sell(o):
        return isinstance(o, list) and o and o[0] == "SELL"
    def promotable(o):
        return is_sell(o) and o[1] in _PROMOTE

    keep = raw_tape
    promotable_orders = [o for o in keep if promotable(o)]
    def prio(o):
        _, _, imp = calculate_impact(o[1], o[2])
        return imp
    promotable_orders.sort(key=prio, reverse=True)

    # In-place refill: sorted promotable sells refill the slots that already held promotable sells
    queue = list(promotable_orders)
    in_place_output = []
    for order in keep:
        in_place_output.append(queue.pop(0) if (promotable(order) and queue) else order)
    in_place_output.extend(queue)

    print("Raw Tape Order Sequence:")
    for idx, o in enumerate(raw_tape):
        print(f"  Slot {idx}: {o}")

    print("\nIn-Place Refilled Sequence (Tier-9 Market Controller):")
    for idx, o in enumerate(in_place_output):
        print(f"  Slot {idx}: {o}")

    # Check invariants
    assert in_place_output[0] == ["SELL", "WHEAT", 10], "Slot 0 non-promotable wheat sell stays in place!"
    assert in_place_output[1] == ["BUY_PRODUCT", "WHEAT", 4], "Feed purchase in slot 1 MUST NOT BE MOVED OR DISPLACED!"
    assert in_place_output[2] == ["SELL", "MILK", 12], "Slot 2 (promotable) must be promoted to MILK (higher impact)!"
    assert in_place_output[3] == ["SELL", "WOOL", 6], "Slot 3 (promotable) takes WOOL (lower impact)!"
    assert in_place_output[4] == ["BUY_ANIMAL", "COW", 1], "Animal purchase in slot 4 MUST NOT BE MOVED!"
    print("\n[VERIFIED] In-place replacement reordered promotable slots (Milk in Slot 2 ahead of Wool in Slot 3) while keeping BUY_PRODUCT WHEAT locked in Slot 1 and non-promotable Wheat in Slot 0.")

    # 3. Two-Player Simultaneous Market Resolution Price Delta
    print("\n--- 3. Two-Player Simultaneous Order Execution Simulation ---")
    # Scenario: Both P0 and P1 produce 12 Milk and 6 Wool on turn 240.
    # P0 uses Raw Tape: Slot 0 = Wool 6, Slot 1 = Milk 12
    # P1 uses Impact-Sorted: Slot 0 = Milk 12, Slot 1 = Wool 6
    
    inv_milk = 10000
    inv_wool = 10000

    # Slot 0:
    # P0 sells 6 Wool
    p0_wool_price_raw = _mprice("WOOL", inv_wool)
    p0_wool_rev_raw = 6 * p0_wool_price_raw
    inv_wool += 6

    # P1 sells 12 Milk (Impact sorted!)
    p1_milk_price_opt = _mprice("MILK", inv_milk)
    p1_milk_rev_opt = 12 * p1_milk_price_opt
    inv_milk += 12

    # Slot 1:
    # P0 sells 12 Milk (After P1 already dumped 12 Milk into market!)
    p0_milk_price_raw = _mprice("MILK", inv_milk)
    p0_milk_rev_raw = 12 * p0_milk_price_raw
    inv_milk += 12

    # P1 sells 6 Wool (After P0 dumped 6 Wool into market)
    p1_wool_price_opt = _mprice("WOOL", inv_wool)
    p1_wool_rev_opt = 6 * p1_wool_price_opt
    inv_wool += 6

    p0_total_raw = p0_wool_rev_raw + p0_milk_rev_raw
    p1_total_opt = p1_milk_rev_opt + p1_wool_rev_opt
    delta = p1_total_opt - p0_total_raw

    print(f"P0 (Raw Tape)       : Wool Rev = ${p0_wool_rev_raw} (P={p0_wool_price_raw}), Milk Rev = ${p0_milk_rev_raw} (P={p0_milk_price_raw}) -> Total = ${p0_total_raw}")
    print(f"P1 (Impact-Sorted)  : Milk Rev = ${p1_milk_rev_opt} (P={p1_milk_price_opt}), Wool Rev = ${p1_wool_rev_opt} (P={p1_wool_price_opt}) -> Total = ${p1_total_opt}")
    print(f"Single-Turn Advantage for Impact-Sorting: +${delta:.2f} coins")
    assert delta > 0, "Impact sorting must yield strictly higher revenue against raw order queue!"
    print(f"\n[MATHEMATICALLY VERIFIED] Impact sorting captures +${delta:.2f} single-turn price advantage in simultaneous multi-agent resolution.")

if __name__ == "__main__":
    test_market_controller()
