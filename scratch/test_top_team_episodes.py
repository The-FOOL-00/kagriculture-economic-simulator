import os
import sys
import json
import kaggle

sys.stdout.reconfigure(encoding='utf-8')
kaggle.api.authenticate()

# Check top teams from leaderboard
with open("scratch/top50_leaderboard.json", "r", encoding="utf-8") as f:
    top50 = json.load(f)

print("Testing fetching episodes for top teams...")
with kaggle.api.build_kaggle_client() as k_client:
    # Test list_team_public_submissions
    for team in top50[:5]:
        t_id = team['TeamId']
        t_name = team['TeamName']
        print(f"\nChecking team: {t_name} (ID: {t_id})...")
        try:
            from kagglesdk.competitions.types.competition_api_service import ApiListTeamPublicSubmissionsRequest
            req = ApiListTeamPublicSubmissionsRequest()
            req.team_id = t_id
            resp = k_client.competitions.competition_api_client.list_team_public_submissions(req)
            print(f"Team {t_name} public submissions: {resp}")
        except Exception as e:
            print(f"Error list_team_public_submissions for {t_name}: {e}")

