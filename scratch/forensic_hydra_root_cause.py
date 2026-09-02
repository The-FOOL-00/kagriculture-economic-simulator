# SPDX-License-Identifier: MIT
"""
Root-Cause Forensic Analysis Script for Hydra-Prime V1 Failure
"""

import os
import sys
import json
import copy
import base64
import zlib
import time
import numpy as np
from kaggle_environments import make

# Reference agents
REF_AGENTS = {
    "Aethel_V1": "replays/raw/reference_agents/closer_cleo.py",
    "Broker_Bea": "replays/raw/reference_agents/broker_bea.py",
    "Ledger_Lena": "replays/raw/reference_agents/ledger_lena.py",
    "Slotter_Silas": "replays/raw/reference_agents/slotter_silas.py",
    "Rancher_Rita": "replays/raw/reference_agents/rancher_rita.py",
    "Melon_Mateo": "replays/raw/reference_agents/melon_mateo.py",
    "Fallow_Finn": "replays/raw/reference_agents/fallow_finn.py",
}

def analyze_tape_composition():
    """Analyze the exact animal and crop count in the base _TRACE."""
    with open("replays/raw/reference_agents/closer_cleo.py", "r", encoding="utf-8") as f:
        code = f.read()
    
    # Extract trace
    lines = code.splitlines()
    trace_b85 = lines[46].strip()[1:-1]
    trace = json.loads(zlib.decompress(base64.b85decode(trace_b85)).decode("utf-8"))
    
    animals_bought = {"COW": 0, "SHEEP": 0, "GOOSE": 0}
    crops_bought = {}
    land_bought = 0
    hands_hired = 0
    
    for step_idx, step_act in enumerate(trace):
        market = step_act.get("market", [])
        for order in market:
            if not isinstance(order, list) or not order:
                continue
            op = order[0]
            if op == "BUY_ANIMAL" and len(order) >= 3:
                animals_bought[order[1]] = animals_bought.get(order[1], 0) + int(order[2] or 0)
            elif op == "BUY_SEED" and len(order) >= 3:
                crops_bought[order[1]] = crops_bought.get(order[1], 0) + int(order[2] or 0)
            elif op == "BUY_LAND":
                land_bought += 1
            elif op == "HIRE":
                hands_hired += 1

    print("=== BASE TAPE COMPOSITION ===")
    print(f"Total Steps in Tape: {len(trace)}")
    print(f"Animals Bought: {animals_bought}")
    print(f"Seeds Bought: {crops_bought}")
    print(f"Land Purchases: {land_bought}")
    print(f"Hands Hired: {hands_hired}")
    return {
        "animals_bought": animals_bought,
        "crops_bought": crops_bought,
        "land_bought": land_bought,
        "hands_hired": hands_hired,
        "trace_len": len(trace)
    }

if __name__ == "__main__":
    analyze_tape_composition()
