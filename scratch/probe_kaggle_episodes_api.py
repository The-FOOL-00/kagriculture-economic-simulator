import requests
import json
import urllib.request
import os

sub_id = 55893176
team_id = 16657198

# Check kaggle api credentials from ~/.kaggle/kaggle.json
kaggle_json_path = os.path.expanduser("~/.kaggle/kaggle.json")
auth = None
if os.path.exists(kaggle_json_path):
    with open(kaggle_json_path, "r") as f:
        kdata = json.load(f)
        auth = (kdata["username"], kdata["key"])
        print(f"Kaggle username: {kdata['username']}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Content-Type": "application/json"
}

endpoints = [
    f"https://www.kaggle.com/api/i/tournaments.TournamentService/ListEpisodes",
    f"https://www.kaggle.com/api/i/episodes.EpisodeService/ListEpisodes",
]

payloads = [
    {"submissionId": sub_id},
    {"submissionId": str(sub_id)},
    {"teamId": team_id},
    {"teamId": str(team_id)},
    {"submissionIds": [sub_id]},
    {"teamIds": [team_id]}
]

for ep in endpoints:
    for pl in payloads:
        try:
            r = requests.post(ep, json=pl, headers=headers, auth=auth, timeout=10)
            print(f"POST {ep} with {pl} -> Status: {r.status_code}, Length: {len(r.text)}")
            if r.status_code == 200 and len(r.text) > 50:
                data = r.json()
                print("Keys:", data.keys())
                print("Preview:", str(data)[:300])
        except Exception as e:
            print(f"Error {ep}: {e}")

# Also try GET requests
get_urls = [
    f"https://www.kaggle.com/api/i/tournaments.TournamentService/ListEpisodes?submissionId={sub_id}",
    f"https://www.kaggle.com/api/i/tournaments.TournamentService/ListEpisodes?teamId={team_id}",
    f"https://www.kaggle.com/api/i/episodes.EpisodeService/ListEpisodes?submissionId={sub_id}",
    f"https://www.kaggle.com/api/i/episodes.EpisodeService/ListEpisodes?teamId={team_id}",
    f"https://www.kaggle.com/api/i/tournaments.TournamentService/GetSubmissionDetails?submissionId={sub_id}",
]

for url in get_urls:
    try:
        r = requests.get(url, headers=headers, auth=auth, timeout=10)
        print(f"GET {url} -> Status: {r.status_code}, Length: {len(r.text)}")
        if r.status_code == 200 and len(r.text) > 50:
            data = r.json()
            print("Keys:", data.keys())
            print("Preview:", str(data)[:300])
    except Exception as e:
        print(f"Error {url}: {e}")
