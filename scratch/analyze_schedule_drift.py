import json
import numpy as np

with open("scratch/jit_melon_results/dev_tournament_results.json", "r") as f:
    dev_data = json.load(f)

# Pick seed 2001 (Seat 0 for H, Seat 0 for A)
h_game = next(r for r in dev_data if r["treatment"] == "H" and r["seed"] == 2001 and not r["swapped"])
a_game = next(r for r in dev_data if r["treatment"] == "A" and r["seed"] == 2001 and not r["swapped"])

checkpoints = (24, 48, 72, 100, 120, 144, 168, 192, 216, 240, 264, 288, 336, 360, 432, 504, 600, 650, 719)

print(f"=== DOWNSTREAM SCHEDULE DRIFT AUDIT: TREATMENT A (V2) vs TREATMENT H (JIT) ===")
print("Step | Cash(A)   Cash(H)   | MelonsField(A/H) | Cows(A/H) Sheep(A/H) | Hands(A/H) | ShedWheat(A/H)")
print("-" * 90)

for s in checkpoints:
    t_a = a_game["telemetry"].get(f"step_{s}", {})
    t_h = h_game["telemetry"].get(f"step_{s}", {})
    
    ca = t_a.get("money", 0)
    ch = t_h.get("money", 0)
    ma = t_a.get("melons_planted", 0)
    mh = t_h.get("melons_planted", 0)
    cowa = t_a.get("cows", 0)
    cowh = t_h.get("cows", 0)
    sha = t_a.get("sheep", 0)
    shh = t_h.get("sheep", 0)
    ha = t_a.get("hands", 0)
    hh = t_h.get("hands", 0)
    wa = t_a.get("shed_wheat", 0)
    wh = t_h.get("shed_wheat", 0)
    
    print(f"{s:4d} | ${ca:7.0f} ${ch:7.0f} |       {ma:2d} / {mh:2d}      |   {cowa:1d}/{cowh:1d}       {sha:1d}/{shh:1d}   |    {ha:2d} / {hh:2d}   |     {wa:2d} / {wh:2d}")
