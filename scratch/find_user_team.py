import pandas as pd

df = pd.read_csv("scratch/leaderboard_csv/kaggriculture-publicleaderboard-2026-09-06T12_46_59.csv")
print("Total teams:", len(df))

# Check team members or names
candidates = df[df['TeamMemberUserNames'].str.contains('sundar|aethel|vijaikm|destbreso', case=False, na=False)]
print("Matches in Leaderboard:")
for idx, r in candidates.iterrows():
    print(dict(r))

# Check top 50 stats:
print("\n--- Leaderboard Milestones ---")
print("Top 1:", df.iloc[0]['Score'], df.iloc[0]['TeamName'])
print("Top 5:", df.iloc[4]['Score'], df.iloc[4]['TeamName'])
print("Top 10:", df.iloc[9]['Score'], df.iloc[9]['TeamName'])
print("Top 20:", df.iloc[19]['Score'], df.iloc[19]['TeamName'])
print("Top 50:", df.iloc[49]['Score'], df.iloc[49]['TeamName'])
