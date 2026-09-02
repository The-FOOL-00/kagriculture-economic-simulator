import requests
import json
import os
import urllib3

urllib3.disable_warnings()

access_token_file = os.path.expanduser('~/.kaggle/access_token')
with open(access_token_file) as f:
    token = f.read().strip()

headers = {'Authorization': f'Bearer {token}'}

url = 'https://www.kaggle.com/api/v1/competitions/submissions/list/147734'
r = requests.get(url, headers=headers, verify=False, timeout=10)
if r.status_code != 200:
    url = 'https://www.kaggle.com/api/v1/competitions/kaggriculture/submissions/list'
    r = requests.get(url, headers=headers, verify=False, timeout=10)

print(f"Status Code: {r.status_code}")
if r.status_code == 200:
    subs = r.json()
    print(f"Total submissions on Kaggle: {len(subs)}")
    for s in subs[:15]:
        sid = s.get('id')
        dt = s.get('date')
        st = s.get('status')
        desc = s.get('description')
        fn = s.get('fileName')
        score = s.get('publicScore')
        print(f"  ID: {sid:10s} | Date: {str(dt):20s} | Status: {str(st):12s} | Score: {str(score):8s} | Desc: {str(desc):30s} | File: {fn}")
else:
    print("Response:", r.text[:300])
