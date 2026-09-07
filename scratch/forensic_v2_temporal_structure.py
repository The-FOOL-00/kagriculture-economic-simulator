import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2_mod
from collections import defaultdict, Counter
import numpy as np

BOARD = 10
SHED_ACCESS = frozenset([(4, 4), (5, 4), (4, 5), (5, 5)])

def get_quad(pos):
    x, y = pos
    if x < 5 and y < 5: return "NW"
    if x >= 5 and y < 5: return "NE"
    if x < 5 and y >= 5: return "SW"
    return "SE"

def analyze_v2_temporal(seed=42):
    # Track per worker:
    # positions, actions, current task, zone transitions, shed visits
    worker_history = defaultdict(list)
    
    def wrapped_v2(obs, config=None):
        step = int(obs.get("step", 0) or 0)
        day = step // 24
        hour = step % 24
        
        farm = obs["farms"][0]
        farmer = tuple(farm["farmer"])
        hands = [tuple(h) for h in farm.get("hands", []) or []]
        workers = [farmer] + hands
        
        act = v2_mod.agent(obs)
        f_act = act.get("farmer", ["PASS"])
        h_acts = act.get("hands", []) or []
        all_acts = [f_act] + [h_acts[i] if i < len(h_acts) else ["PASS"] for i in range(len(hands))]
        
        for w_i, (pos, a) in enumerate(zip(workers, all_acts)):
            op = a[0] if isinstance(a, list) and a else str(a)
            worker_history[w_i].append({
                "step": step, "day": day, "hour": hour, "pos": pos,
                "op": op, "zone": get_quad(pos), "in_shed": pos in SHED_ACCESS
            })
        return act

    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([wrapped_v2, "starter"])
    
    print(f"=== V2 Temporal Commitment Forensics (Seed {seed}) ===")
    
    total_zone_transitions = 0
    total_shed_returns = 0
    worker_zone_switches = {}
    worker_shed_visits = {}
    worker_task_chains = {}
    
    for w_i in sorted(worker_history.keys()):
        records = worker_history[w_i]
        n_turns = len(records)
        if n_turns == 0: continue
        
        # Zone transitions
        zone_changes = 0
        cur_zone = records[0]["zone"]
        for r in records[1:]:
            if r["zone"] != cur_zone:
                zone_changes += 1
                cur_zone = r["zone"]
        worker_zone_switches[w_i] = zone_changes
        total_zone_transitions += zone_changes
        
        # Shed returns (transitioning from not in shed to in shed)
        shed_returns = 0
        was_in_shed = records[0]["in_shed"]
        for r in records[1:]:
            if r["in_shed"] and not was_in_shed:
                shed_returns += 1
            was_in_shed = r["in_shed"]
        worker_shed_visits[w_i] = shed_returns
        total_shed_returns += shed_returns
        
        # Productive action clusters & contiguous chains
        chains = []
        cur_chain = 0
        for r in records:
            op = r["op"]
            if op not in ("NORTH", "SOUTH", "EAST", "WEST", "PASS", "NONE", ""):
                cur_chain += 1
            else:
                if cur_chain > 0:
                    chains.append(cur_chain)
                    cur_chain = 0
        if cur_chain > 0: chains.append(cur_chain)
        worker_task_chains[w_i] = chains
        
        avg_chain = np.mean(chains) if chains else 0.0
        max_chain = max(chains) if chains else 0
        
        # Dominant zones
        zone_counts = Counter(r["zone"] for r in records)
        top_zone = zone_counts.most_common(1)[0]
        zone_pct = top_zone[1] / n_turns * 100
        
        print(f"Worker {w_i:2d} ({n_turns:3d} turns): Dominant Zone={top_zone[0]} ({zone_pct:4.1f}%) | Zone Changes={zone_changes:2d} ({zone_changes/max(1, n_turns/24):4.1f}/day) | Shed Returns={shed_returns:2d} | Avg Prod Chain={avg_chain:4.2f} (Max={max_chain:2d})")
        
    print(f"\nAggregate V2 Statistics:")
    print(f"  Total Zone Transitions across season: {total_zone_transitions}")
    print(f"  Total Shed Returns across season:     {total_shed_returns}")
    print(f"  Avg Zone Transitions per Worker/Day: {total_zone_transitions / 30 / len(worker_history):.2f}")
    print(f"  Avg Shed Returns per Worker/Day:     {total_shed_returns / 30 / len(worker_history):.2f}")

if __name__ == "__main__":
    analyze_v2_temporal()
