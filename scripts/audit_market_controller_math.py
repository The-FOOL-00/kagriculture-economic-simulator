import math
from pathlib import Path
import sys

# Import functions from candidate_d_aethel_refined
import importlib.util

spec = importlib.util.spec_from_file_location("cand_d", "agents/candidate_d_aethel_refined.py")
cand_d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cand_d)

def run_math_audit():
    print("=" * 80)
    print("AUDITING MARKET CONTROLLER MATH, PRICE CURVES & SORT KEYS")
    print("=" * 80)

    # 1. Test _mprice calculation against manual reference formula
    print("\n--- 1. Testing Price Impact Curve (_mprice) ---")
    items = ["MELON", "STRAWBERRY", "MILK", "WOOL", "WHEAT", "FERTILIZER"]
    
    passed_mprice = True
    for item in items:
        params = cand_d._MP[item]
        base, throughput, below_f, below_t, above_f, above_t = params
        I0 = cand_d._I0
        
        # Test across various inventory levels
        for inv in [0, 5, 10, 15, 20, 30, 50, 100]:
            actual_price = cand_d._mprice(item, inv)
            
            # Recompute manually
            if inv < I0:
                amp = below_t * base / cand_d._mshape(below_f, throughput)
                val = base + amp * cand_d._mshape(below_f, I0 - inv)
            else:
                amp = above_t * base / cand_d._mshape(above_f, throughput)
                val = base - amp * cand_d._mshape(above_f, inv - I0)
            expected_price = max(cand_d._PRICE_FLOOR, int(round(val)))
            
            if actual_price != expected_price:
                print(f"  [FAIL] {item} inv={inv}: actual={actual_price} != expected={expected_price}")
                passed_mprice = False
                
    if passed_mprice:
        print("  >>> _mprice calculation verified 100% correct across all test points.")

    # 2. Test Price Impact Sorting Math
    # Delta Revenue = qty * (P(I) - P(I + qty))
    print("\n--- 2. Testing Price Impact Metric Delta Revenue Formula ---")
    mock_obs = {
        "step": 100,
        "player": 0,
        "farms": [{"money": 1000}, {"money": 1000}],
        "market": {"inventory": {"MELON": 10, "WOOL": 10, "WHEAT": 10, "MILK": 10}},
        "private": {"shed": {"MELON": 5, "WOOL": 5, "WHEAT": 20, "MILK": 5}},
        "town": {"unlocked_shops": []}
    }

    test_orders = [
        ["SELL", "MELON", 5],
        ["SELL", "WOOL", 5],
        ["SELL", "MILK", 5],
        ["SELL", "WHEAT", 20]
    ]

    for ord in test_orders:
        p = cand_d._sell_priority(ord, mock_obs, step=100)
        item = ord[1]
        qty = ord[2]
        inv = mock_obs["market"]["inventory"][item]
        p_now = cand_d._mprice(item, inv)
        p_after = cand_d._mprice(item, inv + qty)
        impact = qty * (p_now - p_after)
        race = cand_d._race_factor(item, 100, mock_obs)
        expected_priority = float(impact * race)
        
        diff = abs(p - expected_priority)
        print(f"  Item: {item:12s} | Qty: {qty:2d} | P(I): {p_now:3d} | P(I+q): {p_after:3d} | dP: {p_now - p_after:2d} | Impact: {impact:5.1f} | Priority: {p:6.2f} (Expected: {expected_priority:6.2f})")
        if diff > 1e-5:
            print(f"    [FAIL] Priority mismatch for {item}!")
            return False
            
    print("  >>> Price Impact priority formula verified 100% exact.")

    # 3. Test Queue In-Place Slot Preservation
    print("\n--- 3. Testing In-Place Slot Preservation Logic ---")
    sample_action = {
        "market": [
            ["SELL", "WOOL", 2],        # Slot 0 (promotable sell)
            ["SELL", "MELON", 1],       # Slot 1 (promotable sell)
            ["BUY_PRODUCT", "WHEAT", 10], # Slot 2 (CRITICAL BUY - MUST NOT BE DISPLACED)
            ["SELL", "MILK", 3],        # Slot 3 (promotable sell)
            ["BUY_ANIMAL", "COW", 1],   # Slot 4 (CRITICAL BUY)
            ["SELL", "WHEAT", 5],       # Slot 5 (unpromotable / protected sell)
        ]
    }

    # Pass through agent market controller
    mock_obs_game = {
        "step": 200,
        "player": 0,
        "farms": [{"money": 5000}, {"money": 5000}],
        "market": {"inventory": {"MELON": 15, "WOOL": 10, "MILK": 10, "WHEAT": 20}},
        "private": {"shed": {"MELON": 1, "WOOL": 2, "MILK": 3, "WHEAT": 5}},
        "town": {"unlocked_shops": []}
    }

    # We mock _base_agent to return sample_action
    cand_d._base_agent = lambda obs, config=None: {
        "farmer": [],
        "hands": [],
        "market": [list(x) for x in sample_action["market"]]
    }
    
    modified_action = cand_d.agent(mock_obs_game)
    mod_market = modified_action["market"]
    
    print("  Original Market Queue:")
    for idx, ord in enumerate(sample_action["market"]):
        print(f"    Slot {idx}: {ord}")
        
    print("\n  Modified Market Queue by Controller:")
    for idx, ord in enumerate(mod_market):
        print(f"    Slot {idx}: {ord}")
        
    # Check that Slot 2 is still BUY_PRODUCT WHEAT and Slot 4 is still BUY_ANIMAL COW
    slot2_ok = (mod_market[2][0] == "BUY_PRODUCT" and mod_market[2][1] == "WHEAT")
    slot4_ok = (mod_market[4][0] == "BUY_ANIMAL" and mod_market[4][1] == "COW")
    
    print(f"\n  Slot 2 (BUY_PRODUCT WHEAT) preserved: {slot2_ok}")
    print(f"  Slot 4 (BUY_ANIMAL COW) preserved: {slot4_ok}")
    
    if slot2_ok and slot4_ok:
        print("  >>> In-place queue preservation verified: Critical buy slots remain untouched.")
        return True
    else:
        print("  >>> FAIL: Critical buy orders were displaced!")
        return False

if __name__ == "__main__":
    ok = run_math_audit()
    if ok:
        print("\nALL MARKET CONTROLLER MATH AND LOGIC CHECKS PASSED (PASS)")
        sys.exit(0)
    else:
        print("\nMARKET CONTROLLER AUDIT FAILED (FAIL)")
        sys.exit(1)
