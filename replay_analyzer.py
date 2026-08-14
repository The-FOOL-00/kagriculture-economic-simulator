"""
=============================================================================
Kaggriculture Replay Downloader & Match Intelligence Analyzer
=============================================================================
Use this script to analyze local or downloaded Kaggle match replays.
Features:
1. Replay JSON parser & metric extractor.
2. Step-by-step wealth trajectory comparison.
3. Opponent crop strategy deconstruction & market transaction breakdown.
4. Identification of market price crashes and inflection points.
=============================================================================
"""

import json
import os
import sys
import subprocess


def download_episode(episode_id, output_dir="./replays"):
    os.makedirs(output_dir, exist_ok=True)
    cmd = f"kaggle competitions replay {episode_id} -p {output_dir}"
    print(f"Executing: {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(f"Error/Warning: {res.stderr}")
    return os.path.join(output_dir, f"{episode_id}.json")


def analyze_replay(replay_file_path):
    print("=" * 70)
    print(f"ANALYZING MATCH REPLAY: {replay_file_path}")
    print("=" * 70)
    
    with open(replay_file_path, "r") as f:
        data = json.load(f)

    steps = data.get("steps", [])
    if not steps:
        print("Invalid or empty replay file.")
        return

    num_steps = len(steps)
    final_step = steps[-1]
    
    r0 = final_step[0].get("reward", 0)
    r1 = final_step[1].get("reward", 0)
    status0 = final_step[0].get("status", "UNKNOWN")
    status1 = final_step[1].get("status", "UNKNOWN")

    print(f"Total Steps: {num_steps} (30 Days)")
    print(f"Player 0 Final Cash: ${r0:,.2f} [{status0}]")
    print(f"Player 1 Final Cash: ${r1:,.2f} [{status1}]")
    if r0 > r1:
        print(f"Winner: Player 0 (+${r0 - r1:,.2f})")
    elif r1 > r0:
        print(f"Winner: Player 1 (+${r1 - r0:,.2f})")
    else:
        print("Outcome: Tie")

    # Track metrics over time
    day_snapshots = []
    p0_crop_plants = {}
    p1_crop_plants = {}
    p0_sells = {}
    p1_sells = {}

    for step_idx, step in enumerate(steps):
        day = step_idx // 24
        hour = step_idx % 24
        
        obs0 = step[0].get("observation", {})
        farms = obs0.get("farms", [{}, {}])
        f0 = farms[0] if len(farms) > 0 else {}
        f1 = farms[1] if len(farms) > 1 else {}
        
        # Track market actions
        for p_idx, s_agent in enumerate(step):
            act = s_agent.get("action", {}) or {}
            m_orders = act.get("market", []) or []
            for order in m_orders:
                if isinstance(order, list) and len(order) >= 2:
                    op = order[0]
                    item = order[1]
                    qty = int(order[2]) if len(order) >= 3 else 1
                    if op == "SELL":
                        target_dict = p0_sells if p_idx == 0 else p1_sells
                        target_dict[item] = target_dict.get(item, 0) + qty

        # Track plant actions
        for p_idx, s_agent in enumerate(step):
            act = s_agent.get("action", {}) or {}
            farmer_act = act.get("farmer", []) or []
            hands_acts = act.get("hands", []) or []
            all_unit_acts = [farmer_act] + hands_acts
            for u_act in all_unit_acts:
                if isinstance(u_act, list) and len(u_act) >= 2 and u_act[0] == "PLANT":
                    crop = u_act[1]
                    target_dict = p0_crop_plants if p_idx == 0 else p1_crop_plants
                    target_dict[crop] = target_dict.get(crop, 0) + 1

        if hour == 23 or step_idx == num_steps - 1:
            day_snapshots.append({
                "day": day,
                "p0_money": f0.get("money", 0),
                "p1_money": f1.get("money", 0),
                "p0_hands": len(f0.get("hands", [])),
                "p1_hands": len(f1.get("hands", [])),
                "p0_quads": len(f0.get("unlocked_quadrants", ["NW"])),
                "p1_quads": len(f1.get("unlocked_quadrants", ["NW"])),
            })

    print("\n--- Day-by-Day Wealth Progression ---")
    print(f"{'Day':4s} | {'Player 0 Cash':15s} | {'Player 1 Cash':15s} | {'P0 Quads':8s} | {'P1 Quads':8s}")
    print("-" * 65)
    for snap in day_snapshots:
        if snap["day"] in [0, 1, 2, 5, 10, 15, 20, 25, 29]:
            print(f"{snap['day']:4d} | ${snap['p0_money']:14,.0f} | ${snap['p1_money']:14,.0f} | {snap['p0_quads']:8d} | {snap['p1_quads']:8d}")

    print("\n--- Lifetime Crop Planting Breakdown ---")
    print("Player 0 Planted:", p0_crop_plants)
    print("Player 1 Planted:", p1_crop_plants)

    print("\n--- Lifetime Units Sold to Market ---")
    print("Player 0 Sold:", p0_sells)
    print("Player 1 Sold:", p1_sells)
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if path.endswith(".json") and os.path.exists(path):
            analyze_replay(path)
        else:
            # Assume episode ID
            downloaded = download_episode(path)
            if os.path.exists(downloaded):
                analyze_replay(downloaded)
    else:
        print("Usage: python replay_analyzer.py <replay_file.json or episode_id>")
