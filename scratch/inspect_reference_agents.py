import pandas as pd
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

ref_dir = "replays/raw/reference_agents"

print("=== REFERENCE AGENTS MANIFEST ===")
manifest_df = pd.read_csv(os.path.join(ref_dir, "agents_manifest.csv"))
print(manifest_df.to_string())

print("\n=== BASELINE LEAGUE ===")
league_df = pd.read_csv(os.path.join(ref_dir, "baseline_league.csv"))
print(league_df.to_string())

print("\n=== HEAD TO HEAD GAMES SAMPLE ===")
h2h_df = pd.read_csv(os.path.join(ref_dir, "head_to_head_games.csv"))
print(h2h_df.head(15).to_string())
