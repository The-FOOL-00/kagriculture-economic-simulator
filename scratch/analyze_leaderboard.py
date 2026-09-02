import os
import sys
import glob
import pandas as pd
import json

sys.stdout.reconfigure(encoding='utf-8')

csv_files = glob.glob("scratch/leaderboard_csv/*.csv")
if not csv_files:
    print("No CSV files found!")
    sys.exit(1)

lb_csv = csv_files[0]
print(f"Reading {lb_csv}...")

df = pd.read_csv(lb_csv)
print(f"Total rows: {len(df)}")
print("Columns:", list(df.columns))

# Sort by Score descending
df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)
df['Rank'] = df.index + 1

print("\n" + "="*90)
print(f"TOP 25 TEAMS ON KAGGRICULTURE PUBLIC LEADERBOARD (Total Teams: {len(df)})")
print("="*90)
cols_to_show = ['Rank', 'TeamName', 'Score', 'LastSubmissionDate', 'SubmissionCount']
print(df[cols_to_show].head(25).to_string(index=False))

print("\n" + "="*90)
print(f"RANKS 26 TO 50:")
print("="*90)
print(df[cols_to_show].iloc[25:50].to_string(index=False))

# Look for our team
print("\n" + "="*90)
print("SEARCHING FOR OUR SUBMISSIONS / TEAM:")
print("="*90)
our_matches = df[df['TeamName'].str.contains('Eldritch|thefool|Sundareswaran|Aethel', case=False, na=False)]
print(our_matches[cols_to_show].to_string(index=False))

# Score distribution statistics
print("\n" + "="*90)
print("SCORE DISTRIBUTION SUMMARY:")
print("="*90)
print(df['Score'].describe())

# Save clean Top 50 to json
top50 = df.head(50).to_dict(orient='records')
with open("scratch/top50_leaderboard.json", "w", encoding="utf-8") as f:
    json.dump(top50, f, indent=2, ensure_ascii=False)
