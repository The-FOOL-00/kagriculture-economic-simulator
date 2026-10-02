# Challenger C1: Labor Dispatch & Idle-Zeroing
import os
import sys
import tarfile
import tempfile

_V3_AGENT = None

def _get_v3():
    global _V3_AGENT
    if _V3_AGENT is not None:
        return _V3_AGENT
    # Look for submission_Vj_kc_v3.tar.gz in current dir or parent dirs
    search_dirs = [os.getcwd(), os.path.dirname(os.path.abspath(__file__)), os.path.dirname(os.getcwd())]
    tarball = None
    for d in search_dirs:
        p = os.path.join(d, "submission_Vj_kc_v3.tar.gz")
        if os.path.exists(p):
            tarball = p
            break
    if not tarball:
        tarball = r"C:\Users\Sundareswaran\Kagriculture-v24\submission_Vj_kc_v3.tar.gz"
    
    work = tempfile.mkdtemp(prefix="v3_c1_")
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
    
    hands_actions = list(action.get('hands', []))
    if not hands_actions:
        return action
    
    step = int(observation.get('step', 0) or 0)
    player = observation.get('player', 0)
    farms = observation.get('farms', [])
    if player >= len(farms):
        return action
    my_farm = farms[player]
    hands = my_farm.get('hands', [])
    tiles = my_farm.get('tiles', [])
    private = observation.get('private', {})
    inventories = private.get('inventories', [])
    
    MOVES = [
        (0, -1, 'NORTH'),
        (0, 1, 'SOUTH'),
        (1, 0, 'EAST'),
        (-1, 0, 'WEST')
    ]
    
    modified = False
    for i in range(min(len(hands_actions), len(hands))):
        h_act = hands_actions[i]
        if h_act == ['PASS'] or not h_act:
            hx, hy = hands[i]
            actor_idx = i + 1
            h_inv = inventories[actor_idx] if actor_idx < len(inventories) else {}
            
            # Check current tile
            if 0 <= hy < len(tiles) and 0 <= hx < len(tiles[hy]):
                curr_tile = tiles[hy][hx]
                if isinstance(curr_tile, dict):
                    if curr_tile.get('kind') == 'PLANT':
                        if curr_tile.get('yield_units', 0) > 0:
                            hands_actions[i] = ['HARVEST']
                            modified = True
                            continue
                        elif not curr_tile.get('watered_today', False):
                            hands_actions[i] = ['WATER']
                            modified = True
                            continue
                    elif curr_tile.get('kind') == 'PASTURE':
                        if not curr_tile.get('fed_today', False) and h_inv.get('WHEAT', 0) > 0:
                            hands_actions[i] = ['FEED']
                            modified = True
                            continue
                        elif not curr_tile.get('cared_today', False):
                            hands_actions[i] = ['CARE']
                            modified = True
                            continue
            
            # Check orthogonal neighbors
            stepped = False
            for dx, dy, move_cmd in MOVES:
                nx, ny = hx + dx, hy + dy
                if 0 <= ny < len(tiles) and 0 <= nx < len(tiles[ny]):
                    n_tile = tiles[ny][nx]
                    if isinstance(n_tile, dict):
                        # If neighbor has unwatered plant or ripe crop
                        if n_tile.get('kind') == 'PLANT' and (not n_tile.get('watered_today', False) or n_tile.get('yield_units', 0) > 0):
                            hands_actions[i] = [move_cmd]
                            modified = True
                            stepped = True
                            break
                        # If neighbor has pasture needing feed/care
                        elif n_tile.get('kind') == 'PASTURE' and ((not n_tile.get('fed_today', False) and h_inv.get('WHEAT', 0) > 0) or not n_tile.get('cared_today', False)):
                            hands_actions[i] = [move_cmd]
                            modified = True
                            stepped = True
                            break
            if stepped:
                continue

    if modified:
        action['hands'] = hands_actions
    return action
