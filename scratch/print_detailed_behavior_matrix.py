import json

with open("scratch/top_meta_behavior_matrix.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Focus on primary archetypes
primary_agents = [
    "Crop Dusta", "KawattaTaido", "Whyme Labs", "Yuan800", "MtN", "Eldritch", "Yuyajk", "GAYATHRI SALINI"
]

print("=" * 130)
print("GROUND-TRUTH TOP-META BEHAVIOR MATRIX")
print("=" * 130)

for agent in primary_agents:
    if agent not in data:
        continue
    d = data[agent]
    print(f"\n[{agent.upper()}] (Matches: {d['matches']}) | Mean Reward: ${d['final_reward']:,.1f}")
    print(f"  * Macro Timing: Q2 Unlock @ Step {d['q2_step']} (Day {d['q2_step']/24:.1f}) | Q3 Unlock @ Step {d['q3_step']} (Day {d['q3_step']/24:.1f}) | Q4 Unlock: {d['q4_step']}")
    print(f"  * Day 0 Setup: Hires: {d['day0_hires']} | Pastures: {d['day0_pastures']} | Cows: {d['day0_cows']} | Sheep: {d['day0_sheep']} | Post-Setup Cash: ${d['day0_money']:,.1f}")
    print(f"  * Infrastructure: Pastures: D5={d['pastures_d5']} -> D11={d['pastures_d11']} -> D29={d['pastures_d29']}")
    print(f"  * Herd: Cows: D5={d['cows_d5']} -> D11={d['cows_d11']} -> D29={d['cows_d29']} | Sheep: D5={d['sheep_d5']} -> D11={d['sheep_d11']} -> D29={d['sheep_d29']}")
    print(f"  * Labor: Workers: D5={d['workers_d5']} -> D11={d['workers_d11']} -> D29={d['workers_d29']}")
    print(f"  * Cash Trajectory: D5=${d['money_d5']:,.1f} -> D11=${d['money_d11']:,.1f} -> D20=${d['money_d20']:,.1f} -> D29=${d['money_d29']:,.1f}")
    print(f"  * Production/Sales: Milk: {d['milk_sold']} | Wool: {d['wool_sold']} | Fertilizer: {d['fertilizer_sold']} | Melons: {d['melons_sold']} | Strawberries: {d['strawberries_sold']} | Tomatoes: {d['tomatoes_sold']}")
    print(f"  * Wheat Economics: Wheat Bought: {d['wheat_bought']} units | Wheat Sold: {d['wheat_sold']} units")
    print(f"  * Micro-Mechanisms: Fert Sale Hour: {d['fert_sale_hours_mode']}:00 (batch: {d['fert_avg_batch']}) | First Milk Sale: Step {d['milk_first_sale_step']} | Sells Before Buys: {d['sells_before_buys_turns']} turns | Last Seed Buy: Step {d['last_seed_buy_step']} | Last Animal Buy: Step {d['last_animal_buy_step']}")
