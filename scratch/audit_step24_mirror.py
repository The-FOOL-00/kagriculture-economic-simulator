"""
scratch/audit_step24_mirror.py
Inspect Step 0 to Step 25 in V2 vs V2 Mirror match to see why liquidity differs from solo/starter play.
"""
import sys
import os
sys.path.insert(0, os.path.abspath("."))
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2

def audit_step24():
    env = kaggle_environments.make("kaggriculture", configuration={"seed": 1200, "episodeSteps": 720}, debug=False)
    env.reset()
    
    for step in range(30):
        obs0 = env.state[0].observation
        obs1 = env.state[1].observation
        
        act0 = v2.agent(obs0)
        act1 = v2.agent(obs1)
        
        farm0 = obs0["farms"][0]
        farm1 = obs1["farms"][1]
        mkt = obs0.get("market", {})
        prices = mkt.get("prices", {})
        
        if step in (0, 1, 23, 24, 25):
            print(f"\n--- STEP {step} ---")
            print(f"P0 Money: ${farm0.get('money')} | P1 Money: ${farm1.get('money')}")
            print(f"Prices: Wheat={prices.get('WHEAT')}, Melon={prices.get('MELON')}, Fertilizer={prices.get('FERTILIZER')}")
            print(f"P0 Act Market: {act0.get('market')}")
            print(f"P0 Shed: {obs0.get('private', {}).get('shed')}")
            
        env.step([act0, act1])
        
if __name__ == "__main__":
    audit_step24()
