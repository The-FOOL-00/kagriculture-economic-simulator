import sys
import json
import os
from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()
api.authenticate()

os.makedirs("scratch", exist_ok=True)
os.makedirs("replays/raw", exist_ok=True)

# Competitions details
print("=== COMPETITION DETAILS ===")
try:
    comp = api.competition_view("kaggriculture")
    print(f"Ref: {comp.ref}")
    print(f"Title: {comp.title}")
    print(f"Deadline: {getattr(comp, 'deadline', None)}")
    print(f"Evaluation: {getattr(comp, 'evaluationMetric', None)}")
except Exception as e:
    print(f"Comp error: {e}")

# Leaderboard
print("\n=== LEADERBOARD (Top 100) ===")
try:
    lb = api.competition_leaderboard_view("kaggriculture")
    lb_data = []
    for i, e in enumerate(lb):
        row = {
            "rank": i + 1,
            "teamId": getattr(e, 'teamId', getattr(e, 'team_id', None)),
            "teamName": str(getattr(e, 'teamName', getattr(e, 'team_name', ''))),
            "score": float(getattr(e, 'score', 0.0)),
            "submissionDate": str(getattr(e, 'submissionDate', getattr(e, 'submission_date', '')))
        }
        lb_data.append(row)
        if i < 30:
            print(f"#{row['rank']:2d} | Score: {row['score']:7.1f} | Team: {row['teamName']} | Date: {row['submissionDate']}")
    with open("scratch/leaderboard_full.json", "w", encoding="utf-8") as f:
        json.dump(lb_data, f, indent=2)
except Exception as e:
    print(f"Leaderboard error: {e}")

# Datasets files check
print("\n=== INSPECTING GEORGYMAMARIN/KAGGRICULTURE-EPISODES ===")
try:
    files = api.dataset_list_files("georgymamarin/kaggriculture-episodes")
    print(f"Files in georgymamarin/kaggriculture-episodes ({len(files.files)} files):")
    for f in files.files:
        print(f"  - {f.name} ({f.size} bytes)")
except Exception as e:
    print(f"Dataset files error: {e}")

print("\n=== INSPECTING KAGGLE/KAGGRICULTURE-EPISODES-INDEX ===")
try:
    files = api.dataset_list_files("kaggle/kaggriculture-episodes-index")
    print(f"Files in kaggle/kaggriculture-episodes-index ({len(files.files)} files):")
    for f in files.files:
        print(f"  - {f.name} ({f.size} bytes)")
except Exception as e:
    print(f"Dataset files error: {e}")

print("\n=== INSPECTING DESTBRESO/KAGGRICULTURE-BENCHMARK-MATCHUPS ===")
try:
    files = api.dataset_list_files("destbreso/kaggriculture-benchmark-matchups")
    print(f"Files in destbreso/kaggriculture-benchmark-matchups ({len(files.files)} files):")
    for f in files.files:
        print(f"  - {f.name} ({f.size} bytes)")
except Exception as e:
    print(f"Dataset files error: {e}")

print("\n=== INSPECTING RAYKKRETZSCHMAR/KAGGRICULTURE-REFERENCE-AGENTS ===")
try:
    files = api.dataset_list_files("raykkretzschmar/kaggriculture-reference-agents")
    print(f"Files in raykkretzschmar/kaggriculture-reference-agents ({len(files.files)} files):")
    for f in files.files:
        print(f"  - {f.name} ({f.size} bytes)")
except Exception as e:
    print(f"Dataset files error: {e}")
