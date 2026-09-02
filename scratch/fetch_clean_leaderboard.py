import json
import sys
from kaggle.api.kaggle_api_extended import KaggleApi

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

api = KaggleApi()
api.authenticate()

lb = api.competition_leaderboard_view("kaggriculture")
print(f"Total LB entries fetched: {len(lb)}")

lb_rows = []
for i, e in enumerate(lb):
    row = {
        "rank": i + 1,
        "teamId": getattr(e, 'teamId', getattr(e, 'team_id', None)),
        "teamName": str(getattr(e, 'teamName', getattr(e, 'team_name', ''))),
        "score": float(getattr(e, 'score', 0.0)),
        "submissionDate": str(getattr(e, 'submissionDate', getattr(e, 'submission_date', '')))
    }
    lb_rows.append(row)

with open("scratch/leaderboard_full.json", "w", encoding="utf-8") as f:
    json.dump(lb_rows, f, indent=2)

print("\nTop 20 Leaderboard:")
for r in lb_rows[:20]:
    print(f"#{r['rank']:2d} | Score: {r['score']:7.1f} | Team: {r['teamName']:<25} | Date: {r['submissionDate']}")
