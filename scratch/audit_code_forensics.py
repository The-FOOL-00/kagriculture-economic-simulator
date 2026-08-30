"""
Code Forensics: Hardcoding, Opponent Model, Dynamic Allocator, Lookahead
(Parts 20, 21, 22, 23)
"""

import os
import sys
import re
import ast

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 1. Part 20: Audit Opponent Model
def audit_opponent_model():
    print("\n" + "="*80)
    print("PART 20 — AUDIT OPPONENT MODELING (engine/opponent_model.py & agents)")
    print("="*80)
    with open("engine/opponent_model.py", "r") as f:
        opp_code = f.read()
        
    print("OpponentModel class definition found. Lines:", len(opp_code.splitlines()))
    # Check what features are extracted
    features = []
    if "imminent_harvests" in opp_code: features.append("imminent_harvests")
    if "crop_counts" in opp_code: features.append("crop_counts")
    if "animal_counts" in opp_code: features.append("animal_counts")
    if "predicted_glut" in opp_code: features.append("predicted_glut")
    print("Extracted Features:", features)
    
    # Check if agents/hybrid_6c3s_10m.py uses OpponentModel
    with open("agents/hybrid_6c3s_10m.py", "r") as f:
        hybrid_code = f.read()
    uses_opp_model = "OpponentModel" in hybrid_code or "opp_tiles" in hybrid_code or "opp_analysis" in hybrid_code
    print("Does Hybrid_6C3S_10M use OpponentModel?", uses_opp_model)
    if not uses_opp_model:
        print("  -> FORENSIC FINDING: Hybrid_6C3S_10M completely IGNORES opponent observations! Opponent modeling is not connected to the champion planner!")

# 2. Part 21: Audit Dynamic Economic Allocator
def audit_dynamic_allocator():
    print("\n" + "="*80)
    print("PART 21 — AUDIT DYNAMIC ECONOMIC ALLOCATOR (engine/dynamic_allocator.py & agents/hybrid_dynamic_economic.py)")
    print("="*80)
    with open("engine/dynamic_allocator.py", "r") as f:
        alloc_code = f.read()
    with open("agents/hybrid_dynamic_economic.py", "r") as f:
        agent_dyn_code = f.read()
        
    print("Dynamic allocator lines:", len(alloc_code.splitlines()))
    print("Hybrid Dynamic Economic agent lines:", len(agent_dyn_code.splitlines()))
    
    # Check how decisions are computed in hybrid_dynamic_economic.py
    print("\nKey logic in hybrid_dynamic_economic.py:")
    for line in agent_dyn_code.splitlines():
        if "compute_portfolio" in line or "expected_roi" in line or "melon_target" in line or "target_cows" in line:
            print(" ", line.strip())

# 3. Part 22: Audit Lookahead Implementation
def audit_lookahead_planner():
    print("\n" + "="*80)
    print("PART 22 — AUDIT LOOKAHEAD IMPLEMENTATION (agents/hybrid_lookahead.py)")
    print("="*80)
    with open("agents/hybrid_lookahead.py", "r") as f:
        la_code = f.read()
        
    print("Lookahead agent lines:", len(la_code.splitlines()))
    # Check if it does simulation vs approximate arithmetic vs heuristic scoring
    has_sim = "simulate" in la_code or "rollout" in la_code or "tree" in la_code or "branch" in la_code or "evaluate_candidate" in la_code
    print("Contains tree search / rollout simulation?", has_sim)
    
    for line in la_code.splitlines():
        if "lookahead" in line.lower() or "simulate" in line.lower() or "horizon" in line.lower() or "score" in line.lower():
            print(" ", line.strip())

# 4. Part 23: Audit Hidden Hardcoding
def audit_hidden_hardcoding():
    print("\n" + "="*80)
    print("PART 23 — AUDIT HIDDEN HARDCODING ACROSS STRATEGY CODEBASE")
    print("="*80)
    
    hardcoded_items = [
        ("target_cows=6, target_sheep=3", "agents/hybrid_6c3s_10m.py", "Fixed herd capacity", "Unsafe if capital constrained", "Dynamic economic portfolio optimization"),
        ("target_melons=10", "agents/hybrid_6c3s_10m.py", "Fixed early melon tile count", "Assumes fixed $800 capital available", "Dynamic land/cash budget allocation"),
        ("sell_batch_size=14", "agents/hybrid_6c3s_10m.py", "Fixed batch liquidation size", "Empirical heuristic", "Slippage-aware price elasticity curve"),
        ("step % 4 == 0", "agents/hybrid_6c3s_10m.py", "Tied to shop consumption interval", "Safe (matches engine rule)", "Keep synchronized with shop interval"),
        ("day <= 12 for animals", "agents/hybrid_6c3s_10m.py", "Prevents buying animals too late", "Safe heuristic", "Remaining game ROI discounting"),
        ("day <= 26 for planting", "agents/hybrid_6c3s_10m.py", "Crop maturity cutoff", "Safe (crops need 2-4 days)", "Per-crop remaining growth horizon"),
        ("feed_reserve = animals * 2", "agents/hybrid_6c3s_10m.py", "2-day wheat starvation buffer", "Safe (avoids starvation)", "Dynamically track exact wheat days"),
        ("n_unlocked == 0 and money >= 1250 (Day 0 NE)", "agents/hybrid_6c3s_10m.py", "Hardcoded NE quadrant expansion", "Requires exactly $1,000 + buffer", "Dynamic land purchase valuation"),
        ("n_unlocked == 1 and money >= 2500 and day <= 14 (SW)", "agents/hybrid_6c3s_10m.py", "Hardcoded SW quadrant expansion", "Requires $2,000 + buffer", "Dynamic expansion planner"),
    ]
    
    print(f"{'Hardcoded Rule':32} | {'File':25} | {'Why It Exists':30} | {'Safe?':25} | {'Recommended Improvement'}")
    print("-" * 140)
    for rule, file, why, safe, imp in hardcoded_items:
        print(f"{rule:32} | {file:25} | {why:30} | {safe:25} | {imp}")

if __name__ == "__main__":
    audit_opponent_model()
    audit_dynamic_allocator()
    audit_lookahead_planner()
    audit_hidden_hardcoding()
