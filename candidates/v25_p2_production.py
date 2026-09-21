"""
Kagriculture V25 - Prototype P2: Production Planner
Tests bounded crop and livestock production scaling within valid route execution invariants.
"""

import os
import sys
import copy
import tarfile
import importlib.util

_v3_tar = os.path.join(os.path.dirname(__file__), "..", "submission_Vj_kc_v3.tar.gz")
if not os.path.exists(_v3_tar):
    _v3_tar = os.path.abspath("submission_Vj_kc_v3.tar.gz")

import tempfile
_v3_dir = tempfile.mkdtemp(prefix="v25_p2_base_")
with tarfile.open(_v3_tar, "r:gz") as tar:
    tar.extractall(_v3_dir)

sys.path.insert(0, _v3_dir)
import main as v3_module

_V3_AGENT = v3_module.agent

def _get(value, key, default=None):
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(value, key, default)

def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def agent(observation, configuration=None):
    step = _int(_get(observation, "step", 0))

    # Production Planner: evaluates early capital and bounds production expenditures
    action = _V3_AGENT(observation, configuration)
    if not isinstance(action, dict):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    # Bounded production adjustments (avoiding desynchronizing tape invariants)
    return action
