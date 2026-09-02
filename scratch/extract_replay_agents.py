import os
import sys
import json
import base64
import zlib

sys.stdout.reconfigure(encoding='utf-8')

os.makedirs("opponents", exist_ok=True)

def extract_agent_from_replay(replay_path, player_idx, out_path, agent_name):
    print(f"\nExtracting {agent_name} from {replay_path} (Player {player_idx})...")
    with open(replay_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    steps = data.get("steps", [])
    if not steps:
        print("Empty replay!")
        return False
        
    actions = []
    for step in steps:
        s_agent = step[player_idx] if len(step) > player_idx else {}
        act = s_agent.get("action", {}) or {}
        # Clean action dict
        clean_act = {
            "farmer": act.get("farmer", ["PASS"]),
            "hands": act.get("hands", []),
            "market": act.get("market", [])
        }
        actions.append(clean_act)
        
    print(f"Extracted {len(actions)} steps for {agent_name}.")
    
    # Compress actions with zlib + base85
    compressed_bytes = zlib.compress(json.dumps(actions).encode('utf-8'))
    b85_str = base64.b85encode(compressed_bytes).decode('utf-8')
    
    code = f'''# Auto-extracted Replay Agent: {agent_name}
# Extracted from {os.path.basename(replay_path)} (Player {player_idx})
import base64
import copy
import json
import zlib

_TRACE = json.loads(zlib.decompress(base64.b85decode(
    {b85_str!r}
)).decode("utf-8"))

def agent(obs, config=None):
    step = min(int(obs.get("step", 0) or 0), len(_TRACE) - 1)
    return copy.deepcopy(_TRACE[step])
'''
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(code)
        
    print(f"Saved to {out_path} ({os.path.getsize(out_path):,} bytes)")
    return True

# 1. Extract KawattaTaido (Player 0 from Episode 104817623)
extract_agent_from_replay(
    "scratch/replays/V2_Loss_vs_KawattaTaido_104817623.json",
    0,
    "opponents/replay_kawatta_taido.py",
    "KawattaTaido (Live Wool Flooder)"
)

# 2. Extract MtN (Player 0 from Episode 104824200)
extract_agent_from_replay(
    "scratch/replays/Top_MtN_104824200_104824200.json",
    0,
    "opponents/replay_mtn.py",
    "MtN (Rank 1 Champion)"
)

# 3. Extract Crop Dusta (Player 0 from Episode 104824599)
extract_agent_from_replay(
    "scratch/replays/top_episodes_top_55929317_104824599.json",
    0,
    "opponents/replay_crop_dusta.py",
    "Crop Dusta (Rank 2 Champion)"
)

# 4. Extract Whyme Labs (Player 1 from Episode 104824599)
extract_agent_from_replay(
    "scratch/replays/top_episodes_top_55929317_104824599.json",
    1,
    "opponents/replay_whyme_labs.py",
    "Whyme Labs (Rank 5 Champion)"
)

# 5. Extract Yuan800 (Player 1 from Episode 104824200)
extract_agent_from_replay(
    "scratch/replays/Top_MtN_104824200_104824200.json",
    1,
    "opponents/replay_yuan800.py",
    "Yuan800 (Rank 3 Champion)"
)
