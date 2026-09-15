import json

with open("scratch/strawberry_capacity_experiment_results.json") as f:
    d = json.load(f)

print("DETAILED TELEMETRY COMPARISON ACROSS ARMS:")
print(f"{'ARM':<6} {'NAME':<25} {'STRAW_SOLD':<12} {'STRAW_HARV':<12} {'FERT_APP':<10} {'MOVES':<8} {'PROD':<8} {'IDLE':<8} {'FEED_BGT':<10}")
for arm, s in d["summary"].items():
    print(f"{arm:<6} {s['name']:<25} {s['mean_straw_sold']:>8.1f}u    {s['mean_straw_harvested']:>8.1f}u    {s['mean_fert_applied']:>6.1f}     {s['mean_moves']:>6.0f}   {s['mean_prod']:>6.0f}   {s['mean_idle']:>6.0f}   {s['mean_feed_bought']:>6.1f}u")
