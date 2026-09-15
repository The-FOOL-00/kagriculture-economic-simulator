import sys, os, json
sys.path.insert(0, 'external_repos/kaggriculture-cppsim')
sys.path.insert(0, 'candidates/closed_loop_architecture')
sys.path.insert(0, 'extracted_agents/dmitrii_lb2800')
import kagsim
from closed_loop_v2 import ClosedLoopAgentV2
import importlib.util

spec = importlib.util.spec_from_file_location('dmitrii_agent', 'extracted_agents/dmitrii_lb2800/main.py')
dmitrii_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dmitrii_mod)

g = kagsim.Game(50081)
p_v2 = ClosedLoopAgentV2()
p_dmi = dmitrii_mod.agent

first_cash_div = None
first_tile_div = None
first_act_div = None

timeline = []

while not g.done:
    obs_v2 = g.observe(0)
    obs_dmi = g.observe(1)
    step = int(obs_v2['step'])
    
    act_v2 = p_v2.act(obs_v2)
    act_dmi = p_dmi(obs_dmi)
    
    cash_v2 = obs_v2['farms'][0]['money']
    cash_dmi = obs_dmi['farms'][1]['money']
    
    if first_cash_div is None and abs(cash_v2 - cash_dmi) > 1e-4:
        first_cash_div = (step, cash_v2, cash_dmi)
        
    tiles_v2 = obs_v2['farms'][0]['tiles']
    tiles_dmi = obs_dmi['farms'][1]['tiles']
    tile_diffs = 0
    diff_coords = []
    for r in range(10):
        for c in range(10):
            t0 = tiles_v2[r][c]
            t1 = tiles_dmi[r][c]
            if t0 != t1:
                tile_diffs += 1
                diff_coords.append((r, c, str(t0), str(t1)))
                
    if first_tile_div is None and tile_diffs > 0:
        first_tile_div = (step, tile_diffs, diff_coords)

    if first_act_div is None and (act_v2 != act_dmi):
        first_act_div = (step, act_v2, act_dmi)

    # Detailed checkpoints
    if step in [163, 164, 165, 216, 217, 218, 258, 259, 260, 695, 696, 697, 712, 713, 714, 715, 716, 717, 718]:
        timeline.append({
            'step': step,
            'cash_v2': cash_v2,
            'cash_dmi': cash_dmi,
            'act_v2_market': act_v2.get('market', []),
            'act_dmi_market': act_dmi.get('market', []),
            'act_v2_farmer': act_v2.get('farmer'),
            'act_dmi_farmer': act_dmi.get('farmer'),
            'act_v2_hands': act_v2.get('hands', []),
            'act_dmi_hands': act_dmi.get('hands', []),
            'tile_diffs': tile_diffs,
            'sample_diff_coords': diff_coords[:3] if diff_coords else [],
            'shed_v2': obs_v2['private']['shed'],
            'shed_dmi': obs_dmi['private']['shed']
        })

    g.step(act_v2, act_dmi)

final_v2 = g.observe(0)['farms'][0]['money']
final_dmi = g.observe(1)['farms'][1]['money']

print(f"Final Reward: V2={final_v2}, Dmi={final_dmi}, Delta={final_v2 - final_dmi}")
print(f"First Cash Divergence: {first_cash_div}")
print(f"First Tile Divergence: {first_tile_div}")
print(f"First Action Divergence step: {first_act_div[0] if first_act_div else None}")

with open('scratch/audit2_1_seed50081_timeline.json', 'w') as f:
    json.dump({'first_cash_div': first_cash_div, 'first_tile_div': first_tile_div, 'timeline': timeline}, f, indent=2, default=str)
print("Timeline written successfully.")
