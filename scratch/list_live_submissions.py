import requests
import os
import json
import time
import urllib3

urllib3.disable_warnings()

access_token_file = os.path.expanduser('~/.kaggle/access_token')
with open(access_token_file) as f:
    token = f.read().strip()

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

urls = [
    'https://www.kaggle.com/api/v1/competitions.CompetitionApiService/ListSubmissions',
    'https://api.kaggle.com/v1/competitions.CompetitionApiService/ListSubmissions'
]

data = None
for url in urls:
    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, json={'competitionName': 'kaggriculture'}, verify=False, timeout=15)
            if r.status_code == 200:
                data = r.json()
                break
        except Exception as e:
            time.sleep(1)
    if data is not None:
        break

if data is not None:
    subs = data.get('submissions', [])
    print(f"Total submissions on Kaggle: {len(subs)}")
    for s in subs:
        ref = s.get('ref')
        dt = s.get('date')
        status = s.get('status')
        score = s.get('publicScore')
        fn = s.get('fileName')
        desc = s.get('description')
        print(f"Ref: {ref} | Date: {dt} | Status: {status} | Score: {score} | File: {fn} | Desc: {desc}")
else:
    print("Could not fetch submissions from Kaggle API.")
