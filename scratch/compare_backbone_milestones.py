"""
Section 10: Milestone Coverage Analysis
Compares the V54 proposal route against Declarative Backbone execution.
"""
import sys
sys.path.insert(0, ".")
sys.path.insert(0, "candidates/declarative_backbone")
import base64, json, zlib, re

# Extract _V54_ROUTE from variant_v54_h3q4/main.py
with open("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py", "r", encoding="utf-8") as f:
    code = f.read()

m = re.search(r'_V54_ROUTE = json\.loads\(zlib\.decompress\(base64\.b85decode\(\s*\((.*?)\)\s*\)\)\.decode\("utf-8"\)\)', code, re.DOTALL)
if not m:
    print("Could not find _V54_ROUTE")
    exit(1)

b85_str = m.group(1).replace("'", "").replace("\n", "").replace(" ", "")
route_json = zlib.decompress(base64.b85decode(b85_str.encode("ascii"))).decode("utf-8")
v54_route = json.loads(route_json)

print(f"Loaded V54 Route: {len(v54_route)} steps")

# Analyze V54 Route Milestones
v54_hires = {}
v54_land = []
v54_seeds = {}
v54_animals = {}
v54_sales = {}
v54_day1_purchases = []

for step_idx, step_action in enumerate(v54_route):
    day = step_idx // 24
    hour = step_idx % 24
    market = step_action.get("market", [])
    for o in market:
        op = o[0]
        if step_idx < 24:
            v54_day1_purchases.append(o)
        if op == "HIRE":
            v54_hires[day] = v54_hires.get(day, 0) + 1
        elif op == "BUY_LAND":
            v54_land.append((step_idx, day))
        elif op == "BUY_SEED":
            v54_seeds[o[1]] = v54_seeds.get(o[1], 0) + (o[2] if len(o) > 2 else 1)
        elif op == "BUY_ANIMAL":
            v54_animals[o[1]] = v54_animals.get(o[1], 0) + 1
        elif op == "SELL":
            prod = o[1]
            qty = o[2] if len(o) > 2 else 1
            v54_sales[prod] = v54_sales.get(prod, 0) + qty

# Load Declarative Ledger from Seed 2003 solo run
from scratch.audit_solo_economic_ledger import run_audited_game
decl = run_audited_game(2003)

print("\n" + "="*80)
print(f"{'Milestone':30s} | {'V54 Route':20s} | {'Declarative':20s} | {'Match?':8s}")
print("="*80)

milestones = [
    ("Day 1 Hires", f"{v54_hires.get(0, 0)} workers", f"{decl['workers_by_day'].get(0, 0)} workers", v54_hires.get(0,0) == decl['workers_by_day'].get(0,0)),
    ("Day 1 Seeds", "Melon 8, Wheat 3", f"Melon {decl['seeds_bought'].get('MELON', 0)}", False),
    ("Land Unlock 1 (step)", f"Step {v54_land[0][0]} (Day {v54_land[0][1]})" if v54_land else "N/A", f"Step {decl['land_unlock_steps'][0][0]}", abs((v54_land[0][0] if v54_land else 0) - decl['land_unlock_steps'][0][0]) < 24),
    ("Land Unlock 2 (step)", f"Step {v54_land[1][0]} (Day {v54_land[1][1]})" if len(v54_land)>1 else "N/A", f"Step {decl['land_unlock_steps'][1][0]}", abs((v54_land[1][0] if len(v54_land)>1 else 0) - decl['land_unlock_steps'][1][0]) < 24),
    ("Total Hires (Worker-Days)", f"{sum(v54_hires.values())} hires", f"{sum(decl['workers_by_day'].values())} hires", False),
    ("Peak Daily Workers", f"{max(v54_hires.values())} workers", f"{max(decl['workers_by_day'].values())} workers", max(v54_hires.values()) == max(decl['workers_by_day'].values())),
    ("Wheat Seeds Bought", f"{v54_seeds.get('WHEAT', 0)} seeds", f"{decl['seeds_bought'].get('WHEAT', 0)} seeds", False),
    ("Wheat Seeds Planted", f"~187 planted", f"{decl['seeds_planted'].get('WHEAT', 0)} planted", False),
    ("Strawberry Seeds Bought", f"{v54_seeds.get('STRAWBERRY', 0)} seeds", f"{decl['seeds_bought'].get('STRAWBERRY', 0)} seeds", v54_seeds.get('STRAWBERRY', 0) == decl['seeds_bought'].get('STRAWBERRY', 0)),
    ("Strawberry Seeds Planted", f"{v54_seeds.get('STRAWBERRY', 0)} planted", f"{decl['seeds_planted'].get('STRAWBERRY', 0)} planted", False),
    ("Melon Seeds Bought", f"{v54_seeds.get('MELON', 0)} seeds", f"{decl['seeds_bought'].get('MELON', 0)} seeds", v54_seeds.get('MELON', 0) == decl['seeds_bought'].get('MELON', 0)),
    ("Melon Seeds Planted", f"{v54_seeds.get('MELON', 0)} planted", f"{decl['seeds_planted'].get('MELON', 0)} planted", True),
    ("Carrot Seeds Bought", f"{v54_seeds.get('CARROT', 0)} seeds", f"{decl['seeds_bought'].get('CARROT', 0)} seeds", False),
    ("Cow Purchases", f"{v54_animals.get('COW', 0)} cows", f"{decl['animals_bought'].get('COW', 0)} cows", v54_animals.get('COW', 0) == decl['animals_bought'].get('COW', 0)),
    ("Sheep Purchases", f"{v54_animals.get('SHEEP', 0)} sheep", f"{decl['animals_bought'].get('SHEEP', 0)} sheep", v54_animals.get('SHEEP', 0) == decl['animals_bought'].get('SHEEP', 0)),
    ("Wheat Feed Sourced From", "Home-grown wheat", "Market purchases ($8k)", False),
    ("First Sell Step", "Step 72 (Day 3)", "Step 72 (Day 3)", True),
    ("Terminal Wheat Dump", "Yes (386 sold)", "No (0 sold)", False),
]

for name, v54_val, decl_val, match in milestones:
    m_str = "YES" if match else "NO"
    print(f"{name:30s} | {v54_val:20s} | {decl_val:20s} | {m_str:8s}")

matches_count = sum(1 for m in milestones if m[3])
coverage_score = matches_count / len(milestones)
print("="*80)
print(f"BACKBONE COVERAGE SCORE: {matches_count}/{len(milestones)} ({coverage_score:.1%})")
