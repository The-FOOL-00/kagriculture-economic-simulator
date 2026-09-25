# SPDX-License-Identifier: MIT
import json
from collections import Counter

def main():
    target_path = "candidates/v32_rlx2/reports/strategic_targets.jsonl"
    with open(target_path, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f]
    
    pos = [r for r in records if r.get("best_delta", 0) > 0]
    print(f"Total evaluated targets in RL-X2: {len(records)}")
    print(f"Total targets with best_delta > 0: {len(pos)}")
    
    action_names = {
        0: "FOLLOW_A7",
        1: "OPPORTUNISTIC_SELL",
        2: "SELECTIVE_PREEMPT_SELL",
        3: "LIQUIDATE_SURPLUS",
        4: "CROP_EXPANSION_MELON",
        5: "CROP_EXPANSION_WHEAT",
        6: "LIVESTOCK_EXPANSION_COW",
        7: "LIVESTOCK_EXPANSION_SHEEP",
        8: "PRESERVE_CASH",
        9: "EXPAND_LAND",
    }
    
    print("\nAction breakdown for positive targets:")
    action_counts = Counter(r["best_action"] for r in pos)
    for act_idx, count in sorted(action_counts.items()):
        print(f"  Action {act_idx} ({action_names.get(act_idx, 'UNKNOWN')}): {count} targets")
        
    print("\nStep breakdown for positive targets:")
    step_counts = Counter(r["step"] for r in pos)
    for step, count in sorted(step_counts.items()):
        print(f"  Step {step} (Day {step//24}): {count} targets")

    print("\nOpponent breakdown for positive targets:")
    opp_counts = Counter(r["opponent_id"] for r in pos)
    for opp, count in sorted(opp_counts.items()):
        print(f"  Opponent {opp}: {count} targets")

    print("\nTop 15 positive targets by delta:")
    top_pos = sorted(pos, key=lambda r: r["best_delta"], reverse=True)
    for i, r in enumerate(top_pos[:15]):
        act_name = action_names.get(r["best_action"], str(r["best_action"]))
        print(f"  {i+1:2d}. Seed {r['seed']} Step {r['step']:3d} Opp {r['opponent_id']:12s} Seat {r['seat']} "
              f"Action {r['best_action']} ({act_name:24s}) Delta: +${r['best_delta']:8.2f} "
              f"(A7=${r['a7_cash']:7.1f} -> Best=${r['best_cash']:7.1f})")

if __name__ == "__main__":
    main()
