# Challenger C3: Carrot-Pipelined Compounding
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
    
    work = tempfile.mkdtemp(prefix="v3_c3_")
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
    # Days 2 to 12: replace Strawberry seed orders with Carrot seed orders
    if 48 <= step <= 312:
        market = list(action.get('market', []))
        mod_market = False
        for i, order in enumerate(market):
            if len(order) >= 3 and order[0] == 'BUY_SEED' and order[1] == 'STRAWBERRY':
                market[i] = ['BUY_SEED', 'CARROT', order[2]]
                mod_market = True
        if mod_market:
            action['market'] = market
            
        # Also replace planting actions if carrying CARROT seeds
        private = observation.get('private', {})
        carrot_seeds = private.get('seeds', {}).get('CARROT', 0)
        if carrot_seeds > 0:
            farmer_act = action.get('farmer')
            if farmer_act and len(farmer_act) >= 2 and farmer_act[0] == 'PLANT' and farmer_act[1] == 'STRAWBERRY':
                action['farmer'] = ['PLANT', 'CARROT']
            hands_acts = list(action.get('hands', []))
            for i, h in enumerate(hands_acts):
                if h and len(h) >= 2 and h[0] == 'PLANT' and h[1] == 'STRAWBERRY':
                    hands_acts[i] = ['PLANT', 'CARROT']
            action['hands'] = hands_acts
            
    return action
