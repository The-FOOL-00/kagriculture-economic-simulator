import sys, os
sys.path.insert(0, os.path.abspath('.'))

from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent
import kaggle_environments

cfg = {'episodeSteps': 720, 'seed': 1060}

agent = ParameterizedQuotaAgent(50)

# Track sheep on days 20, 21, 22, 23
class EscapeAuditor(ParameterizedQuotaAgent):
    def __init__(self):
        super().__init__(50)
        self.logs = []

    def __call__(self, obs, config=None):
        step = int(obs.get('step', 0) or 0)
        day = step // 24
        hr = step % 24
        if 20 <= day <= 23:
            p = int(obs.get('player', 0) or 0)
            farm = obs.get('farms')[p]
            tiles = farm.get('tiles')
            priv = obs.get('private')
            shed = priv.get('shed') or {}
            
            sheep = {}
            for y in range(10):
                for x in range(10):
                    t = tiles[y][x]
                    if isinstance(t, dict) and t.get('animal') == 'SHEEP':
                        sheep[(x, y)] = {
                            'fed': t.get('fed_today'),
                            'care': t.get('cared_today'),
                            'unfed_count': t.get('consecutive_unfed'),
                            'yield': t.get('yield_units'),
                            'bonus': t.get('pending_care_bonus', 0)
                        }
            
            act = super().__call__(obs, config)
            w_acts = [act.get('farmer', ['PASS'])] + act.get('hands', [])
            w_pos = [tuple(farm.get('farmer', [4, 4]))] + [tuple(h) for h in farm.get('hands', [])]
            
            self.logs.append({
                'day': day, 'hour': hr, 'step': step,
                'sheep': sheep, 'w_acts': w_acts, 'w_pos': w_pos,
                'shed_wheat': shed.get('WHEAT', 0)
            })
            return act
        return super().__call__(obs, config)

auditor = EscapeAuditor()
env = kaggle_environments.make('kaggriculture', configuration=cfg)
env.run([auditor, 'starter'])

print('=== ESCAPE AUDIT (DAYS 20-23) ===')
for d in [20, 21, 22, 23]:
    end = [x for x in auditor.logs if x['day'] == d and x['hour'] == 23][0]
    sw = end['shed_wheat']
    print(f'\nEnd of Day {d}: Shed wheat={sw}')
    for pos, s in end['sheep'].items():
        print(f"  Sheep at {pos}: fed={s['fed']}, care={s['care']}, consecutive_unfed={s['unfed_count']}, yield={s['yield']}, bonus={s['bonus']}")

bad_sheep = None
for d in [21, 22]:
    end = [x for x in auditor.logs if x['day'] == d and x['hour'] == 23][0]
    for pos, s in end['sheep'].items():
        if not s['fed']:
            print(f'\nDay {d}: Unfed sheep was at {pos}!')
            bad_sheep = pos

if bad_sheep:
    print(f'\n--- HOURLY TRACE FOR BAD SHEEP AT {bad_sheep} ON DAY 22 ---')
    for hr in range(24):
        entry = [x for x in auditor.logs if x['day'] == 22 and x['hour'] == hr][0]
        sw = entry['shed_wheat']
        w_near = [(w, entry['w_pos'][w], entry['w_acts'][w]) for w in range(len(entry['w_pos'])) if abs(entry['w_pos'][w][0]-bad_sheep[0]) + abs(entry['w_pos'][w][1]-bad_sheep[1]) <= 3]
        w_on = [(w, entry['w_acts'][w]) for w in range(len(entry['w_pos'])) if entry['w_pos'][w] == bad_sheep]
        print(f"Hr {hr:2d}: Shed wheat={sw}, Workers on {bad_sheep}: {w_on}, Workers near: {w_near}")
