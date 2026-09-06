import pandas as pd
import os

print("=== GEORGYMAMARIN AGENTS.CSV ===")
df_agents = pd.read_csv("replays/raw/georgymamarin/agents.csv")
print("Shape:", df_agents.shape)
print("Columns:", df_agents.columns.tolist())
print(df_agents.head(5))

print("\n=== GEORGYMAMARIN DAILY_STATS.CSV ===")
df_daily = pd.read_csv("replays/raw/georgymamarin/daily_stats.csv")
print("Shape:", df_daily.shape)
print("Columns:", df_daily.columns.tolist())
print(df_daily.head(5))

print("\n=== VIJAIKM FARMER_ACTIONS.CSV ===")
df_farmer = pd.read_csv("replays/raw/vijaikm/farmer_actions.csv", nrows=5)
print("Farmer actions shape:", df_farmer.shape)
print(df_farmer)
