import os
import sys
import time
import math
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
ablation_dir = os.path.join(project_root, "scratch", "clean_ablations")
os.makedirs(ablation_dir, exist_ok=True)

with open(os.path.join(project_root, "agents", "apex_v2_frozen.py"), "r", encoding="utf-8") as f:
    base_code = f.read()

def generate_ablation(filename, feed_buffer=2, cycle2_melons=8, sell_batch=24, emergency=True, target_melons=15, day0_land=True):
    lines = base_code.splitlines()
    cut_idx = 0
    for i, l in enumerate(lines):
        if l.startswith("_agent_instance ="):
            cut_idx = i
            break

    custom_inst = f"""
_agent_instance = ApexSynthesisV2Agent(
    target_cows=8,
    target_sheep=4,
    target_geese=0,
    target_melons={target_melons},
    cycle2_melons={cycle2_melons},
    sell_batch={sell_batch},
    feed_buffer_days={feed_buffer},
    emergency_liquidity={emergency},
    care_animals=True
)
def agent(obs, configuration=None):
    return _agent_instance(obs, configuration)
"""
    new_code = "\n".join(lines[:cut_idx]) + "\n" + custom_inst
    
    # If disabling emergency liquidity, remove emergency override
    if not emergency:
        new_code = new_code.replace("if self.emergency_liquidity:", "if False:")
        
    # If disabling day0 land opening
    if not day0_land:
        new_code = new_code.replace("if n_unlocked == 0 and money >= cost + 250:", "if n_unlocked == 0 and money >= cost + 1500:")

    fpath = os.path.join(ablation_dir, filename)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(new_code)
    return fpath

# Generate 1-factor ablation files
ablations = [
    ("apex_base.py", {"feed_buffer": 2, "cycle2_melons": 8, "sell_batch": 24, "emergency": True, "target_melons": 15, "day0_land": True}),
    ("apex_no_2day_feed.py", {"feed_buffer": 4, "cycle2_melons": 8, "sell_batch": 24, "emergency": True, "target_melons": 15, "day0_land": True}),
    ("apex_no_cycle2_melon.py", {"feed_buffer": 2, "cycle2_melons": 0, "sell_batch": 24, "emergency": True, "target_melons": 15, "day0_land": True}),
    ("apex_no_batch24.py", {"feed_buffer": 2, "cycle2_melons": 8, "sell_batch": 14, "emergency": True, "target_melons": 15, "day0_land": True}),
    ("apex_no_emergency.py", {"feed_buffer": 2, "cycle2_melons": 8, "sell_batch": 24, "emergency": False, "target_melons": 15, "day0_land": True}),
    ("apex_no_day0_land.py", {"feed_buffer": 2, "cycle2_melons": 8, "sell_batch": 24, "emergency": True, "target_melons": 15, "day0_land": False}),
]

for fname, kwargs in ablations:
    generate_ablation(fname, **kwargs)

print("Generated all 1-factor clean ablation files.")
