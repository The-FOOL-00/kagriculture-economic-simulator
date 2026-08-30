import os

ROOT = r"c:\Users\Sundareswaran\Kagriculture"

for b in [4, 8, 12, 14, 18, 24]:
    content = f'''"""Ablation Batch {b} - Clean Wrapper of FrozenControlSlot4"""
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

# Update ablation_c_batch8_only.py
fpath_c = os.path.join(ROOT, "agents", "ablation_c_batch8_only.py")
content_c = f'''"""Ablation C (Batch 8 Only) - Clean Wrapper of FrozenControlSlot4"""
import sys, os
project_root = r"{ROOT}"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.slot4_control_frozen_v2 import FrozenControlSlot4

_instance = FrozenControlSlot4(sell_batch=8)
def agent(obs, configuration=None):
    return _instance(obs, configuration)
'''
with open(fpath_c, "w", encoding="utf-8") as f:
    f.write(content_c)
print(f"Updated: {fpath_c}")
