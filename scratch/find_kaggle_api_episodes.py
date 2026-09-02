import requests
import json
import os

sub_id = 55893176
team_id = 16657198

# Try with kaggle api auth and without auth
kaggle_json_path = os.path.expanduser("~/.kaggle/kaggle.json")
auth = None
if os.path.exists(kaggle_json_path):
    with open(kaggle_json_path, "r") as f:
        kdata = json.load(f)
        auth = (kdata["username"], kdata["key"])

# Let's test standard Kaggle internal API endpoints:
url_candidates = [
    # EpisodeService
    ("POST", "https://www.kaggle.com/api/i/simulations.EpisodeService/ListEpisodes", {"submissionId": sub_id}),
    ("POST", "https://www.kaggle.com/api/i/simulations.EpisodeService/ListEpisodes", {"submissionIds": [sub_id]}),
    ("POST", "https://www.kaggle.com/api/i/simulations.EpisodeService/ListEpisodes", {"teamId": team_id}),
    ("POST", "https://www.kaggle.com/api/i/simulations.EpisodeService/ListEpisodes", {"teamIds": [team_id]}),
    ("POST", "https://www.kaggle.com/api/i/simulations.EpisodeService/ListEpisodes", {"competitionId": 82255}), # Let's find competition ID
    # TournamentService
    ("POST", "https://www.kaggle.com/api/i/tournaments.TournamentService/ListEpisodes", {"submissionId": sub_id}),
    ("POST", "https://www.kaggle.com/api/i/tournaments.TournamentService/ListEpisodes", {"teamId": team_id}),
    ("POST", "https://www.kaggle.com/api/i/tournaments.TournamentService/GetSubmissionDetails", {"submissionId": sub_id}),
    ("POST", "https://www.kaggle.com/api/i/tournaments.TournamentService/ListSubmissions", {"competitionId": 82255}),
    # EpisodesService on www.kaggle.com/requests
    ("POST", "https://www.kaggle.com/requests/EpisodeService/ListEpisodes", {"submissionId": sub_id}),
    ("POST", "https://www.kaggle.com/requests/EpisodeService/ListEpisodes", {"submissionIds": [sub_id]}),
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

for method, url, payload in url_candidates:
    try:
        if method == "POST":
            r = requests.post(url, json=payload, headers=headers, auth=auth, timeout=10)
        else:
            r = requests.get(url, headers=headers, auth=auth, timeout=10)
        print(f"[{r.status_code}] {url} -> {r.text[:200]}")
    except Exception as e:
        print(f"ERR {url}: {e}")
