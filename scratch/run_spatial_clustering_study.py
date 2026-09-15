"""
Spatial Clustering and Contiguity Study
Measures the effect of Compact Spatial Clustering vs Dispersed Allocation on:
- Movement turns per episode
- Productive actions per episode
- Total reward
- Spatial contiguity metric: average distance to nearest same-crop neighbor
"""

import numpy as np
from collections import defaultdict
from kaggle_environments import make

def compute_cluster_compactness(farm_tiles):
    """
    Computes spatial dispersion metric: average pairwise distance within crop clusters.
    Lower score = tighter, more compact cluster.
    """
    crop_positions = defaultdict(list)
    for y in range(len(farm_tiles)):
        for x in range(len(farm_tiles[0])):
            t = farm_tiles[y][x]
            if isinstance(t, dict) and t.get("kind") == "PLANT":
                crop_positions[t.get("crop")].append((x, y))
                
    dispersion = {}
    for crop, pos_list in crop_positions.items():
        if len(pos_list) < 2:
            dispersion[crop] = 0.0
            continue
        pairwise = []
        for i in range(len(pos_list)):
            for j in range(i + 1, len(pos_list)):
                d = abs(pos_list[i][0] - pos_list[j][0]) + abs(pos_list[i][1] - pos_list[j][1])
                pairwise.append(d)
        dispersion[crop] = float(np.mean(pairwise))
    return dispersion

if __name__ == "__main__":
    seeds = [1000, 1001, 1002, 1003, 1004]
    print("Running Spatial Clustering Diagnostics across seeds...")
    
    for agent_name, agent_path in [
        ("CL-Economic-V1 (Baseline)", "candidates/candidate_cl_economic_v1.py"),
        ("CL-Fixed-Zoning (Arm B)", "candidates/candidate_cl_fixed_zoning_v1.py"),
        ("CL-Dynamic-Land (Arm D)", "candidates/candidate_cl_dynamic_land_v1.py"),
        ("Frozen V2 (Benchmark)", "candidates/slot2_aethel_refined_v2.py")
    ]:
        straw_dispersions = []
        melon_dispersions = []
        moves = []
        prods = []
        
        for s in seeds:
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
            env.run([agent_path, "starter"])
            
            # Sample mid-game tile state at Day 16 (step 384)
            tiles_d16 = env.steps[384][0]["observation"]["farms"][0]["tiles"]
            disp = compute_cluster_compactness(tiles_d16)
            if "STRAWBERRY" in disp: straw_dispersions.append(disp["STRAWBERRY"])
            if "MELON" in disp: melon_dispersions.append(disp["MELON"])
            
            # Count movement vs productive actions
            m_count = 0
            p_count = 0
            for step in env.steps:
                act = step[0].get("action", {}) or {}
                all_acts = [act.get("farmer")] + act.get("hands", [])
                for a in all_acts:
                    if a and a[0] in ("NORTH", "SOUTH", "EAST", "WEST"):
                        m_count += 1
                    elif a and a[0] not in ("PASS", "NORTH", "SOUTH", "EAST", "WEST"):
                        p_count += 1
            moves.append(m_count)
            prods.append(p_count)
            
        print(f"[{agent_name}]:")
        print(f"  Mean Move Actions:       {np.mean(moves):.1f}")
        print(f"  Mean Productive Actions: {np.mean(prods):.1f}")
        print(f"  Strawberry Dispersion:   {np.mean(straw_dispersions):.2f} (pairwise dist)")
        print(f"  Melon Dispersion:        {np.mean(melon_dispersions):.2f} (pairwise dist)")
        print("-" * 55)
