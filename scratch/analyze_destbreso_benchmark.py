import pandas as pd
import json
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

dest_dir = "replays/raw/destbreso"
print(f"Inspecting destbreso benchmark dataset in {dest_dir}...")

# Check README
readme_path = os.path.join(dest_dir, "README.md")
if os.path.exists(readme_path):
    print("\n=== README.md ===")
    with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
        print(f.read()[:2000])

# Inspect matchups_top.parquet and matchups_all.parquet
for pfile in ["matchups_top.parquet", "matchups_all.parquet"]:
    ppath = os.path.join(dest_dir, pfile)
    if os.path.exists(ppath):
        print(f"\n=== {pfile} ({os.path.getsize(ppath)/1024/1024:.2f} MB) ===")
        try:
            df = pd.read_parquet(ppath)
            print(f"Rows: {len(df):,}, Columns: {list(df.columns)}")
            print("\nHead 5:")
            print(df.head())
            print("\nSummary of Top Agents/Teams:")
            if 'agent_a' in df.columns and 'agent_b' in df.columns:
                agents = pd.concat([df['agent_a'], df['agent_b']]).value_counts()
                print("Top Agents by frequency:")
                print(agents.head(15))
            elif 'team_a' in df.columns:
                teams = pd.concat([df['team_a'], df['team_b']]).value_counts()
                print("Top Teams by frequency:")
                print(teams.head(15))
        except Exception as e:
            print(f"Error reading {pfile}: {e}")

# Check engine_delta and ladder_forecast
for jfile in ["engine_delta.json", "ladder_forecast.json", "worked_example_routes.json"]:
    jpath = os.path.join(dest_dir, jfile)
    if os.path.exists(jpath):
        print(f"\n=== {jfile} ===")
        try:
            with open(jpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"Keys: {list(data.keys()) if isinstance(data, dict) else len(data)}")
            if isinstance(data, dict):
                for k, v in list(data.items())[:5]:
                    print(f"  {k}: {str(v)[:150]}")
        except Exception as e:
            print(f"Error reading {jfile}: {e}")
