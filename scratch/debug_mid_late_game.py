import sys
sys.path.insert(0, ".")
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2
import scratch.closed_loop_arch_v1 as cl_arch

env = kaggle_environments.make("kaggriculture", configuration={"seed": 206, "episodeSteps": 720})

agent_inst = cl_arch.ClosedLoopArchAgent()
env.reset()

for step in range(720):
    obs0 = env.state[0].observation
    farm0 = obs0["farms"][0]
    priv0 = obs0["private"]
    
    act0 = agent_inst(obs0)
    act1 = v2.agent(env.state[1].observation)
    
    day = step // 24
    hour = step % 24
    
    if hour == 0 and day in (0, 1, 2, 5, 8, 10, 15, 20, 25, 28, 29):
        # Count plants and animals
        plants = {}
        for row in farm0["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    crop = t.get("crop")
                    plants[crop] = plants.get(crop, 0) + 1
        
        cows = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "COW")
        sheep = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
        
        print(f"Day {day:2d} (Step {step:3d}): Money=${farm0['money']:8.1f} | Hands={len(farm0['hands'])} | Cows={cows} | Sheep={sheep}")
        print(f"  Plants on farm: {plants}")
        print(f"  Shed: {priv0['shed']}")
        print(f"  Seeds: {priv0['seeds']}")
        print(f"  Market Action: {act0.get('market')[:4]}")
        
    env.step([act0, act1])

print(f"\nFinal Reward: Player 0 = ${env.steps[-1][0]['reward']:,.1f} | Player 1 (V2) = ${env.steps[-1][1]['reward']:,.1f}")
