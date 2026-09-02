import requests
import json
import os

kaggle_json_path = os.path.expanduser("~/.kaggle/kaggle.json")
with open(kaggle_json_path, "r") as f:
    kdata = json.load(f)
    auth = (kdata["username"], kdata["key"])

sub_id = 55893176
team_id = 16657198

v1_endpoints = [
    f"https://www.kaggle.com/api/v1/competitions/submissions/list/{sub_id}",
    f"https://www.kaggle.com/api/v1/competitions/submissions/kaggriculture",
    f"https://www.kaggle.com/api/v1/competitions/kaggriculture/leaderboard",
    f"https://www.kaggle.com/api/v1/episodes/{sub_id}",
    f"https://www.kaggle.com/api/v1/episodes/kaggriculture",
]

for url in v1_endpoints:
    try:
        r = requests.get(url, auth=auth, timeout=10)
        print(f"[{r.status_code}] {url} -> Content-Type: {r.headers.get('Content-Type')}, Length: {len(r.text)}")
        if r.status_code == 200 and "json" in r.headers.get("Content-Type", "").lower():
            try:
                data = r.json()
                print("JSON type:", type(data))
                if isinstance(data, list):
                    print("List len:", len(data))
                    if data:
                        print("Sample item:", data[0])
                elif isinstance(data, dict):
                    print("Dict keys:", data.keys())
            except:
                print("Text preview:", r.text[:200])
    except Exception as e:
        print(f"ERR {url}: {e}")
