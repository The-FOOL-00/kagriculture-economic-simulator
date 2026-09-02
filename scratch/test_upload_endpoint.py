import os
import json
import requests
import urllib3

urllib3.disable_warnings()

access_token_file = os.path.expanduser('~/.kaggle/access_token')
with open(access_token_file) as f:
    token = f.read().strip()

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

tar_path = 'submission_slot2_aethel_refined_v2.tar.gz'
size = os.path.getsize(tar_path)
mtime = int(os.path.getmtime(tar_path))

req_payload = {
    'competitionName': 'kaggriculture',
    'fileName': 'submission_slot2_aethel_refined_v2.tar.gz',
    'contentLength': size,
    'lastModifiedEpochSeconds': mtime
}

url = 'https://www.kaggle.com/api/v1/competitions.CompetitionApiService/StartSubmissionUpload'
r = requests.post(url, headers=headers, json=req_payload, verify=False, timeout=15)

print(f"StartSubmissionUpload Status: {r.status_code}")
print("Response:", r.text[:300])
