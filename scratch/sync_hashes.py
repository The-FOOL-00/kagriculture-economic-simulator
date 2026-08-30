import os
import hashlib

project_root = r"c:\Users\Sundareswaran\Kagriculture"
frozen_file = os.path.join(project_root, "agents", "apex_v2_frozen.py")
cand_file = os.path.join(project_root, "candidates", "slot5_apex_synthesis_v2.py")
main_file = os.path.join(project_root, "main.py")

with open(frozen_file, "r", encoding="utf-8") as f:
    exact_code = f.read()

with open(cand_file, "w", encoding="utf-8") as f:
    f.write(exact_code)

with open(main_file, "w", encoding="utf-8") as f:
    f.write(exact_code)

def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

h_f = sha256_file(frozen_file)
h_c = sha256_file(cand_file)
h_m = sha256_file(main_file)

print(f"Frozen Hash:    {h_f}")
print(f"Candidate Hash: {h_c}")
print(f"Main Hash:      {h_m}")
print(f"Exact Byte Match: {h_f == h_c == h_m}")
