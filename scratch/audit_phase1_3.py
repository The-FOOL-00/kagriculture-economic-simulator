# SPDX-License-Identifier: MIT
import json
from collections import Counter, defaultdict
import numpy as np

with open("benchmark_results.json", "r") as f:
    data = json.load(f)

legs = data["raw_legs"]
a7_map = {(l["seed"], l["opponent"], l["seat"]): l for l in legs if l["policy"] == "A7_BASELINE"}
v35_map = {(l["seed"], l["opponent"], l["seat"]): l for l in legs if l["policy"] == "V35_FULL"}

print(f"Total paired matches: {len(a7_map)}")

def get_class(cand_c, opp_c):
    if cand_c > opp_c:
        return "WIN"
    elif cand_c == opp_c:
        return "TIE"
    else:
        return "LOSS"

transitions = Counter()
non_wins_v35 = []

for k, a7 in a7_map.items():
    v35 = v35_map[k]
    a7_c = get_class(a7["cand_cash"], a7["opp_cash"])
    v35_c = get_class(v35["cand_cash"], v35["opp_cash"])
    transitions[(a7_c, v35_c)] += 1
    if v35_c != "WIN":
        non_wins_v35.append((k, a7_c, v35_c, a7["cand_cash"], a7["opp_cash"], v35["cand_cash"], v35["opp_cash"]))

print("\n--- TRANSITION MATRIX ---")
for (a, v), count in sorted(transitions.items()):
    print(f"A7 {a:4s} -> V35 {v:4s}: {count:3d}")

print("\n--- V35 NON-WINS ---")
for item in non_wins_v35:
    k, a7_c, v35_c, a7_cc, a7_oc, v35_cc, v35_oc = item
    print(f"Key {k}: A7 {a7_c} ({a7_cc:.1f} vs {a7_oc:.1f}) -> V35 {v35_c} ({v35_cc:.1f} vs {v35_oc:.1f}), diff={v35_cc - a7_cc:+.1f}")

# Breakdown by opponent
print("\n--- OPPONENT BREAKDOWN ---")
opponents = sorted(list(set(l["opponent"] for l in legs)))
for opp in opponents:
    opp_keys = [k for k in a7_map if k[1] == opp]
    n = len(opp_keys)
    a7_wins_strict = sum(1 for k in opp_keys if a7_map[k]["cand_cash"] > a7_map[k]["opp_cash"])
    a7_ties = sum(1 for k in opp_keys if a7_map[k]["cand_cash"] == a7_map[k]["opp_cash"])
    a7_losses = sum(1 for k in opp_keys if a7_map[k]["cand_cash"] < a7_map[k]["opp_cash"])
    a7_points = a7_wins_strict + 0.5 * a7_ties

    v35_wins_strict = sum(1 for k in opp_keys if v35_map[k]["cand_cash"] > v35_map[k]["opp_cash"])
    v35_ties = sum(1 for k in opp_keys if v35_map[k]["cand_cash"] == v35_map[k]["opp_cash"])
    v35_losses = sum(1 for k in opp_keys if v35_map[k]["cand_cash"] < v35_map[k]["opp_cash"])
    v35_points = v35_wins_strict + 0.5 * v35_ties

    deltas = [v35_map[k]["cand_cash"] - a7_map[k]["cand_cash"] for k in opp_keys]
    rescues = sum(1 for k in opp_keys if a7_map[k]["cand_cash"] <= a7_map[k]["opp_cash"] and v35_map[k]["cand_cash"] > v35_map[k]["opp_cash"])
    casualties = sum(1 for k in opp_keys if a7_map[k]["cand_cash"] > a7_map[k]["opp_cash"] and v35_map[k]["cand_cash"] <= v35_map[k]["opp_cash"])

    print(f"Opponent {opp:12s} (N={n}):")
    print(f"  A7 : W={a7_wins_strict:2d}, T={a7_ties:2d}, L={a7_losses:2d} | pts={a7_points:4.1f} ({a7_points/n*100:5.1f}%)")
    print(f"  V35: W={v35_wins_strict:2d}, T={v35_ties:2d}, L={v35_losses:2d} | pts={v35_points:4.1f} ({v35_points/n*100:5.1f}%)")
    print(f"  Rescues: {rescues}, Casualties: {casualties}")
    print(f"  Paired Cash Delta: mean={np.mean(deltas):+.2f}, median={np.median(deltas):+.2f}, min={np.min(deltas):+.2f}, max={np.max(deltas):+.2f}")

