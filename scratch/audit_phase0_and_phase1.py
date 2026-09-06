import hashlib
import os
import tarfile
import json
import glob

def get_sha256(filepath):
    if not os.path.exists(filepath):
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def inspect_tarball(tar_path):
    if not os.path.exists(tar_path):
        return None
    tar_hash = get_sha256(tar_path)
    members = []
    member_hashes = {}
    with tarfile.open(tar_path, "r:*") as tar:
        for m in tar.getmembers():
            members.append(m.name)
            if m.isfile():
                f = tar.extractfile(m)
                if f:
                    content = f.read()
                    member_hashes[m.name] = hashlib.sha256(content).hexdigest()
    return {
        "tar_path": tar_path,
        "tar_sha256": tar_hash,
        "members": members,
        "member_hashes": member_hashes
    }

files_to_hash = [
    "candidates/slot1_titan_control.py",
    "candidates/slot2_aethel_refined_v2.py",
    "agents/candidate_a_aethel_v1.py",
    "agents/candidate_b_aethel_mc.py",
    "agents/candidate_c_aethel_t712.py",
    "agents/candidate_d_aethel_refined.py",
    "agents/aethel_factorial_base.py",
    "agents/golden_v1.py",
    "main.py",
    "bot.py",
    "replays/raw/reference_agents/closer_cleo.py",
    "scratch/arch_base.py",
    "submission.tar.gz",
    "submission_slot2_aethel_refined_v2.tar.gz"
]

print("="*80)
print("PHASE 0 & PHASE 1: REPOSITORY & LIVE PORTFOLIO HASH VERIFICATION")
print("="*80)

for f in files_to_hash:
    sha = get_sha256(f)
    print(f"{f:50s} : {sha}")

print("\n--- Tarball Payload Inspection ---")
for t in ["submission.tar.gz", "submission_slot2_aethel_refined_v2.tar.gz"]:
    res = inspect_tarball(t)
    if res:
        print(f"Tarball: {res['tar_path']}")
        print(f"  Tarball SHA256: {res['tar_sha256']}")
        print(f"  Members: {res['members']}")
        for m, h in res['member_hashes'].items():
            print(f"    Member '{m}' SHA256: {h}")

target_v1_hash = "8addafc2de814b4ea76c63a30b166420a0ff8e8a86d40c6ae2651ef5c043d1f9"
target_v1_cand_a_hash = "c1945f24f34ca9d5124e8200df14af019f6cb4cdec3ca402d9a3a88f6b04e36f"
target_v2_hash = "79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d"

print("\n--- Search for Bit-Identical Files in Repository ---")
for root, dirs, files in os.walk("."):
    if ".git" in root or "__pycache__" in root:
        continue
    for file in files:
        if file.endswith(".py") or file.endswith(".gz") or file.endswith(".tar"):
            p = os.path.join(root, file)
            sha = get_sha256(p)
            if sha == target_v1_hash:
                print(f"MATCH V1 (Closer Cleo Raw) ({target_v1_hash[:12]}...): {p}")
            if sha == target_v1_cand_a_hash:
                print(f"MATCH V1 (Candidate A)     ({target_v1_cand_a_hash[:12]}...): {p}")
            if sha == target_v2_hash:
                print(f"MATCH V2 SOURCE            ({target_v2_hash[:12]}...): {p}")
