import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

# Run V2 standalone vs pass to see its strawberry timeline
env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
env.run([v2_agent, lambda obs, cfg: {}])

# Track strawberry tiles over time
for step_idx in [119, 167, 215, 239, 287, 335, 383, 431, 479, 527, 575, 623, 671, 719]:
    obs = env.steps[step_idx][0]['observation']
    farm = obs['farms'][0]
    day = obs['day']
    hour = obs['hour']
    
    # Count strawberry tiles: planted, ripe, yield
    str_count = 0
    str_ripe = 0
    str_total_yield = 0
    for r in farm['tiles']:
        for t in r:
            if isinstance(t, dict) and t.get('crop') == 'STRAWBERRY':
                str_count += 1
                if int(t.get('yield_units', 0) or 0) > 0:
                    str_ripe += 1
                    str_total_yield += int(t.get('yield_units', 0))
    
    shed_str = obs['private']['shed'].get('STRAWBERRY', 0)
    money = farm['money']
    quads = farm['unlocked_quadrants']
    print(f"Step {step_idx:3d} (D{day:2d} H{hour:2d}): Money=${money:,.0f} | Quads={quads} | StrawTiles={str_count:2d} (Ripe={str_ripe:2d}, YieldInField={str_total_yield:2d}) | StrawInShed={shed_str:2d}")
