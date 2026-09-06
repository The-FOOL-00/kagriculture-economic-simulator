import sys
sys.path.insert(0, ".")
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2
import scratch.closed_loop_arch_v1 as cl_arch

env = kaggle_environments.make("kaggriculture", configuration={"seed": 215620170, "episodeSteps": 720})

agent_inst = cl_arch.ClosedLoopArchAgent()
env.reset()

for step in range(72):
    obs0 = env.state[0].observation
    farm0 = obs0["farms"][0]
    priv0 = obs0["private"]
    
    act0 = agent_inst(obs0)
    act1 = v2.agent(env.state[1].observation)
    
    day = step // 24
    hour = step % 24
    
    # Check animals on farm
    animals = []
    for y in range(5):
        for x in range(5):
            t = farm0["tiles"][y][x]
            if isinstance(t, dict) and "animal" in t:
                animals.append(((x, y), t["animal"], f"fed={t['fed_today']}", f"cared={t['cared_today']}", f"unfed_days={t.get('consecutive_unfed', 0)}"))
                
    if hour in (0, 1, 5, 10, 20, 23):
        print(f"Step {step:2d} (D{day} H{hour:2d}): Animals={animals} | Shed wheat={priv0['shed'].get('WHEAT')} | Invs={[inv.get('WHEAT', 0) for inv in priv0['inventories']]}")
        print(f"  Farmer: {act0['farmer']} | Hands: {act0['hands'][:3]}")
        
    env.step([act0, act1])
