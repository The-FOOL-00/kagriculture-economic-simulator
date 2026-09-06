import json
import glob
import os

files = glob.glob("scratch/replays/*.json")
print(f"Found {len(files)} replays in scratch/replays")

for fpath in files:
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            d = json.load(f)
        steps = d.get("steps")
        if not steps or len(steps) < 25:
            continue
        
        # Check both players for step 0 / 1 market actions
        # In Kaggle environments replay format:
        # steps[1][p]['action'] contains the action executed at step 0!
        # Or let's check step 0 vs step 1.
        for p in [0, 1]:
            # Look at step 1 action or step 0 action
            act0 = steps[0][p].get("action")
            act1 = steps[1][p].get("action")
            # Let's see which one has the market orders
            mkt0 = act0.get("market") if isinstance(act0, dict) else []
            mkt1 = act1.get("market") if isinstance(act1, dict) else []
            
            # If mkt1 has the opening orders:
            opening_mkt = mkt1 if mkt1 else mkt0
            if opening_mkt and len(opening_mkt) > 3:
                # Count hires, animals, seeds, products
                hires = sum(1 for x in opening_mkt if isinstance(x, list) and x[0] == "HIRE")
                cows = sum(x[2] for x in opening_mkt if isinstance(x, list) and x[0] == "BUY_ANIMAL" and x[1] == "COW")
                sheep = sum(x[2] for x in opening_mkt if isinstance(x, list) and x[0] == "BUY_ANIMAL" and x[1] == "SHEEP")
                melons = sum(x[2] for x in opening_mkt if isinstance(x, list) and x[0] == "BUY_SEED" and x[1] == "MELON")
                wheat_s = sum(x[2] for x in opening_mkt if isinstance(x, list) and x[0] == "BUY_SEED" and x[1] == "WHEAT")
                feed = sum(x[2] for x in opening_mkt if isinstance(x, list) and x[0] == "BUY_PRODUCT" and x[1] == "WHEAT")
                
                # Also check step 2 feed buy if any
                act2 = steps[2][p].get("action")
                mkt2 = act2.get("market") if isinstance(act2, dict) else []
                feed_s2 = sum(x[2] for x in mkt2 if isinstance(x, list) and x[0] == "BUY_PRODUCT" and x[1] == "WHEAT")
                
                # Check cash after day 0 purchases (at step 1 or 2)
                f_obs = steps[1][p]["observation"]["farms"][p]
                money = f_obs.get("money")
                
                fname = os.path.basename(fpath)
                print(f"{fname:45s} P{p} | Hires:{hires} Cows:{cows} Sheep:{sheep} Melons:{melons} WheatSeed:{wheat_s} Feed0:{feed} Feed1:{feed_s2} Cash1:${money}")
    except Exception as e:
        # print(f"Error {fpath}: {e}")
        pass
