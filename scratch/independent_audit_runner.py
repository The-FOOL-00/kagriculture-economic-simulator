"""
Independent Forensic Verification & Audit Runner
Computes ground-truth statistics directly from raw JSON results and simulator files.
"""
import os
import sys
import json
import hashlib
import inspect
import numpy as np
from collections import defaultdict, Counter

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

results_audit = {}

# ----------------------------------------------------------------------
# 1. FILE & SOURCE HASH AUDIT
# ----------------------------------------------------------------------
def get_file_hashes(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, "rb") as f:
        data = f.read()
    return {
        "md5": hashlib.md5(data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "lines": len(data.splitlines())
    }

files_to_hash = [
    "candidates/compiled_v54_plus_residual.py",
    "candidates/compiled_v54_plus_shop.py",
    "candidates/v54_plus_residual.py",
    "candidates/v54_plus_shop.py",
    "candidates/closed_loop_architecture/closed_loop_v2.py",
    "candidates/closed_loop_architecture/closed_loop_v3.py",
    "candidates/closed_loop_architecture/action_arbitrator.py",
    "candidates/closed_loop_architecture/shop_transition_model.py",
    "extracted_agents/dmitrii_lb2800/main.py",
    "extracted_agents/dmitrii_lb2800/policy.py",
    "extracted_agents/dmitrii_lb2800/router_parent.py",
    "extracted_agents/dmitrii_lb2800/terminal_planner.py",
    "external_repos/kaggriculture-cppsim/sim/sim.hpp"
]

hashes_out = {}
for rel in files_to_hash:
    full = os.path.join(BASE_DIR, rel)
    hashes_out[rel] = get_file_hashes(full)

# Also check source inspect hashes (as was done in v2_dmitrii_residual_profit_map.md)
try:
    from closed_loop_v2 import ClosedLoopAgentV2
    import router_parent
    hashes_out["inspect_ClosedLoopAgentV2"] = hashlib.md5(inspect.getsource(ClosedLoopAgentV2).encode()).hexdigest()
    hashes_out["inspect_router_parent"] = hashlib.md5(inspect.getsource(router_parent).encode()).hexdigest()
except Exception as e:
    hashes_out["inspect_error"] = str(e)

results_audit["hashes"] = hashes_out

# ----------------------------------------------------------------------
# 2. V2 vs DMITRII MARGIN SCAN AUDIT (150 seeds)
# ----------------------------------------------------------------------
scan_file = os.path.join(BASE_DIR, "scratch", "v2_dmitrii_margin_scan.json")
if os.path.exists(scan_file):
    with open(scan_file, "r") as f:
        scan_data = json.load(f)
    
    v2_dm_stats = {}
    for split_key in ["disc_margins", "qual_margins", "hold_margins"]:
        margins = scan_data.get(split_key, [])
        n = len(margins)
        wins = sum(1 for m in margins if m > 0)
        losses = sum(1 for m in margins if m < 0)
        ties = sum(1 for m in margins if m == 0)
        mean = float(np.mean(margins))
        median = float(np.median(margins))
        std = float(np.std(margins, ddof=1))
        se = std / np.sqrt(n) if n > 0 else 0
        ci95 = [float(mean - 1.96 * se), float(mean + 1.96 * se)]
        v2_dm_stats[split_key] = {
            "n": n,
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "win_rate": wins / n if n > 0 else 0,
            "mean": mean,
            "median": median,
            "std": std,
            "se": se,
            "ci95": ci95,
            "min": float(min(margins)),
            "max": float(max(margins))
        }
    
    all_margins = scan_data.get("disc_margins", []) + scan_data.get("qual_margins", []) + scan_data.get("hold_margins", [])
    n_all = len(all_margins)
    wins_all = sum(1 for m in all_margins if m > 0)
    losses_all = sum(1 for m in all_margins if m < 0)
    ties_all = sum(1 for m in all_margins if m == 0)
    mean_all = float(np.mean(all_margins))
    median_all = float(np.median(all_margins))
    std_all = float(np.std(all_margins, ddof=1))
    se_all = std_all / np.sqrt(n_all) if n_all > 0 else 0
    ci95_all = [float(mean_all - 1.96 * se_all), float(mean_all + 1.96 * se_all)]
    v2_dm_stats["total"] = {
        "n": n_all,
        "wins": wins_all,
        "losses": losses_all,
        "ties": ties_all,
        "win_rate": wins_all / n_all if n_all > 0 else 0,
        "mean": mean_all,
        "median": median_all,
        "std": std_all,
        "se": se_all,
        "ci95": ci95_all,
        "min": float(min(all_margins)),
        "max": float(max(all_margins)),
        "ci_crosses_zero": (ci95_all[0] <= 0 <= ci95_all[1])
    }
    results_audit["v2_vs_dmitrii_scan"] = v2_dm_stats

# ----------------------------------------------------------------------
# 3. V3 THREE DATASET VALIDATION AUDIT
# ----------------------------------------------------------------------
v3_val_file = os.path.join(BASE_DIR, "scratch", "v3_three_dataset_validation.json")
if os.path.exists(v3_val_file):
    with open(v3_val_file, "r") as f:
        v3_val_data = json.load(f)
    results_audit["v3_three_dataset_validation"] = v3_val_data

# ----------------------------------------------------------------------
# 4. TRUE PIZZA SWEEP AUDIT (6 True Pizza Seeds)
# ----------------------------------------------------------------------
pizza_file = os.path.join(BASE_DIR, "scratch", "true_pizza_sweep_results.json")
if os.path.exists(pizza_file):
    with open(pizza_file, "r") as f:
        pizza_data = json.load(f)
    results_audit["true_pizza_sweep"] = pizza_data

# ----------------------------------------------------------------------
# 5. CROP PORTFOLIO SWEEP AUDIT
# ----------------------------------------------------------------------
crop_file = os.path.join(BASE_DIR, "scratch", "crop_portfolio_sweep_results.json")
if os.path.exists(crop_file):
    with open(crop_file, "r") as f:
        crop_data = json.load(f)
    results_audit["crop_portfolio_sweep"] = crop_data

# ----------------------------------------------------------------------
# 6. ADDITIVE TOMATO DISCOVERY AUDIT
# ----------------------------------------------------------------------
add_file = os.path.join(BASE_DIR, "scratch", "additive_discovery_results.json")
if os.path.exists(add_file):
    with open(add_file, "r") as f:
        add_data = json.load(f)
    results_audit["additive_discovery"] = add_data

# ----------------------------------------------------------------------
# 7. RECONSTRUCTED LIVE LOSSES AUDIT (161 matches)
# ----------------------------------------------------------------------
live_losses_file = os.path.join(BASE_DIR, "scratch", "reconstructed_live_losses_forensics.json")
if os.path.exists(live_losses_file):
    with open(live_losses_file, "r") as f:
        live_losses_data = json.load(f)
    results_audit["live_losses_forensics"] = {
        "count": len(live_losses_data),
        "sample": live_losses_data[:3] if isinstance(live_losses_data, list) else list(live_losses_data.keys())[:5]
    }

# ----------------------------------------------------------------------
# 8. SHOP DEMAND VERIFICATION
# ----------------------------------------------------------------------
import kaggle_environments
from kaggle_environments.envs.kaggriculture import kaggriculture

official_shops = kaggriculture.SHOPS
try:
    from shop_transition_model import SHOP_DEMANDS as claimed_demands
except:
    claimed_demands = None

shop_demand_diffs = {}
if claimed_demands:
    for s, off_items in official_shops.items():
        claimed_items = claimed_demands.get(s, [])
        shop_demand_diffs[s] = {
            "official": sorted(off_items),
            "claimed": sorted(claimed_items),
            "matches": sorted(off_items) == sorted(claimed_items)
        }
results_audit["shop_demand_diffs"] = shop_demand_diffs

# Save all audited numbers to a master audit JSON
out_path = os.path.join(BASE_DIR, "scratch", "independent_audit_summary.json")
with open(out_path, "w") as f:
    json.dump(results_audit, f, indent=2)

print(f"Independent audit summary generated successfully: {out_path}")
print("Total keys audited:", len(results_audit))
print("V2 vs Dmitrii margin scan total mean:", results_audit.get("v2_vs_dmitrii_scan", {}).get("total", {}).get("mean"))
print("V2 vs Dmitrii margin scan CI95:", results_audit.get("v2_vs_dmitrii_scan", {}).get("total", {}).get("ci95"))
print("CI crosses zero?", results_audit.get("v2_vs_dmitrii_scan", {}).get("total", {}).get("ci_crosses_zero"))
for s, diff in shop_demand_diffs.items():
    if not diff["matches"]:
        print(f"Shop mismatch: {s} -> official: {diff['official']} vs claimed: {diff['claimed']}")
