import copy
import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

def compile_dairy_continuation():
    with open("extracted_agents/dmitrii_lb2800/actions.json") as f:
        tapes = json.load(f)
        
    tape0 = tapes[0]
    dairy_tape = copy.deepcopy(tape0)
    
    # Window 0 (0..143) is 100% untouched
    # In Window 1 (144..718), optimize market orders for Dairy:
    # 1. Town consumes:
    #    SMOOTHIE: 1 STRAWBERRY, 1 MILK
    #    ICE CREAM: 1 STRAWBERRY, 1 MILK, 1 WHEAT
    #    Combined per 4-step pulse: 2 STRAWBERRY, 2 MILK, 1 WHEAT.
    # 2. Retarget sell orders:
    #    - On step % 4 == 0: place targeted SELL orders:
    #      ['SELL', 'MILK', 2], ['SELL', 'STRAWBERRY', 2], ['SELL', 'WHEAT', 1]
    #    - Ensure morning hires ('HIRE') and wheat feed purchases ('BUY_PRODUCT', 'WHEAT') are NEVER removed!
    #    - On terminal steps (>= 712), keep liquidation intact.
    
    modified_steps = 0
    for step in range(144, 712):
        act = dairy_tape[step]
        orig_market = act.get("market", [])
        
        # Keep all non-SELL orders (HIRE, BUY_ANIMAL, BUY_PRODUCT, BUY_SEED)
        buys = [o for o in orig_market if o and o[0] != "SELL"]
        orig_sells = [o for o in orig_market if o and o[0] == "SELL"]
        
        # New market orders for this step
        new_market = list(buys)
        
        if step % 4 == 0:
            # Town consumption pulse!
            # Prioritize high-value town goods: Milk, Strawberry, Wheat
            new_market.append(["SELL", "MILK", 2])
            new_market.append(["SELL", "STRAWBERRY", 2])
            new_market.append(["SELL", "WHEAT", 1])
            # Also keep any fertilizer or melon sales from original tape
            for s in orig_sells:
                if s[1] in ("MELON", "FERTILIZER", "CARROT", "EGG"):
                    new_market.append(s)
        else:
            # Non-pulse turn: do NOT sell Milk or Strawberry!
            # Only allow essential cash-generating sales (Fertilizer, Melon, Carrot, Egg)
            for s in orig_sells:
                if s[1] in ("MELON", "FERTILIZER", "CARROT", "EGG"):
                    new_market.append(s)
                    
        # Cap at 10 orders
        act["market"] = new_market[:10]
        modified_steps += 1
        
    print(f"Compiled Dairy continuation across {modified_steps} steps (Steps 144..711).")
    
    out_path = "scratch/dairy_specialized_tape.json"
    with open(out_path, "w") as f:
        json.dump(dairy_tape, f)
    print(f"Saved dairy tape to {out_path}")
    return dairy_tape

if __name__ == "__main__":
    compile_dairy_continuation()
