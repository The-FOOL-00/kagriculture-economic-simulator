import json
import re
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NB_PATH = os.path.join(BASE_DIR, "scratch", "kernels", "yhay81__three-day-shop-router", "three-day-shop-router.ipynb")

_UNIT_OPS = (
    "PASS", "NORTH", "SOUTH", "EAST", "WEST", "PICKUP", "DROP",
    "PLACE", "PLANT", "WATER", "HARVEST", "FERTILIZE", "DIG",
    "BUILD_COOP", "BUILD_PASTURE", "FEED", "COLLECT_FERTILIZER", "CARE",
)
_MARKET_OPS = ("PASS", "HIRE", "BUY_LAND", "BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL", "SELL")
_ITEMS = (
    "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG",
    "MILK", "WOOL", "FERTILIZER", "GOOSE", "COW", "SHEEP",
)

def decode_action_str(encoded):
    tokens = [int(x) for x in encoded.strip().split()]
    if not tokens:
        return {"farmer": ["PASS"], "hands": [], "market": []}
    n_units = tokens[0]
    n_orders = tokens[1]
    idx = 2
    units = []
    for _ in range(n_units):
        op = tokens[idx]
        arg = tokens[idx+1]
        qty = tokens[idx+2]
        idx += 3
        name = _UNIT_OPS[op] if 0 <= op < len(_UNIT_OPS) else "PASS"
        if name in {"PLANT", "PICKUP", "PLACE"}:
            item = _ITEMS[arg] if 0 <= arg < len(_ITEMS) else _ITEMS[0]
            units.append([name, item] if qty == 1 else [name, item, int(qty)])
        else:
            units.append([name])
            
    farmer = units[0] if units else ["PASS"]
    hands = units[1:] if len(units) > 1 else []
    
    market = []
    for _ in range(n_orders):
        op = tokens[idx]
        item = tokens[idx+1]
        qty = tokens[idx+2]
        idx += 3
        name = _MARKET_OPS[op] if 0 <= op < len(_MARKET_OPS) else "PASS"
        if name != "PASS":
            if name in {"HIRE", "BUY_LAND"}:
                market.append([name])
            else:
                item_name = _ITEMS[item] if 0 <= item < len(_ITEMS) else _ITEMS[0]
                market.append([name, item_name, int(qty)])
                
    return {"farmer": farmer, "hands": hands, "market": market}

def extract_tapes():
    with open(NB_PATH, encoding="utf-8") as f:
        nb = json.load(f)
    tape_cell = None
    for cell in nb["cells"]:
        src = "".join(cell.get("source", []))
        if "const char* const kEncodedTapes" in src:
            tape_cell = src
            break
    if not tape_cell:
        raise ValueError("kEncodedTapes not found in notebook!")
        
    pattern = re.compile(r'\{\s*"([^"]+)"', re.DOTALL)
    # Extract all quoted string literals inside kEncodedTapes
    lines = tape_cell.splitlines()
    tape0_lines = []
    tape1_lines = []
    current_route = -1
    
    for l in lines:
        if "kEncodedTapes" in l:
            current_route = 0
            # get string literals on this line
        if current_route >= 0:
            strs = re.findall(r'"([^"]*)"', l)
            for s in strs:
                if current_route == 0:
                    tape0_lines.append(s)
                    if len(tape0_lines) == 719:
                        current_route = 1
                elif current_route == 1:
                    tape1_lines.append(s)
                    if len(tape1_lines) == 719:
                        current_route = 2
                        break
                        
    print(f"Extracted Route 0: {len(tape0_lines)} turns, Route 1: {len(tape1_lines)} turns")
    
    decoded_tapes = []
    for route_idx, tape_raw in enumerate([tape0_lines, tape1_lines]):
        route_actions = []
        for step, raw in enumerate(tape_raw):
            route_actions.append(decode_action_str(raw))
        decoded_tapes.append(route_actions)
        
    out_json = os.path.join(BASE_DIR, "scratch", "yhay81_three_day_router_tapes.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(decoded_tapes, f)
    print(f"Saved decoded tapes to {out_json}")
    return decoded_tapes

if __name__ == "__main__":
    extract_tapes()
