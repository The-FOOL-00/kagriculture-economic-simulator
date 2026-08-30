"""
=============================================================================
KAGGRICULTURE STANDALONE COMPILER
=============================================================================
Compiles modular engine code into a production-ready, zero-dependency main.py
for Kaggle competition submission.
=============================================================================
"""

import os


def compile_main():
    output_path = "main.py"
    
    sections = [
        ("config.py", ["import math"]),
        ("pathfinding.py", ["from collections import deque"]),
        ("engine/world_model.py", ["import copy"]),
        ("engine/market_model.py", []),
        ("engine/town_model.py", []),
        ("engine/economic_evaluator.py", []),
        ("engine/opponent_model.py", []),
        ("engine/labor_scheduler.py", []),
        ("engine/macro_planner.py", []),
        ("engine/unified_agent.py", []),
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
- Deadline-Aware Spatial Labor Scheduler
- Rolling-Horizon Macro Portfolio Planner
=============================================================================
"""

import math
import copy
from collections import deque

'''

    body_lines = []
    
    for filename, _ in sections:
        if not os.path.exists(filename):
            continue
        with open(filename, "r") as f:
            lines = f.readlines()
            
        cleaned = []
        for line in lines:
            # Strip local module imports
            stripped = line.strip()
            if (stripped.startswith("from config") or 
                stripped.startswith("from pathfinding") or 
                stripped.startswith("from engine.") or 
                stripped.startswith("import config") or
                stripped.startswith("import pathfinding")):
                continue
            if stripped.startswith("import math") or stripped.startswith("import copy") or stripped.startswith("from collections import deque"):
                continue
            cleaned.append(line)
            
        body_lines.append(f"\n# {'='*70}\n# SECTION: {filename}\n# {'='*70}\n")
        body_lines.extend(cleaned)

    full_code = header + "".join(body_lines)
    
    with open(output_path, "w") as f:
        f.write(full_code)

    print(f"Successfully compiled {len(full_code.splitlines())} lines to {output_path}")


if __name__ == "__main__":
    compile_main()
