import json

with open("scratch/top50_leaderboard_snapshot.json", "r", encoding="utf-8") as f:
    top50 = json.load(f)

print(f"{'Rank':<5} | {'Team ID':<10} | {'Score/Elo':<10} | {'Team Name':<30} | {'Members'}")
print("-" * 85)
for t in top50[:20]:
    tname = t['TeamName'].encode('ascii', 'replace').decode('ascii')[:30]
    members = t['TeamMemberUserNames'].encode('ascii', 'replace').decode('ascii')
    print(f"{t['Rank']:<5} | {t['TeamId']:<10} | {t['Score']:<10.1f} | {tname:<30} | {members}")
