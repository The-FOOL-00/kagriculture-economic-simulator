import json

with open("experiments/EXP-AEC-001/CHECKPOINT.json", "r") as f:
    chk = json.load(f)

completed = chk["completed_seeds"]
print(f"Total completed seeds in checkpoint: {len(completed)}")

mirrored_count = 0
identical_game_count = 0

for seed_str, d in completed.items():
    # In Match A: AEC is seat 0, ctrl is seat 1
    # reward_0_A = aec_score_a, reward_1_A = ctrl_score_a
    r0_a = d["aec_score_a"]
    r1_a = d["ctrl_score_a"]
    
    # In Match B: AEC is seat 1, ctrl is seat 0
    # reward_0_B = ctrl_score_b, reward_1_B = aec_score_b
    r0_b = d["ctrl_score_b"]
    r1_b = d["aec_score_b"]
    
    if r0_a == r0_b and r1_a == r1_b:
        identical_game_count += 1
    else:
        print(f"Divergence in seed {seed_str}: Match A (r0={r0_a}, r1={r1_a}) vs Match B (r0={r0_b}, r1={r1_b})")

print(f"Seeds where Match A and Match B had 100% identical seat rewards (Seat 0 reward match A == Seat 0 reward match B, and Seat 1 reward match A == Seat 1 reward match B): {identical_game_count} / {len(completed)}")
