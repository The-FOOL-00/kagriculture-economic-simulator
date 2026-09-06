import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

replay_path = 'scratch/replays/Whyme_Labs_104824599.json'
with open(replay_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

steps = data['steps']
p_idx = 1 # Crop Dusta

# Map size and quadrants:
# 20x20 total or 24x24? Let's check farm grid dimensions
f0 = steps[0][p_idx]['observation']['farms'][p_idx]
tiles = f0['tiles']
H = len(tiles)
W = len(tiles[0])
print(f"Farm Dimensions: {H}x{W}")

# Quadrant boundaries:
# NW: rows 0..H/2-1, cols 0..W/2-1
# NE: rows 0..H/2-1, cols W/2..W-1
# SW: rows H/2..H-1, cols 0..W/2-1
# SE: rows H/2..H-1, cols W/2..W-1

# Analyze spatial usage at intervals:
check_steps = [24, 72, 120, 150, 200, 250, 300, 400, 500, 600, 719]

for s in check_steps:
    f_obs = steps[s][p_idx]['observation']['farms'][p_idx]
    grid = f_obs['tiles']
    
    quad_stats = {'NW': {'pasture': 0, 'crop': {}, 'soil': 0, 'grass': 0},
                  'NE': {'pasture': 0, 'crop': {}, 'soil': 0, 'grass': 0},
                  'SW': {'pasture': 0, 'crop': {}, 'soil': 0, 'grass': 0},
                  'SE': {'pasture': 0, 'crop': {}, 'soil': 0, 'grass': 0}}
                  
    mid_r = H // 2
    mid_c = W // 2
    
    for r in range(H):
        for c in range(W):
            q_name = ('N' if r < mid_r else 'S') + ('W' if c < mid_c else 'E')
            t = grid[r][c]
            if isinstance(t, dict):
                k = t.get('kind')
                if k == 'PASTURE':
                    quad_stats[q_name]['pasture'] += 1
                elif k == 'PLANT':
                    cr = t.get('crop', 'UNKNOWN')
                    quad_stats[q_name]['crop'][cr] = quad_stats[q_name]['crop'].get(cr, 0) + 1
            elif t == 'SOIL':
                quad_stats[q_name]['soil'] += 1
            elif t == 'GRASS':
                quad_stats[q_name]['grass'] += 1
                
    print(f"\n--- STEP {s} (Day {s//24}, Hour {s%24}) SPATIAL BREAKDOWN ---")
    for q_name in ['NW', 'NE', 'SW', 'SE']:
        st = quad_stats[q_name]
        crops_str = ", ".join([f"{k}:{v}" for k, v in st['crop'].items()]) if st['crop'] else "none"
        print(f"  Quad {q_name}: Pastures={st['pasture']:2d} | Soils={st['soil']:2d} | Crops=[{crops_str}] | Grass={st['grass']:2d}")

