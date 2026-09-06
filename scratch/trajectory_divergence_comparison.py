import json
import sys
sys.path.insert(0, '.')
from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2
import opponents.replay_whyme_labs as whyme

sys.stdout.reconfigure(encoding='utf-8')

# 1. Load Crop Dusta ground truth from Episode 104824599
replay_path = 'scratch/replays/Whyme_Labs_104824599.json'
with open(replay_path, 'r', encoding='utf-8') as f:
    rep_data = json.load(f)

seed = rep_data['info']['seed'] # 215620170
print(f"Running Baseline V2 on Seed {seed} vs Replay_Whyme_Labs (Player 0 Whyme, Player 1 Us)...")

# 2. Run Baseline V2 on the exact same seed in Player 1 slot
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
env.run([whyme.agent, v2.agent])

v2_steps = env.steps
cd_steps = rep_data['steps']

print(f"Crop Dusta Replay Final Reward: ${cd_steps[-1][1]['reward']:,.1f}")
print(f"Baseline V2 Final Reward:      ${v2_steps[-1][1]['reward']:,.1f}\n")

# 3. Step-by-step comparison to find FIRST STRUCTURAL DIVERGENCE
# Compare cash, cows, sheep, workers, pastures, quadrants, crops, market actions

diff_table = []
first_diff_found = False

for s in range(720):
    cd_obs = cd_steps[s][1]['observation']
    cd_farm = cd_obs['farms'][1]
    cd_act = cd_steps[s][1].get('action', {})
    cd_m_act = cd_act.get('market', []) if isinstance(cd_act, dict) else []
    
    v2_obs = v2_steps[s][1]['observation']
    v2_farm = v2_obs['farms'][1]
    v2_act = v2_steps[s][1].get('action', {})
    v2_m_act = v2_act.get('market', []) if isinstance(v2_act, dict) else []
    
    cd_money = float(cd_farm.get('money', 0))
    v2_money = float(v2_farm.get('money', 0))
    
    cd_quads = len(cd_farm.get('unlocked_quadrants', []))
    v2_quads = len(v2_farm.get('unlocked_quadrants', []))
    
    cd_cows = sum(1 for row in cd_farm.get('tiles', []) for t in row if isinstance(t, dict) and t.get('animal') == 'COW')
    v2_cows = sum(1 for row in v2_farm.get('tiles', []) for t in row if isinstance(t, dict) and t.get('animal') == 'COW')
    
    cd_sheep = sum(1 for row in cd_farm.get('tiles', []) for t in row if isinstance(t, dict) and t.get('animal') == 'SHEEP')
    v2_sheep = sum(1 for row in v2_farm.get('tiles', []) for t in row if isinstance(t, dict) and t.get('animal') == 'SHEEP')
    
    cd_past = sum(1 for row in cd_farm.get('tiles', []) for t in row if isinstance(t, dict) and t.get('kind') == 'PASTURE')
    v2_past = sum(1 for row in v2_farm.get('tiles', []) for t in row if isinstance(t, dict) and t.get('kind') == 'PASTURE')
    
    cd_workers = len(cd_farm.get('hands', [])) + (1 if cd_farm.get('farmer') else 0)
    v2_workers = len(v2_farm.get('hands', [])) + (1 if v2_farm.get('farmer') else 0)
    
    # Check for divergence
    diffs = []
    if cd_quads != v2_quads:
        diffs.append(f"Q: CD=Q{cd_quads} vs V2=Q{v2_quads}")
    if cd_cows != v2_cows:
        diffs.append(f"Cows: CD={cd_cows} vs V2={v2_cows}")
    if cd_sheep != v2_sheep:
        diffs.append(f"Sheep: CD={cd_sheep} vs V2={v2_sheep}")
    if cd_past != v2_past:
        diffs.append(f"Pastures: CD={cd_past} vs V2={v2_past}")
    if cd_workers != v2_workers:
        diffs.append(f"Workers: CD={cd_workers} vs V2={v2_workers}")
    if abs(cd_money - v2_money) > 50:
        diffs.append(f"Cash: CD=${cd_money:.0f} vs V2=${v2_money:.0f}")
    if str(cd_m_act) != str(v2_m_act):
        diffs.append(f"MarketAct diff")
        
    if diffs and not first_diff_found:
        first_diff_found = True
        print(f"*** FIRST DIVERGENCE AT STEP {s} (D{s//24:02d}:H{s%24:02d}) ***")
        print(f"  Crop Dusta State: Cash=${cd_money:.1f}, Q={cd_quads}, Cows={cd_cows}, Sheep={cd_sheep}, Past={cd_past}, W={cd_workers}, Market={cd_m_act}")
        print(f"  Baseline V2 State: Cash=${v2_money:.1f}, Q={v2_quads}, Cows={v2_cows}, Sheep={v2_sheep}, Past={v2_past}, W={v2_workers}, Market={v2_m_act}")
        print(f"  Diffs: {', '.join(diffs)}\n")

    # Record at key milestones
    if s in [0, 24, 72, 120, 121, 122, 144, 168, 192, 198, 200, 201, 216, 240, 255, 264, 266, 360, 480, 600, 712, 719]:
        diff_table.append({
            'step': s,
            'day': s // 24,
            'hour': s % 24,
            'cd_money': cd_money,
            'v2_money': v2_money,
            'cd_quads': cd_quads,
            'v2_quads': v2_quads,
            'cd_cows': cd_cows,
            'v2_cows': v2_cows,
            'cd_sheep': cd_sheep,
            'v2_sheep': v2_sheep,
            'cd_past': cd_past,
            'v2_past': v2_past,
            'cd_workers': cd_workers,
            'v2_workers': v2_workers,
            'cd_m_act': cd_m_act,
            'v2_m_act': v2_m_act,
        })

