import os
import hashlib

def get_file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

out_lines = []
out_lines.append("# FORENSIC SHA256 ARTIFACT HASH LEDGER")
out_lines.append("# Generated during Adversarial Verification Audit\n")

out_lines.append("## 1. Protected Baseline & Candidate Agents")
agents = [
    ("V66 Public Submission", r"external_repos\kaggriculture-v66-agent\main.py"),
    ("V66 Meta Closed Loop", r"external_repos\kaggriculture-v66-agent\candidate_v66_meta_closed_loop.py"),
    ("V54 h3q4 Candidate", r"external_repos\lixingtao123-Kaggriculture\variant_v54_h3q4\main.py"),
    ("V2 Protected Control", r"agents\slot4_control_frozen_v2.py"),
    ("Titan Protected Control", r"candidates\slot1_titan_control.py"),
    ("Okami Solution Agent", r"external_repos\okami001-Kaggriculture\main.py"),
]
for name, p in agents:
    if os.path.exists(p):
        h = get_file_hash(p)
        out_lines.append(f"{h}  {name:30s}  ({p})")

out_lines.append("\n## 2. Extracted Lineage Source Artifacts")
extracted = [
    r"forensic_verification\extracted_sources\layer_0.py",
    r"forensic_verification\extracted_sources\layer_1.py",
    r"forensic_verification\extracted_sources\layer_2.py",
]
for p in extracted:
    if os.path.exists(p):
        h = get_file_hash(p)
        out_lines.append(f"{h}  {os.path.basename(p):30s}  ({p})")

out_lines.append("\n## 3. Extracted V49 Lineage Modules")
v49_dir = r"forensic_verification\extracted_sources\v49_modules"
if os.path.exists(v49_dir):
    for f in sorted(os.listdir(v49_dir)):
        fp = os.path.join(v49_dir, f)
        h = get_file_hash(fp)
        out_lines.append(f"{h}  {f:30s}  ({fp})")

out_lines.append("\n## 4. Benchmark Raw Data Artifacts")
bench_dir = r"forensic_verification\benchmark_raw"
if os.path.exists(bench_dir):
    for f in sorted(os.listdir(bench_dir)):
        fp = os.path.join(bench_dir, f)
        h = get_file_hash(fp)
        out_lines.append(f"{h}  {f:30s}  ({fp})")

out_text = "\n".join(out_lines) + "\n"
with open(r"forensic_verification\hashes.txt", "w", encoding="utf-8") as f:
    f.write(out_text)

print("Generated forensic_verification/hashes.txt")
