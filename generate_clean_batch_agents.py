import os

ROOT = r"c:\Users\Sundareswaran\Kagriculture"
batch_sizes = [4, 8, 12, 14, 16, 18, 20, 24]

for b in batch_sizes:
    content = f'''"""Clean Batch {b} Agent - Direct Wrapper of FrozenControlSlot4"""
import sys, os
project_root = r"{ROOT}"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.slot4_control_frozen_v2 import FrozenControlSlot4

_instance = FrozenControlSlot4(sell_batch={b})
def agent(obs, configuration=None):
    return _instance(obs, configuration)
'''
    fpath = os.path.join(ROOT, "agents", f"ablation_batch_{b}.py")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated: {fpath}")

print("All clean batch agents generated successfully.")
