import os, sys, json
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "scratch"))
import kagsim
import router_parent as mod_r
from test_tomato_with_sales import TomatoSpecialistV1

# Compare winning seed 50026 vs losing seed 50003
for s, label in [(50026, "WINNING SEED 50026"), (50003, "LOSING SEED 50003")]:
    print(f"\n=== {label} ===")
    g = kagsim.Game(s)
    p_tom = TomatoSpecialistV1(sale_batch=6)
    p_dmi = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    
    # Track units harvested and sold
    sales = {}
    while not g.done:
        step = g.observe(0)["step"]
        a0 = p_tom.act(g.observe(0))
        a1 = p_dmi.act(g.observe(1))
        for m in a0.get("market", []):
            if m and m[0] == "SELL":
                # Only if executed? We will track post-step cash
                pass
        g.step(a0, a1)
        
    obs0 = g.observe(0)
    print(f"Final Cash: ${g.reward(0):,.0f} vs Dmitrii ${g.reward(1):,.0f}")
    print(f"Shops: {obs0['town']['unlocked_shops']}")
    print(f"Tiles: {sum(1 for r in obs0['farms'][0]['tiles'] for t in r if isinstance(t, dict) and t.get('crop') == 'TOMATO')} tomatoes remaining")
    print(f"Weeds: {sum(1 for r in obs0['farms'][0]['tiles'] for t in r if isinstance(t, dict) and t.get('kind') == 'WEED')}")
