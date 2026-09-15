import sys
import os
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import router_parent as mod_r

policy = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

def classify_shops(shops):
    s_set = set(shops)
    if "YARN_STORE" in s_set:
        return "YARN"
    if "SMOOTHIE_SHOP" in s_set or "ICE_CREAM_SHOP" in s_set:
        return "DAIRY"
    if "PIZZA_SHOP" in s_set:
        return "PIZZA"
    if "PET_CAFE" in s_set:
        return "PET_CAFE"
    return "DISPERSED"

def get_seed_info(seed):
    g = kagsim.Game(seed)
    for _ in range(144):
        g.step(policy.act(g.observe(0)), {})
    shops = tuple(g.observe(0)["town"]["unlocked_shops"])
    category = classify_shops(shops)
    return {"seed": seed, "shops": list(shops), "category": category}

def build_cohort(start_seed, end_seed, target_counts):
    collected = {cat: [] for cat in target_counts}
    for s in range(start_seed, end_seed):
        info = get_seed_info(s)
        cat = info["category"]
        if len(collected[cat]) < target_counts[cat]:
            collected[cat].append(info)
        if all(len(collected[c]) == target_counts[c] for c in target_counts):
            break
            
    # Flatten
    flat_list = []
    for cat, items in collected.items():
        flat_list.extend(items)
    return flat_list, collected

target_counts = {
    "YARN": 12,       # ~24%
    "DAIRY": 10,      # ~20%
    "PIZZA": 10,      # ~20%
    "PET_CAFE": 9,    # ~18%
    "DISPERSED": 9    # ~18%
} # Total = 50 seeds

print("Sampling Qualification Cohort (50000 - 51000)...")
qual_flat, qual_grouped = build_cohort(50001, 51000, target_counts)
print(f"Qualification sampled: {len(qual_flat)} seeds across {list(qual_grouped.keys())}")
with open("scratch/qualification_seeds.json", "w") as f:
    json.dump({"seeds": qual_flat, "counts": {k: len(v) for k, v in qual_grouped.items()}}, f, indent=2)

print("Sampling Fresh Holdout Cohort (60000 - 61000)...")
holdout_flat, holdout_grouped = build_cohort(60001, 61000, target_counts)
print(f"Holdout sampled: {len(holdout_flat)} seeds across {list(holdout_grouped.keys())}")
with open("scratch/fresh_holdout_seeds.json", "w") as f:
    json.dump({"seeds": holdout_flat, "counts": {k: len(v) for k, v in holdout_grouped.items()}}, f, indent=2)

print("Stratified cohorts successfully generated and saved.")
