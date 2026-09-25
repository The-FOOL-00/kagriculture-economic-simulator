import json

recs = [json.loads(line) for line in open("route_counterfactuals.jsonl")]
for r in recs:
    if r["target_route"] == "R2_DMITRII":
        seed = r["seed"]
        step = r["switch_step"]
        a7 = r["base_a7_cash"]
        sw = r["switched_cash"]
        delta = r["delta_vs_a7"]
        print(f"Seed {seed} @ step {step:3d}: A7=${a7:,.0f} -> Switch=${sw:,.0f} (Delta={delta:+,.0f})")