print("=" * 140)
print(f"{'Step':>4} | {'Day:Hr':>6} | {'Crop Dusta (CD)':<45} | {'Baseline V2':<45} | {'Key Structural Divergence & Consequence'}")
print("-" * 140)

for d in diff_table:
    cd_summary = f"${d['cd_money']:7.0f} | Q{d['cd_quads']} | {d['cd_cows']}C/{d['cd_sheep']}S | P:{d['cd_past']:2d} | W:{d['cd_workers']:2d}"
    v2_summary = f"${d['v2_money']:7.0f} | Q{d['v2_quads']} | {d['v2_cows']}C/{d['v2_sheep']}S | P:{d['v2_past']:2d} | W:{d['v2_workers']:2d}"
    
    note = ""
    if d['step'] == 0:
        note = "CD & V2 both buy 3 Cows, 1 Sheep on Day 0"
    elif d['step'] == 72:
        note = "CD has 5 Pastures built; V2 has 4 Pastures"
    elif d['step'] == 121:
        note = "CD buys Q2 at Step 122; V2 delays Q2 to Step 168"
    elif d['step'] == 122:
        note = "CD unlocks Q2 on Day 5 (46 steps earlier than V2)"
    elif d['step'] == 168:
        note = "V2 finally unlocks Q2; CD already has 10 Pastures and expanding"
    elif d['step'] == 198:
        note = "CD liquidates 18 Milk across Steps 198-200; V2 buys 3 Sheep"
    elif d['step'] == 200:
        note = "CD unlocks Q3 on Day 8 (55 steps earlier than V2)"
    elif d['step'] == 201:
        note = "CD buys 2 extra Cows on Q3; V2 still on Q2 with 5 Cows/6 Sheep"
    elif d['step'] == 255:
        note = "V2 unlocks Q3; CD already has 10 Cows, 14 Pastures, importing wheat"
    elif d['step'] == 264:
        note = "V2 reaches 8 Cows; CD reaches 11 Cows and scaling to 13"
    elif d['step'] == 360:
        note = "Midgame: CD has 13 Cows + 16 Pastures; V2 has 8 Cows + 6 Sheep"
    elif d['step'] == 719:
        note = f"Final: CD=${d['cd_money']:,.0f} vs V2=${d['v2_money']:,.0f}"
        
    print(f"{d['step']:4d} | D{d['day']:02d}:H{d['hour']:02d} | {cd_summary:<45} | {v2_summary:<45} | {note}")

print("=" * 140)
