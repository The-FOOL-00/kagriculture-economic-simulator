import hashlib

def get_sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

print("Slot 1 (Aethel-Prime V1):", get_sha256("agents/candidate_a_aethel_v1.py"))
print("Slot 2 (Aethel-Refined V2):", get_sha256("candidates/slot2_aethel_refined_v2.py"))