# Breakdown by Seed
print("\n--- SEED BREAKDOWN ---")
seeds = sorted(list(set(k[0] for k in a7_map)))
for s in seeds:
    s_keys = [k for k in a7_map if k[0] == s]
    n = len(s_keys)
    cohort = "DEV" if s in seeds[:5] else "FRESH"
    a7_pts = sum(1 if a7_map[k]["cand_cash"] > a7_map[k]["opp_cash"] else (0.5 if a7_map[k]["cand_cash"] == a7_map[k]["opp_cash"] else 0) for k in s_keys)
    v35_pts = sum(1 if v35_map[k]["cand_cash"] > v35_map[k]["opp_cash"] else (0.5 if v35_map[k]["cand_cash"] == v35_map[k]["opp_cash"] else 0) for k in s_keys)
    deltas = [v35_map[k]["cand_cash"] - a7_map[k]["cand_cash"] for k in s_keys]
    rescues = sum(1 for k in s_keys if a7_map[k]["cand_cash"] <= a7_map[k]["opp_cash"] and v35_map[k]["cand_cash"] > v35_map[k]["opp_cash"])
    casualties = sum(1 for k in s_keys if a7_map[k]["cand_cash"] > a7_map[k]["opp_cash"] and v35_map[k]["cand_cash"] <= v35_map[k]["opp_cash"])
    print(f"Seed {s} ({cohort}, N={n}): A7={a7_pts:4.1f}/{n} ({a7_pts/n*100:.1f}%), V35={v35_pts:4.1f}/{n} ({v35_pts/n*100:.1f}%), Rescues={rescues}, Cas={casualties}, delta_mean={np.mean(deltas):+.2f}")

# Breakdown by Cohort
print("\n--- COHORT BREAKDOWN ---")
for c_name, c_seeds in [("DEV", seeds[:5]), ("FRESH", seeds[5:])]:
    c_keys = [k for k in a7_map if k[0] in c_seeds]
    n = len(c_keys)
    a7_pts = sum(1 if a7_map[k]["cand_cash"] > a7_map[k]["opp_cash"] else (0.5 if a7_map[k]["cand_cash"] == a7_map[k]["opp_cash"] else 0) for k in c_keys)
    v35_pts = sum(1 if v35_map[k]["cand_cash"] > v35_map[k]["opp_cash"] else (0.5 if v35_map[k]["cand_cash"] == v35_map[k]["opp_cash"] else 0) for k in c_keys)
    deltas = [v35_map[k]["cand_cash"] - a7_map[k]["cand_cash"] for k in c_keys]
    rescues = sum(1 for k in c_keys if a7_map[k]["cand_cash"] <= a7_map[k]["opp_cash"] and v35_map[k]["cand_cash"] > v35_map[k]["opp_cash"])
    casualties = sum(1 for k in c_keys if a7_map[k]["cand_cash"] > a7_map[k]["opp_cash"] and v35_map[k]["cand_cash"] <= v35_map[k]["opp_cash"])
    print(f"Cohort {c_name} (N={n}): A7={a7_pts:4.1f}/{n} ({a7_pts/n*100:5.2f}%), V35={v35_pts:4.1f}/{n} ({v35_pts/n*100:5.2f}%), Rescues={rescues}, Cas={casualties}, delta_mean={np.mean(deltas):+.2f}, delta_min={np.min(deltas):+.2f}")

# Breakdown by Seat
print("\n--- SEAT BREAKDOWN ---")
for seat in [0, 1]:
    seat_keys = [k for k in a7_map if k[2] == seat]
    n = len(seat_keys)
    a7_pts = sum(1 if a7_map[k]["cand_cash"] > a7_map[k]["opp_cash"] else (0.5 if a7_map[k]["cand_cash"] == a7_map[k]["opp_cash"] else 0) for k in seat_keys)
    v35_pts = sum(1 if v35_map[k]["cand_cash"] > v35_map[k]["opp_cash"] else (0.5 if v35_map[k]["cand_cash"] == v35_map[k]["opp_cash"] else 0) for k in seat_keys)
    deltas = [v35_map[k]["cand_cash"] - a7_map[k]["cand_cash"] for k in seat_keys]
    rescues = sum(1 for k in seat_keys if a7_map[k]["cand_cash"] <= a7_map[k]["opp_cash"] and v35_map[k]["cand_cash"] > v35_map[k]["opp_cash"])
    casualties = sum(1 for k in seat_keys if a7_map[k]["cand_cash"] > a7_map[k]["opp_cash"] and v35_map[k]["cand_cash"] <= v35_map[k]["opp_cash"])
    print(f"Seat {seat} (N={n}): A7={a7_pts:4.1f}/{n} ({a7_pts/n*100:5.2f}%), V35={v35_pts:4.1f}/{n} ({v35_pts/n*100:5.2f}%), Rescues={rescues}, Cas={casualties}, delta_mean={np.mean(deltas):+.2f}, delta_min={np.min(deltas):+.2f}")
