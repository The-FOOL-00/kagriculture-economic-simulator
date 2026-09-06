import zipfile
import os
import pandas as pd
import json

def main():
    csv_file = "scratch/leaderboard_csv/kaggriculture-publicleaderboard-2026-09-06T12_46_59.csv"
    if not os.path.exists(csv_file):
        zip_path = "scratch/kaggriculture.zip"
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall("scratch/leaderboard_csv")
            
    df = pd.read_csv(csv_file)
    total_teams = len(df)
    
    # Let's inspect top 50
    top50 = []
    for i in range(min(50, len(df))):
        row = df.iloc[i]
        top50.append({
            "Rank": int(row['Rank']),
            "TeamId": int(row['TeamId']),
            "TeamName": str(row['TeamName']),
            "Score": float(row['Score']),
            "SubmissionCount": int(row['SubmissionCount']),
            "LastSubmissionDate": str(row['LastSubmissionDate']),
            "TeamMemberUserNames": str(row['TeamMemberUserNames'])
        })
        
    with open("scratch/top50_leaderboard_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(top50, f, indent=2, ensure_ascii=False)
        
    print(f"Total active teams: {total_teams}")
    print(f"Top 1: Rank {top50[0]['Rank']}, TeamId {top50[0]['TeamId']}, Score: {top50[0]['Score']}")
    print(f"Top 5: Rank {top50[4]['Rank']}, TeamId {top50[4]['TeamId']}, Score: {top50[4]['Score']}")
    print(f"Top 10: Rank {top50[9]['Rank']}, TeamId {top50[9]['TeamId']}, Score: {top50[9]['Score']}")
    print(f"Top 20: Rank {top50[19]['Rank']}, TeamId {top50[19]['TeamId']}, Score: {top50[19]['Score']}")
    print(f"Top 50: Rank {top50[49]['Rank']}, TeamId {top50[49]['TeamId']}, Score: {top50[49]['Score']}")
    
    # Search for user team / username
    user_rows = df[df['TeamMemberUserNames'].str.contains('sundareswaran|sundar|aethel', case=False, na=False)]
    print("\nUser rows found by username search:")
    for idx, r in user_rows.iterrows():
        print(f"Rank {r['Rank']}: Team '{r['TeamName']}' (TeamId {r['TeamId']}), Score: {r['Score']}, Subs: {r['SubmissionCount']}")

if __name__ == "__main__":
    main()
