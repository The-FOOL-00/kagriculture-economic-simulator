# Challenger C2: Clustered Livestock & Cow Scaling
import os
import sys
import tarfile
import tempfile

_V3_AGENT = None

def _get_v3():
    global _V3_AGENT
    if _V3_AGENT is not None:
        return _V3_AGENT
    search_dirs = [os.getcwd(), os.path.dirname(os.path.abspath(__file__)), os.path.dirname(os.getcwd())]
    tarball = None
    for d in search_dirs:
        p = os.path.join(d, "submission_Vj_kc_v3.tar.gz")
        if os.path.exists(p):
            tarball = p
            break
    if not tarball:
        tarball = r"C:\Users\Sundareswaran\Kagriculture-v24\submission_Vj_kc_v3.tar.gz"
    
    work = tempfile.mkdtemp(prefix="v3_c2_")
    with tarfile.open(tarball, "r:gz") as tar:
        tar.extractall(work)
    sys.path.insert(0, work)
    import main as v3_module
    _V3_AGENT = v3_module.agent
    return _V3_AGENT

def agent(observation, configuration=None):
    v3 = _get_v3()
    action = v3(observation, configuration)
    if not isinstance(action, dict):
        return action
    
    step = int(observation.get('step', 0) or 0)
    # Days 0-3: expand cow purchase targets
    if step <= 96:
        player = observation.get('player', 0)
        farms = observation.get('farms', [])
        if player < len(farms):
            my_farm = farms[player]
            money = my_farm.get('money', 0)
            tiles = my_farm.get('tiles', [])
            owned_cows = sum(1 for row in tiles for tile in row if isinstance(tile, dict) and tile.get('animal') == 'COW')
            
            market = list(action.get('market', []))
            has_buy_cow = any(len(o) > 1 and o[0] == 'BUY_ANIMAL' and o[1] == 'COW' for o in market)
            
            if money >= 250 and owned_cows < 10 and not has_buy_cow:
                market.append(['BUY_ANIMAL', 'COW', 1])
                action['market'] = market
                
    return action
