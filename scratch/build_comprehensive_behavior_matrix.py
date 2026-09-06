import pandas as pd
import json

df = pd.read_csv("scratch/ground_truth_replays_dataset.csv")

# Clean player names
df['player_clean'] = df['player'].apply(lambda x: str(x).encode('ascii', 'replace').decode('ascii'))

# Filter top competitive agents
top_archetypes = [
    "Crop Dusta", "Whyme Labs", "Yuan800", "MtN", "KawattaTaido",
    "3??", "Eldritch", "Yuyajk", "GAYATHRI SALINI", "MrGS"
]

sub_df = df[df['player_clean'].isin(top_archetypes)].copy()

print(f"Total competitive match records: {len(sub_df)}")

# Group by player
metrics = [
    'final_reward', 'day0_money', 'day0_hires', 'day0_pastures', 'day0_cows', 'day0_sheep',
    'q2_step', 'q3_step', 'q4_step',
    'pastures_d5', 'pastures_d11', 'pastures_d29',
    'cows_d5', 'cows_d11', 'cows_d29',
    'sheep_d5', 'sheep_d11', 'sheep_d29',
    'workers_d5', 'workers_d11', 'workers_d29',
    'money_d5', 'money_d11', 'money_d20', 'money_d29',
    'wheat_bought', 'wheat_sold', 'milk_sold', 'wool_sold', 'fertilizer_sold',
    'melons_sold', 'strawberries_sold', 'tomatoes_sold', 'carrots_sold',
    'fert_sale_hours_mode', 'fert_avg_batch', 'milk_first_sale_step',
    'sells_before_buys_turns', 'buys_before_sells_turns',
    'last_seed_buy_step', 'last_animal_buy_step'
]

grouped = sub_df.groupby('player_clean')[metrics].mean().round(1)

# Sort by final reward
grouped = grouped.sort_values(by='final_reward', ascending=False)

print("\n--- BEHAVIOR MATRIX SUMMARY ---")
print(grouped[['final_reward', 'q2_step', 'q3_step', 'pastures_d29', 'cows_d29', 'sheep_d29', 'workers_d29', 'wheat_bought', 'milk_sold', 'wool_sold', 'fertilizer_sold']])

# Export to json and csv
grouped.to_csv("scratch/top_meta_behavior_matrix.csv")
grouped.to_json("scratch/top_meta_behavior_matrix.json", orient="index", indent=2)

print("\nSaved top_meta_behavior_matrix.csv and top_meta_behavior_matrix.json successfully.")
