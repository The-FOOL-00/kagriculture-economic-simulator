import json

with open("research/v50/loss_regimes/v49_loss_corpus.json") as f:
    corpus = json.load(f)

for i, l in enumerate(corpus):
    seed = l["seed"]
    seat = l["seat"]
    margin = l["final_margin"]
    print(f"\n==========================================")
    print(f"Loss #{i+1}: Seed {seed}, Seat {seat}, Opp {l['opp']}, Margin {margin:+.1f}")
    print(f"Final: V49={l['final_cash_v49']}, Opp={l['final_cash_opp']}, V48={l['final_cash_v48']}, Raw2945={l['final_cash_2945']}")
    print(f"First behind step: {l['first_behind_step']}")
    print(f"Shops: {l['shops']}")
    
    # Check timeline for divergence and trajectory
    tl = l["v49_timeline_samples"]
    # Look at day 25..29 (steps 600..718)
    late_samples = [s for s in tl if s["step"] >= 600]
    for s in late_samples[::4]: # every 4th sample
        print(f"  Step {s['step']}: Cash={s['cash']}, OppCash={s['opp_cash']}, Diff={s['cash_diff']:+.1f}")
