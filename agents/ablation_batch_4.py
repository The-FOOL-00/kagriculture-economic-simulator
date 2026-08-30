"""Clean Batch 4 Agent - Direct Wrapper of FrozenControlSlot4"""
import sys, os
project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.slot4_control_frozen_v2 import FrozenControlSlot4

_instance = FrozenControlSlot4(sell_batch=4)
def agent(obs, configuration=None):
    return _instance(obs, configuration)
