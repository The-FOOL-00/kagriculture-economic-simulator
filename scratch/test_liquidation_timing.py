import sys
import numpy as np
from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2
import opponents.live_flooder_v1 as lf

sys.stdout.reconfigure(encoding='utf-8')

# Run 10 games of baseline V2 vs LiveFlooder and inspect shed inventory and cash at Steps 168, 180, 192, 200, 204, 216, 240, 255
print("Inspecting Baseline V2 shed inventory and cash trajectory across turns 168-255...")

checkpoints = [168, 180, 192, 198, 200, 204, 216, 228, 240, 255]

for seed in [42, 100, 200, 300, 500]:
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    # Collect state at each step
    # We can use a wrapper agent that logs
    state_logs = []
    
    def logging_agent(obs):
        step = obs.get("step", 0)
        if step in checkpoints:
            farm = obs["farms"][obs["player"]]
            private = obs.get("private", {})
            shed = private.get("shed", {})
            prices = obs.get("market", {}).get("prices", {})
            
            # Compute liquidation value
            liq_val = (
                shed.get("MILK", 0) * prices.get("MILK", 160) +
                shed.get("WOOL", 0) * prices.get("WOOL", 200) +
                shed.get("FERTILIZER", 0) * prices.get("FERTILIZER", 100) +
                shed.get("STRAWBERRY", 0) * prices.get("STRAWBERRY", 120) +
                shed.get("MELON", 0) * prices.get("MELON", 250)
            )
            state_logs.append({
                "step": step,
                "day": step // 24,
                "hour": step % 24,
                "cash": farm["money"],
                "quads": len(farm["unlocked_quadrants"]),
                "shed_milk": shed.get("MILK", 0),
                "shed_wool": shed.get("WOOL", 0),
                "shed_fert": shed.get("FERTILIZER", 0),
                "shed_wheat": shed.get("WHEAT", 0),
                "liq_val": liq_val,
                "total_potential": farm["money"] + liq_val,
            })
        return v2.agent(obs)
    
    env.run([logging_agent, lf.agent])
    print(f"\n--- SEED {seed} ---")
    for log in state_logs:
        print(f"Step {log['step']:3d} (D{log['day']:02d} H{log['hour']:02d}) | Cash: ${log['cash']:6.1f} | Shed: M{log['shed_milk']:2d} Wl{log['shed_wool']:2d} Ft{log['shed_fert']:2d} Wh{log['shed_wheat']:2d} | LiqVal: ${log['liq_val']:6.1f} | TotalPot: ${log['total_potential']:6.1f} | Q: {log['quads']}")
