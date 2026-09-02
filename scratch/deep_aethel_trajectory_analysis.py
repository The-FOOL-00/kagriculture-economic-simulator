import os
import json
import numpy as np

def run_deep_trajectory_analysis():
    aethel_dir = r'replays\Aethel_prime_v1'
    with open(r'scratch\aethel_full_forensics_reconciled.json', 'r', encoding='utf-8') as f:
        reconciled = json.load(f)

    # 1. Early-game determinism analysis
    # For every game, extract the exact action sequence of our farmer and hands for first 10, 25, 50, 100 turns
    # Compare pairwise action equality across games
    first_10_actions = []
    first_25_actions = []
    first_50_actions = []
    first_100_actions = []
    
    worker_efficiency_records = []
    economic_efficiency_records = []
    
    # Store turn-by-turn asset trajectories for all games
    all_trajectories = []
    
    for r in reconciled:
        rf = r['replay_file']
        rpath = os.path.join(aethel_dir, rf)
        with open(rpath, 'r', encoding='utf-8') as f:
            rep = json.load(f)
            
        our_seat = r['our_seat']
        steps = rep.get('steps', [])
        
        our_actions = []
        
        # Telemetry counters
        total_farmer_actions = 0
        total_hand_actions = 0
        farmer_idle_turns = 0
        farmer_walk_turns = 0
        farmer_productive_turns = 0
        hand_idle_turns = 0
        hand_walk_turns = 0
        hand_productive_turns = 0
        
        total_milk_produced = 0
        total_wool_produced = 0
        total_crops_harvested = 0
        total_market_sales_val = 0
        
        prev_money = 3000
        
        asset_curve = []
        
        for t_idx, step_data in enumerate(steps):
            if len(step_data) < 2:
                continue
            step_elem = step_data[our_seat]
            action = step_elem.get('action', {})
            obs = step_elem.get('observation', {})
            our_farm = obs.get('farms', [{}])[our_seat] if 'farms' in obs and len(obs['farms']) > our_seat else {}
            
            f_act = str(action.get('farmer', ['PASS']))
            h_acts = str(action.get('hands', []))
            m_acts = str(action.get('market', []))
            combined_act = f"{f_act}|{h_acts}|{m_acts}"
            our_actions.append(combined_act)
            
            # Action classification
            fa = action.get('farmer', ['PASS'])
            if len(fa) > 0:
                total_farmer_actions += 1
                cmd = fa[0] if isinstance(fa, list) else str(fa)
                if 'PASS' in cmd or 'WAIT' in cmd:
                    farmer_idle_turns += 1
                elif 'MOVE' in cmd:
                    farmer_walk_turns += 1
                else:
                    farmer_productive_turns += 1
                    
            hands = action.get('hands', [])
            for ha in hands:
                total_hand_actions += 1
                cmd = ha[0] if isinstance(ha, list) and len(ha) > 0 else str(ha)
                if 'PASS' in cmd or 'WAIT' in cmd:
                    hand_idle_turns += 1
                elif 'MOVE' in cmd:
                    hand_walk_turns += 1
                else:
                    hand_productive_turns += 1
                    
            # Count livestock & money
            curr_money = our_farm.get('money', 0)
            tiles = our_farm.get('tiles', [])
            cows, sheep, geese, crops = 0, 0, 0, 0
            for row in tiles:
                for c in row:
                    if isinstance(c, dict):
                        if 'COW' in str(c): cows += 1
                        elif 'SHEEP' in str(c): sheep += 1
                        elif 'GOOSE' in str(c) or 'GEESE' in str(c): geese += 1
                        elif c.get('crop') is not None or c.get('stage') is not None: crops += 1
            
            asset_curve.append({
                'turn': t_idx,
                'money': curr_money,
                'cows': cows,
                'sheep': sheep,
                'geese': geese,
                'crops': crops,
                'workers': len(our_farm.get('hands', [])) + 1,
                'quadrants': len(our_farm.get('unlocked_quadrants', []))
            })
            
        first_10_actions.append(our_actions[:10])
        first_25_actions.append(our_actions[:25])
        first_50_actions.append(our_actions[:50])
        first_100_actions.append(our_actions[:100])
        
        # Worker efficiency
        total_workers_avg = np.mean([a['workers'] for a in asset_curve])
        final_money = asset_curve[-1]['money'] if asset_curve else 0
        final_cows = asset_curve[-1]['cows'] if asset_curve else 0
        final_quads = asset_curve[-1]['quadrants'] if asset_curve else 1
        
        total_prod_turns = farmer_productive_turns + hand_productive_turns
        total_walk_turns = farmer_walk_turns + hand_walk_turns
        total_idle_turns = farmer_idle_turns + hand_idle_turns
        total_turns = max(1, total_prod_turns + total_walk_turns + total_idle_turns)
        
        worker_efficiency_records.append({
            'episode_id': r['episode_id'],
            'outcome': r['outcome'],
            'margin': r['margin'],
            'total_worker_turns': total_turns,
            'productive_pct': total_prod_turns / total_turns * 100,
            'walking_pct': total_walk_turns / total_turns * 100,
            'idle_pct': total_idle_turns / total_turns * 100,
            'productive_actions_per_worker_turn': total_prod_turns / max(1, len(steps)),
            'income_per_worker': r['our_score'] / max(1, total_workers_avg),
            'income_per_animal': r['our_score'] / max(1, final_cows) if final_cows > 0 else 0,
            'income_per_quadrant': r['our_score'] / max(1, final_quads),
            'income_per_productive_turn': r['our_score'] / max(1, total_prod_turns)
        })
        
        all_trajectories.append({
            'episode_id': r['episode_id'],
            'outcome': r['outcome'],
            'margin': r['margin'],
            'our_seat': our_seat,
            'opp_name': r['opp_name'],
            'asset_curve': asset_curve
        })

    # Determinism calculation
    def calc_similarity(act_list):
        n = len(act_list)
        if n < 2: return 1.0
        # Compare each game to the modal action sequence
        steps_len = len(act_list[0])
        match_counts = []
        for s in range(steps_len):
            step_acts = [act_list[i][s] for i in range(n) if s < len(act_list[i])]
            if not step_acts: continue
            # Find most common action
            from collections import Counter
            c = Counter(step_acts)
            mode_freq = c.most_common(1)[0][1]
            match_counts.append(mode_freq / len(step_acts))
        return float(np.mean(match_counts)) * 100

    sim_10 = calc_similarity(first_10_actions)
    sim_25 = calc_similarity(first_25_actions)
    sim_50 = calc_similarity(first_50_actions)
    sim_100 = calc_similarity(first_100_actions)

    print("\n--- AETHEL DETERMINISM & SCRIPTING ANALYSIS ---")
    print(f"Modal Sequence Alignment (First 10 turns):  {sim_10:.1f}%")
    print(f"Modal Sequence Alignment (First 25 turns):  {sim_25:.1f}%")
    print(f"Modal Sequence Alignment (First 50 turns):  {sim_50:.1f}%")
    print(f"Modal Sequence Alignment (First 100 turns): {sim_100:.1f}%")

    print("\n--- WORKER & SPATIAL EFFICIENCY ---")
    avg_prod = np.mean([w['productive_pct'] for w in worker_efficiency_records])
    avg_walk = np.mean([w['walking_pct'] for w in worker_efficiency_records])
    avg_idle = np.mean([w['idle_pct'] for w in worker_efficiency_records])
    print(f"Average Productive Time: {avg_prod:.1f}%")
    print(f"Average Walking Time:    {avg_walk:.1f}%")
    print(f"Average Idle Time:       {avg_idle:.1f}%")

    print("\n--- ECONOMIC EFFICIENCY METRICS ---")
    avg_inc_w = np.mean([w['income_per_worker'] for w in worker_efficiency_records])
    avg_inc_a = np.mean([w['income_per_animal'] for w in worker_efficiency_records if w['income_per_animal'] > 0])
    avg_inc_q = np.mean([w['income_per_quadrant'] for w in worker_efficiency_records])
    avg_inc_p = np.mean([w['income_per_productive_turn'] for w in worker_efficiency_records])
    print(f"Average Income / Worker:          {avg_inc_w:.1f}")
    print(f"Average Income / Animal:          {avg_inc_a:.1f}")
    print(f"Average Income / Land Quadrant:   {avg_inc_q:.1f}")
    print(f"Average Income / Productive Turn: {avg_inc_p:.1f}")

    # Save results
    results = {
        'determinism': {
            'first_10_similarity_pct': sim_10,
            'first_25_similarity_pct': sim_25,
            'first_50_similarity_pct': sim_50,
            'first_100_similarity_pct': sim_100
        },
        'worker_efficiency': {
            'productive_pct': avg_prod,
            'walking_pct': avg_walk,
            'idle_pct': avg_idle
        },
        'economic_efficiency': {
            'income_per_worker': avg_inc_w,
            'income_per_animal': avg_inc_a,
            'income_per_quadrant': avg_inc_q,
            'income_per_productive_turn': avg_inc_p
        },
        'worker_records': worker_efficiency_records,
        'trajectories': all_trajectories
    }
    
    with open(r'scratch\aethel_deep_trajectory_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print("\nSaved deep trajectory results to scratch\aethel_deep_trajectory_results.json")

if __name__ == '__main__':
    run_deep_trajectory_analysis()
