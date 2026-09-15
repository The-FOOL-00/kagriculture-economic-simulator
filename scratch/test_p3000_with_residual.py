"""
scratch/test_p3000_with_residual.py
===================================
Tests pairing the High-Throughput Production Schedule (Public-3000 / HarvestForge-X)
with our proven Residual Controller against V54++ and against IDLE.
"""

import copy
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "opponents", "public_3000"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))
sys.path.insert(0, os.path.join(BASE_DIR, "scratch", "bundled_modules"))

import kagsim
import main as p3000
import v54_plus_shop
import v54_plus_residual

# Load residual controller from bundled modules
import importlib.util
spec = importlib.util.spec_from_file_location("residual_ctrl", os.path.join(BASE_DIR, "scratch", "bundled_modules", "v49.residual_controller.py"))
res_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(res_mod)

ResidualConfig = res_mod.ResidualConfig
ResidualController = res_mod.ResidualController

# Proven deployed parameters: deficit=2000, delta=4, batch=12
cfg = ResidualConfig(
    preempt_money_deficit=2000.0,
    preempt_minimum_delta=4.0,
    preempt_maximum_batch=12,
    front_money_deficit=2000.0,
    front_supply_threshold=2.0,
)

print("Loaded Residual Controller successfully!")
