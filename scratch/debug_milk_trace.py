import sys
sys.path.insert(0, ".")
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2
import scratch.closed_loop_arch_v1 as cl_arch

env = kaggle_environments.make("kaggriculture", configuration={"seed": 201, "episodeSteps": 720})

agent_inst = cl_arch.ClosedLoopArchAgent()
env.reset()

milk_harvested = 0
milk_dropped = 0
milk_sold = 0

for step in range(719):
    obs0 = env.state[0].observation
    farm0 = obs0["farms"][0]
    priv0 = obs0["private"]
    
    act0 = agent_inst(obs0)
    act1 = v2.agent(env.state[1].observation)
    
    # Check milk in inventories
    m_inv = sum(inv.get("MILK", 0) for inv in priv0.get("inventories", []))
    m_shed = priv0.get("shed", {}).get("MILK", 0)
    
    if step % 24 in (0, 12):
        print(f"Step {step:3d} (D{step//24:2d} H{step%24:2d}): Money=${farm0['money']:6.1f} | Milk in Invs={m_inv} | Milk in Shed={m_shed} | Shed wheat={priv0['shed'].get('WHEAT')} | Market: {act0.get('market')[:2]}")
        
    env.step([act0, act1])

print(f"\nFinal Reward: Player 0 = ${env.steps[-1][0]['reward']:,.1f} | Player 1 (V2) = ${env.steps[-1][1]['reward']:,.1f}")
