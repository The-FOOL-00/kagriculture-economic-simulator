# SPDX-License-Identifier: MIT
"""
KAGGRICULTURE LIVE SUBMISSION SCRIPT
Submits Aethel-Refined V2 to Live Slot 2 (Replacing Titan Apex V4)
"""

import os
import sys
import json
import time
import hashlib
import tarfile
import tempfile
import shutil
import requests
import urllib3
from kaggle_environments import make

urllib3.disable_warnings()

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def execute_submission():
    print("================================================================================")
    print("STARTING KAGGRICULTURE SUBMISSION EXECUTION")
    print("================================================================================")
    
    src_path = 'agents/candidate_d_aethel_refined.py'
    staged_path = 'candidates/slot2_aethel_refined_v2.py'
    tar_path = 'submission_slot2_aethel_refined_v2.tar.gz'
    
    expected_src_sha = '79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d'
    expected_tar_sha = 'ac16af822ea972852ba923dbec45503597b8518ecbe62a8744040d352f0c7c92'
    
    print("\n[STEP 1] VERIFYING CRYPTOGRAPHIC HASHES...")
    src_sha = sha256_file(src_path)
    staged_sha = sha256_file(staged_path)
    tar_sha = sha256_file(tar_path)
    
    print(f"  Source SHA-256 : {src_sha}")
    print(f"  Staged SHA-256 : {staged_sha}")
    print(f"  Tarball SHA-256: {tar_sha}")
    
    assert src_sha == expected_src_sha, f"Source SHA mismatch: {src_sha} != {expected_src_sha}"
    assert staged_sha == expected_src_sha, f"Staged SHA mismatch: {staged_sha} != {expected_src_sha}"
    assert tar_sha == expected_tar_sha, f"Tar SHA mismatch: {tar_sha} != {expected_tar_sha}"
    
    print("\n[STEP 2] VERIFYING TARBALL PAYLOAD & ISOLATED SMOKE TEST...")
    temp_dir = tempfile.mkdtemp(prefix="kagg_submit_smoke_")
    with tarfile.open(tar_path, "r:gz") as tar:
        members = tar.getmembers()
        assert len(members) == 1 and members[0].name == 'main.py', f"Unexpected members: {[m.name for m in members]}"
        tar.extractall(path=temp_dir)
        
    extracted_main = os.path.join(temp_dir, 'main.py')
    extracted_sha = sha256_file(extracted_main)
    assert extracted_sha == expected_src_sha, f"Extracted main.py SHA mismatch: {extracted_sha} != {expected_src_sha}"
    
    env = make("kaggriculture", configuration={"seed": 42})
    env.run([extracted_main, "replays/raw/reference_agents/closer_cleo.py"])
    status = env.steps[-1][0]["status"]
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    assert status == "DONE" and len(env.steps) >= 720, f"Smoke test failed: status={status}, steps={len(env.steps)}"
    print(f"  Isolated Smoke Test Passed: Status={status}, Turns={len(env.steps)}, Cand={r0}, Opp={r1} (Margin: {r0-r1:+})")
    shutil.rmtree(temp_dir)
    
    print("\n[STEP 3] AUTHENTICATING WITH KAGGLE API...")
    access_token_file = os.path.expanduser('~/.kaggle/access_token')
    with open(access_token_file) as f:
        token = f.read().strip()
        
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    file_size = os.path.getsize(tar_path)
    file_mtime = int(os.path.getmtime(tar_path))
    
    start_payload = {
        'competitionName': 'kaggriculture',
        'fileName': 'submission_slot2_aethel_refined_v2.tar.gz',
        'contentLength': file_size,
        'lastModifiedEpochSeconds': file_mtime
    }
    
    start_url = 'https://www.kaggle.com/api/v1/competitions.CompetitionApiService/StartSubmissionUpload'
    r_start = requests.post(start_url, headers=headers, json=start_payload, verify=False, timeout=15)
    
    if r_start.status_code != 200:
        start_url_alt = 'https://api.kaggle.com/v1/competitions.CompetitionApiService/StartSubmissionUpload'
        r_start = requests.post(start_url_alt, headers=headers, json=start_payload, verify=False, timeout=15)
        
    assert r_start.status_code == 200, f"StartSubmissionUpload failed: {r_start.status_code} {r_start.text}"
    start_data = r_start.json()
    upload_token = start_data['token']
    create_url = start_data['createUrl']
    print(f"  Upload Token Handshake Successful.")
    
    print("\n[STEP 4] UPLOADING TARBALL BLOB...")
    with open(tar_path, 'rb') as fp:
        tar_bytes = fp.read()
        
    upload_headers = {
        'Content-Type': 'application/octet-stream',
        'Content-Length': str(len(tar_bytes))
    }
    r_upload = requests.put(create_url, data=tar_bytes, headers=upload_headers, verify=False, timeout=60)
    print(f"  Blob Upload HTTP Status: {r_upload.status_code}")
    assert r_upload.status_code in (200, 201), f"Blob upload failed: {r_upload.status_code} {r_upload.text}"
    
    print("\n[STEP 5] CREATING COMPETITION SUBMISSION (SLOT 2)...")
    sub_desc = "Aethel-Refined V2: Validated Challenger (Impact-Sorted MC + Step-712 Dynamic Harvester)"
    create_payload = {
        'competitionName': 'kaggriculture',
        'blobFileTokens': upload_token,
        'submissionDescription': sub_desc
    }
    
    create_url_api = 'https://www.kaggle.com/api/v1/competitions.CompetitionApiService/CreateSubmission'
    r_create = requests.post(create_url_api, headers=headers, json=create_payload, verify=False, timeout=20)
    if r_create.status_code != 200:
        create_url_api_alt = 'https://api.kaggle.com/v1/competitions.CompetitionApiService/CreateSubmission'
        r_create = requests.post(create_url_api_alt, headers=headers, json=create_payload, verify=False, timeout=20)
        
    print(f"  CreateSubmission HTTP Status: {r_create.status_code}")
    assert r_create.status_code == 200, f"CreateSubmission failed: {r_create.status_code} {r_create.text}"
    create_data = r_create.json()
    submission_id = create_data.get('ref') or create_data.get('id')
    submission_msg = create_data.get('message', 'Submission created')
    print(f"  Submission ID: {submission_id}")
    print(f"  Message: {submission_msg}")
    
    print("\n[STEP 6] VERIFYING ACTIVE SUBMISSION ON LEADERBOARD...")
    time.sleep(3)
    list_url = 'https://www.kaggle.com/api/v1/competitions.CompetitionApiService/ListSubmissions'
    r_list = requests.post(list_url, headers=headers, json={'competitionName': 'kaggriculture'}, verify=False, timeout=15)
    if r_list.status_code != 200:
        list_url_alt = 'https://api.kaggle.com/v1/competitions.CompetitionApiService/ListSubmissions'
        r_list = requests.post(list_url_alt, headers=headers, json={'competitionName': 'kaggriculture'}, verify=False, timeout=15)
        
    if r_list.status_code == 200:
        subs = r_list.json().get('submissions', [])
        print(f"  Total Submissions: {len(subs)}")
        latest = subs[0] if subs else {}
        print(f"  Latest Submission on Kaggle:")
        print(f"    Ref       : {latest.get('ref')}")
        print(f"    Date      : {latest.get('date')}")
        print(f"    Status    : {latest.get('status')}")
        print(f"    Filename  : {latest.get('fileName')}")
        print(f"    Desc      : {latest.get('description')}")
        
    return {
        "status": "SUCCESS",
        "submission_id": submission_id,
        "filename": "submission_slot2_aethel_refined_v2.tar.gz",
        "tar_sha256": tar_sha,
        "src_sha256": src_sha,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "description": sub_desc
    }

if __name__ == '__main__':
    res = execute_submission()
    print("\n" + json.dumps(res, indent=2))
