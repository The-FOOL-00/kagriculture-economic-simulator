import sys
import os
sys.path.insert(0, os.path.abspath("."))
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2

def test_crop_and_livestock_schedule(seed=1000):
    env = kaggle_environments.make('kaggriculture', configuration={'seed': seed, 'episodeSteps': 720}, debug=False)
    env.reset()
    
    TURNS_PER_DAY = 24
    
    unwatered_by_day = {}
    unfed_by_day = {}
    
    for step in range(719):
        obs0 = env.state[0].observation
        act0 = v2.agent(obs0)
        env.step([act0, 'random'])
        
        farm = env.state[0].observation['farms'][0]
        tiles = farm.get('tiles', [])
        day = step // TURNS_PER_DAY
        hour = step % TURNS_PER_DAY
        
        if hour == 23:
            unw = []
            unf = []
            for r_idx, row in enumerate(tiles):
                for c_idx, t in enumerate(row):
                    if isinstance(t, dict):
                        if t.get('kind') == 'PLANT' and not t.get('watered_today'):
                            unw.append((c_idx, r_idx, t.get('crop'), t.get('yield_units', 0)))
                        elif t.get('kind') == 'PASTURE' and not t.get('fed_today'):
                            unf.append((c_idx, r_idx, t.get('animal'), t.get('yield_units', 0)))
            if unw:
                unwatered_by_day[day] = unw
            if unf:
                unfed_by_day[day] = unf
                
    print("Days with unwatered plants at hour 23:")
    for d, items in sorted(unwatered_by_day.items()):
        print(f"Day {d}: {len(items)} unwatered crops -> {items[:3]}...")
        
    print("\nDays with unfed animals at hour 23:")
    for d, items in sorted(unfed_by_day.items()):
        print(f"Day {d}: {len(items)} unfed animals -> {items[:3]}...")

if __name__ == '__main__':
    test_crop_and_livestock_schedule()
