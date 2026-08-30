"""
=============================================================================
KAGGRICULTURE STANDALONE COMPILER (CANONICAL BUILD SYSTEM)
=============================================================================
Compiles modular engine subsystems into a production-ready, zero-dependency main.py
for Kaggle competition deployment.
Guarantees byte-for-byte deterministic compilation.
=============================================================================
"""

import os
import sys
import hashlib


def compile_main(output_path="main.py"):
    sections = [
        "config.py",
        "pathfinding.py",
        "engine/world_model.py",
        "engine/market_model.py",
        "engine/town_model.py",
        "engine/economic_evaluator.py",
        "engine/opponent_model.py",
        "engine/livestock_engine.py",
        "engine/dynamic_allocator.py",
        "engine/market_executor.py",
        "engine/labor_scheduler.py",
        "engine/macro_planner.py",
        "engine/unified_agent.py",
    ]

    header = '''"""
=============================================================================
Kaggriculture Apex Titan Grandmaster (Production Deployment Agent)
=============================================================================
Autonomous Modular Architecture:
- World Model & Farm Grid Representation
- Dynamic Price & Slippage Market Model
- Town Demand & Scarcity Consumption Forecaster
- Net Present Value (NPV) & Crop ROI Evaluator
- Opponent Farm Radar & Anti-Glut Frontrunner
- Livestock Fleet Engine (Cows, Sheep, Geese, Pastures, Feed Reserve)
- Dynamic Economic Crop Allocator (Melon, Carrot, Wheat)
- Elasticity-Aware Market Executor
- Deadline-Aware Spatial Labor Scheduler
- Rolling-Horizon Macro Portfolio Planner
=============================================================================
"""

import math
import copy
import random
from collections import deque

'''

    body_lines = []

    for filename in sections:
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Compiler missing required module: {filename}")
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()

        cleaned = []
        for line in lines:
            stripped = line.strip()
            # Strip module-level local imports
            if (stripped.startswith("from config") or
                stripped.startswith("from pathfinding") or
                stripped.startswith("from engine.") or
                stripped.startswith("import config") or
                stripped.startswith("import pathfinding")):
                continue
            # Strip standard library imports that are already in header
            if (stripped.startswith("import math") or
                stripped.startswith("import copy") or
                stripped.startswith("import random") or
                stripped.startswith("from collections import deque")):
                continue
            cleaned.append(line)

        body_lines.append(f"\n# {'='*70}\n# SECTION: {filename}\n# {'='*70}\n")
        body_lines.extend(cleaned)

    full_code = header + "".join(body_lines)

    # Normalize line endings to \n for deterministic cross-platform hashing
    normalized_code = "\n".join(full_code.splitlines()) + "\n"

    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(normalized_code)

    sha = hashlib.sha256(normalized_code.encode("utf-8")).hexdigest()
    print(f"Successfully compiled {len(normalized_code.splitlines())} lines to {output_path} (SHA256: {sha})")
    return sha


if __name__ == "__main__":
    compile_main()
