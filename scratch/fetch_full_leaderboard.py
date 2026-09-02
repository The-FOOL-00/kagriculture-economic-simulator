import os
import sys
import json
import kaggle
from datetime import datetime, timezone
from kagglesdk.competitions.types.competition_api_service import ApiGetLeaderboardRequest

sys.stdout.reconfigure(encoding='utf-8')
kaggle.api.authenticate()

print("Fetching full leaderboard via kagglesdk...")

all_subs = []
page_token = None
page_count = 0

with kaggle.api.build_kaggle_client() as k_client:
    while True:
        req = ApiGetLeaderboardRequest()
        req.competition_name = 'kaggriculture'
        req.page_size = 100
        if page_token:
            req.page_token = page_token
            
        resp = k_client.competitions.competition_api_client.get_leaderboard(req)
        page_count += 1
        subs_on_page = resp.submissions or []
        print(f"Page {page_count}: received {len(subs_on_page)} entries")
        
        for sub in subs_on_page:
            all_subs.append({
                'teamId': getattr(sub, 'team_id', getattr(sub, 'teamId', None)),
                'teamName': getattr(sub, 'team_name', getattr(sub, 'teamName', None)),
                'submissionDate': str(getattr(sub, 'submission_date', getattr(sub, 'submissionDate', ''))),
                'score': float(getattr(sub, 'score', 0.0)) if getattr(sub, 'score', None) is not None else 0.0
            })
            
        page_token = resp.next_page_token
        if not page_token or len(subs_on_page) == 0:
            break

print(f"\nTotal leaderboard entries: {len(all_subs)}")

# Sort descending by score
all_subs.sort(key=lambda x: x['score'], reverse=True)

with open("scratch/full_leaderboard.json", "w", encoding="utf-8") as f:
    json.dump(all_subs, f, indent=2, ensure_ascii=False)

print("\n" + "="*80)
print(f"KAGGRICULTURE LEADERBOARD SNAPSHOT (Total: {len(all_subs)} teams)")
print("="*80)
print(f"{'Rank':<5} | {'Score':<8} | {'Team Name':<35} | {'Team ID':<10} | {'Submission Date'}")
print("-" * 80)
for i, s in enumerate(all_subs):
    if i < 50 or (i < 100 and i % 10 == 0):
        print(f"#{i+1:<4} | {s['score']:<8.1f} | {s['teamName'][:34]:<35} | {s['teamId']:<10} | {s['submissionDate'][:19]}")

# Find our team rank
print("\n" + "="*80)
print("OUR TEAM RANKINGS:")
for i, s in enumerate(all_subs):
    if any(k in str(s['teamName']).lower() for k in ['thefool', 'eldritch', 'sundareswaran', 'aethel']):
        print(f"Rank #{i+1} | Score: {s['score']:.1f} | Team Name: {s['teamName']} | Team ID: {s['teamId']}")
