# SPDX-License-Identifier: MIT
import os
import sys
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent, assert_frozen

def run_detailed_forensics(seed=249677):
    assert_frozen()
    a7 = load_agent("E9_AST")
    dmitrii = load_agent("E8_DMITRII")
    
    fn_a7 = lambda o, c=None: a7.act(o, c)
    fn_dmitrii = lambda o, c=None: dmitrii.act(o, c)
    
    env = make("kaggriculture", configuration={"seed": seed})
    env.run([fn_a7, fn_dmitrii])
    
    # Analyze Steps 710 to 719
    print("=" * 80)
    print(f"DETAILED TERMINAL FORENSICS (Seed {seed})")
    print("=" * 80)
    
    CROPS = ["WHEAT", "CARROT", "STRAWBERRY", "TOMATO", "MELON"]
    PRODUCTS = ["WHEAT", "CARROT", "STRAWBERRY", "TOMATO", "MELON", "FERTILIZER", "EGG", "MILK", "WOOL"]
    
    # Let's inspect step 711, 712, ..., 719
    for s_idx in range(710, len(env.steps)):
        step_data = env.steps[s_idx]
        obs_a7 = step_data[0]["observation"]
        obs_dm = step_data[1]["observation"]
        act_a7 = step_data[0].get("action") or {}
        act_dm = step_data[1].get("action") or {}
        
        farm_a7 = obs_a7["farms"][0]
        farm_dm = obs_dm["farms"][1]
        priv_a7 = obs_a7.get("private") or {}
        priv_dm = obs_dm.get("private") or {}
        
        mkt = obs_a7.get("market", {})
        prices = mkt.get("prices", {})
        
        m_a7 = farm_a7.get("money", 0)
        m_dm = farm_dm.get("money", 0)
        
        print(f"--- Step {s_idx} | Cash: A7=${m_a7:,.1f}, Dmitrii=${m_dm:,.1f} (Diff={m_a7 - m_dm:+,.1f}) ---")
        print(f"  A7 Market Action: {act_a7.get('market', [])}")
        print(f"  Dm Market Action: {act_dm.get('market', [])}")
        print(f"  A7 Farmer: {act_a7.get('farmer')} | Hands ({len(act_a7.get('hands', []))}): {act_a7.get('hands', [])[:4]}")
        print(f"  Dm Farmer: {act_dm.get('farmer')} | Hands ({len(act_dm.get('hands', []))}): {act_dm.get('hands', [])[:4]}")
        
        shed_a7 = priv_a7.get("shed", {})
        shed_dm = priv_dm.get("shed", {})
        invs_a7 = priv_a7.get("inventories", [])
        invs_dm = priv_dm.get("inventories", [])
        
        carried_a7 = {}
        for inv in invs_a7:
            for k, v in inv.items():
                if v > 0:
                    carried_a7[k] = carried_a7.get(k, 0) + v
        carried_dm = {}
        for inv in invs_dm:
            for k, v in inv.items():
                if v > 0:
                    carried_dm[k] = carried_dm.get(k, 0) + v
                    
        print(f"  A7 Shed: {dict(shed_a7)} | Carried: {carried_a7}")
        print(f"  Dm Shed: {dict(shed_dm)} | Carried: {carried_dm}")

    # Inspect final board state (Step 719)
    last_step = env.steps[-1]
    obs_a7 = last_step[0]["observation"]
    obs_dm = last_step[1]["observation"]
    farm_a7 = obs_a7["farms"][0]
    farm_dm = obs_dm["farms"][1]
    priv_a7 = obs_a7["private"]
    priv_dm = obs_dm["private"]
    prices = obs_a7["market"]["prices"]
    
    print("\n" + "=" * 80)
    print("FINAL STATE AT STEP 719 (EPISODE END)")
    print("=" * 80)
    print(f"Market Prices at Step 719: {prices}")
    
    # Calculate Field Yield Remaining for A7
    tiles_a7 = farm_a7["tiles"]
    field_yield_a7 = {}
    field_value_a7 = 0
    mature_tiles_a7 = []
    for r_idx, row in enumerate(tiles_a7):
        for c_idx, tile in enumerate(row):
            if isinstance(tile, dict):
                y = tile.get("yield_units", 0)
                crop = tile.get("crop")
                animal = tile.get("animal")
                fert = tile.get("fertilizer_available", False)
                if y > 0:
                    item = crop if tile.get("kind") == "PLANT" else (
                        "MILK" if animal == "COW" else ("WOOL" if animal == "SHEEP" else ("EGG" if animal == "GOOSE" else None))
                    )
                    if item:
                        field_yield_a7[item] = field_yield_a7.get(item, 0) + y
                        px = prices.get(item, 0)
                        field_value_a7 += y * px
                        mature_tiles_a7.append(((c_idx, r_idx), item, y, px))
                if fert:
                    field_yield_a7["FERTILIZER"] = field_yield_a7.get("FERTILIZER", 0) + 1
                    field_value_a7 += prices.get("FERTILIZER", 0)
                    mature_tiles_a7.append(((c_idx, r_idx), "FERTILIZER", 1, prices.get("FERTILIZER", 0)))
                    
    # Carried value for A7
    carried_val_a7 = 0
    carried_items_a7 = {}
    for inv in priv_a7["inventories"]:
        for k, v in inv.items():
            if v > 0:
                carried_items_a7[k] = carried_items_a7.get(k, 0) + v
                carried_val_a7 += v * prices.get(k, 0)
                
    # Shed value for A7
    shed_val_a7 = 0
    shed_items_a7 = {}
    for k, v in priv_a7["shed"].items():
        if v > 0:
            shed_items_a7[k] = v
            shed_val_a7 += v * prices.get(k, 0)

    print(f"A7 Final Cash: ${farm_a7['money']:,.2f}")
    print(f"A7 Field Yield Remaining: {field_yield_a7} (Nominal Value: ${field_value_a7:,.2f})")
    print(f"A7 Carried Items Remaining: {carried_items_a7} (Nominal Value: ${carried_val_a7:,.2f})")
    print(f"A7 Shed Remaining: {shed_items_a7} (Nominal Value: ${shed_val_a7:,.2f})")
    
    # Same for Dmitrii
    tiles_dm = farm_dm["tiles"]
    field_yield_dm = {}
    field_value_dm = 0
    for r_idx, row in enumerate(tiles_dm):
        for c_idx, tile in enumerate(row):
            if isinstance(tile, dict):
                y = tile.get("yield_units", 0)
                crop = tile.get("crop")
                animal = tile.get("animal")
                fert = tile.get("fertilizer_available", False)
                if y > 0:
                    item = crop if tile.get("kind") == "PLANT" else (
                        "MILK" if animal == "COW" else ("WOOL" if animal == "SHEEP" else ("EGG" if animal == "GOOSE" else None))
                    )
                    if item:
                        field_yield_dm[item] = field_yield_dm.get(item, 0) + y
                        field_value_dm += y * prices.get(item, 0)
                if fert:
                    field_yield_dm["FERTILIZER"] = field_yield_dm.get("FERTILIZER", 0) + 1
                    field_value_dm += prices.get("FERTILIZER", 0)
                    
    carried_val_dm = 0
    carried_items_dm = {}
    for inv in priv_dm["inventories"]:
        for k, v in inv.items():
            if v > 0:
                carried_items_dm[k] = carried_items_dm.get(k, 0) + v
                carried_val_dm += v * prices.get(k, 0)
                
    shed_val_dm = 0
    shed_items_dm = {}
    for k, v in priv_dm["shed"].items():
        if v > 0:
            shed_items_dm[k] = v
            shed_val_dm += v * prices.get(k, 0)
            
    print(f"\nDmitrii Final Cash: ${farm_dm['money']:,.2f}")
    print(f"Dmitrii Field Yield Remaining: {field_yield_dm} (Nominal Value: ${field_value_dm:,.2f})")
    print(f"Dmitrii Carried Items Remaining: {carried_items_dm} (Nominal Value: ${carried_val_dm:,.2f})")
    print(f"Dmitrii Shed Remaining: {shed_items_dm} (Nominal Value: ${shed_val_dm:,.2f})")
    
    print("\n" + "=" * 80)
    print("MATURE/HARVESTABLE TILES FOR A7 AT STEP 719:")
    for tile_info in mature_tiles_a7:
        print(f"  Pos: {tile_info[0]} | Item: {tile_info[1]} | Qty: {tile_info[2]} | Price: {tile_info[3]} | Subtotal: {tile_info[2]*tile_info[3]}")
        
    print("\nWORKER POSITIONS AND INVENTORIES FOR A7 AT STEP 712 vs 719:")
    # Compare step 712 to 719
    step_712 = env.steps[712][0]["observation"]
    f_712 = step_712["farms"][0]
    p_712 = step_712["private"]
    print(f"Step 712: Farmer pos: {f_712['farmer']}, Hands count: {len(f_712['hands'])}")
    for idx, h_pos in enumerate(f_712['hands']):
        inv = p_712['inventories'][idx + 1]
        print(f"  Hand {idx} at {h_pos}, inv: {inv}")
    print(f"Step 719: Farmer pos: {farm_a7['farmer']}, Hands count: {len(farm_a7['hands'])}")
    for idx, h_pos in enumerate(farm_a7['hands']):
        inv = priv_a7['inventories'][idx + 1]
        print(f"  Hand {idx} at {h_pos}, inv: {inv}")

if __name__ == "__main__":
    run_detailed_forensics(249677)
