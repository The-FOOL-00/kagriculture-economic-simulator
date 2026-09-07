import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_cl_aethel_prime import agent as prime_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

pass_ag = lambda obs, cfg=None: {}

def run_telemetry(ag, name):
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
    env.run([ag, pass_ag])
    
    # Track metrics
    sales = {}
    total_actions = 0
    idle_passes = 0
    move_actions = 0
    chore_actions = 0
    action_counts = {}
    
    for step_idx in range(720):
        act = env.steps[step_idx][0].get('action', {})
        # Count market sales
        m_orders = act.get('market', []) or act.get('market_orders', [])
        for o in m_orders:
            if o[0] == 'SELL' and len(o) >= 3:
                sales[o[1]] = sales.get(o[1], 0) + o[2]
                
        # Count worker actions
        all_acts = []
        if act.get('farmer'): all_acts.append(act['farmer'])
        for h in act.get('hands', []): all_acts.append(h)
        
        for a in all_acts:
            cmd = a[0] if isinstance(a, list) and a else str(a)
            action_counts[cmd] = action_counts.get(cmd, 0) + 1
            total_actions += 1
            if cmd == 'PASS': idle_passes += 1
            elif cmd in ('NORTH', 'SOUTH', 'EAST', 'WEST'): move_actions += 1
            else: chore_actions += 1
            
    final_reward = env.state[0].reward
    print(f"=== {name} Telemetry (Seed 42) ===")
    print(f"Final Reward: ${final_reward:,.1f}")
    print(f"Total Worker Actions: {total_actions} (Chores: {chore_actions}, Moves: {move_actions}, Idle: {idle_passes})")
    print(f"Chore Density: {chore_actions / total_actions * 100:.1f}% | Idle Rate: {idle_passes / total_actions * 100:.1f}%")
    print("Action Breakdown:", action_counts)
    print("Total Sales:", sales)
    print()

run_telemetry(v2_agent, "V2 (Frozen Benchmark)")
run_telemetry(prime_agent, "Prime (CL Candidate)")
