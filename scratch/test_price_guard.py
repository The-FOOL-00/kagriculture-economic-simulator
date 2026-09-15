import sys
import copy
from kaggle_environments import make

# Let's see what happens if we add a minimum sell price threshold to candidate_cl_economic_v2
with open("candidates/candidate_cl_economic_v2.py", "r") as f:
    code = f.read()

# Replace the sell condition to check price floor
old_sell = """            if qty > 0:
                p_val = float(prices.get(item, BASE_PRICES.get(item, 100)) or 100)
                sells.append((qty * p_val, item, qty))"""

new_sell = """            if qty > 0:
                p_val = float(prices.get(item, BASE_PRICES.get(item, 100)) or 100)
                # Dynamic Price Reservation Floor: Never dump high-value assets into severe gluts!
                min_p = BASE_PRICES.get(item, 100) * 0.65 if day < 28 else 1.0
                if p_val >= min_p:
                    sells.append((qty * p_val, item, qty))"""

assert old_sell in code, "old_sell string not found"
code_patched = code.replace(old_sell, new_sell)

with open("scratch/cand_v2_price_guard.py", "w") as f:
    f.write(code_patched)

print("Created scratch/cand_v2_price_guard.py. Running Seed 1004...")

cfg = {"episodeSteps": 720, "seed": 1004}
env = make("kaggriculture", configuration=cfg, debug=False)
env.run(["scratch/cand_v2_price_guard.py", "starter"])

reward = env.steps[-1][0].reward
print(f"Seed 1004 Reward with Price Guard: ${reward:,.0f} (vs $86,548 without guard)")
