import pandas as pd

df = pd.read_csv("scratch/ground_truth_replays_dataset.csv")
print("Unique player names in dataset:")
print(df['player'].value_counts())
print("\nFirst 10 rows:")
print(df[['file', 'player', 'p_idx', 'final_reward', 'q2_step', 'q3_step']].head(10))
