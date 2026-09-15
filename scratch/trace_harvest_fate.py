import kaggle_environments
from candidates.candidate_cl_coordinated_v1 import agent as cl_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

for name, ag in [('V2', v2_agent), ('CL', cl_agent)]:
    env = kaggle_environments.make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 42})
    env.run([ag, 'starter'])
    
    sb_harvested = 0
    milk_harvested = 0
    wool_harvested = 0
    fert_collected = 0
    
    for s_idx in range(1, len(env.steps)):
        prev_farm = env.steps[s_idx-1][0]['observation']['farms'][0]
        prev_tiles = prev_farm['tiles']
        act = env.steps[s_idx][0].get('action', {})
        
        farmer_act = act.get('farmer', [])
        hands_act = act.get('hands', [])
        for w_idx, w_act in enumerate([farmer_act] + hands_act):
            cmd = w_act[0] if w_act else ''
            if cmd == 'HARVEST':
                pos = prev_farm['farmer'] if w_idx == 0 else prev_farm['hands'][w_idx-1]
                pt = prev_tiles[pos[1]][pos[0]]
                if isinstance(pt, dict):
                    if pt.get('crop') == 'STRAWBERRY':
                        sb_harvested += int(pt.get('yield_units', 0))
                    elif pt.get('animal') == 'COW':
                        milk_harvested += int(pt.get('yield_units', 0))
                    elif pt.get('animal') == 'SHEEP':
                        wool_harvested += int(pt.get('yield_units', 0))
            elif cmd == 'COLLECT_FERTILIZER':
                fert_collected += 1
                
    final_shed = dict(env.steps[-1][0]['observation']['private']['shed'])
    final_invs = env.steps[-1][0]['observation']['private']['inventories']
    unsold_inv = {}
    for inv in final_invs:
        for k, v in inv.items():
            unsold_inv[k] = unsold_inv.get(k, 0) + v
            
    print(f'=== {name} ===')
    print(f'Strawberry Harvested: {sb_harvested} | Final Shed: {final_shed.get("STRAWBERRY", 0)} | Inv: {unsold_inv.get("STRAWBERRY", 0)}')
    print(f'Milk Harvested: {milk_harvested} | Final Shed: {final_shed.get("MILK", 0)} | Inv: {unsold_inv.get("MILK", 0)}')
    print(f'Wool Harvested: {wool_harvested} | Final Shed: {final_shed.get("WOOL", 0)} | Inv: {unsold_inv.get("WOOL", 0)}')
    print(f'Fert Collected: {fert_collected} | Final Shed: {final_shed.get("FERTILIZER", 0)} | Inv: {unsold_inv.get("FERTILIZER", 0)}')
    print(f'Total final unsold inventory in hands: {unsold_inv}')
    print(f'Final Shed: {final_shed}')
