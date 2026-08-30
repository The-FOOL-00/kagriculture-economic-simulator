import os
import sys
import glob
import hashlib
import datetime
import tarfile

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def get_sha256(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

print("="*90)
print("PART 1 — FREEZE REPOSITORY STATE & GENERATE MANIFEST")
print("="*90)

files = sorted(glob.glob(os.path.join(project_root, "**/*"), recursive=True))
manifest_entries = []

for f in files:
    if not os.path.isfile(f):
        continue
    rel = os.path.relpath(f, project_root)
    if rel.startswith(".git") or "__pycache__" in rel or rel.startswith("scratch"):
        continue
    sz = os.path.getsize(f)
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y-%m-%d %H:%M:%S')
    h = get_sha256(f)
    
    # Categorize role
    if rel.startswith("candidates/"):
        role = "Candidate Staging"
    elif rel.startswith("ablation_agents/"):
        role = "Ablation Agent Variant"
    elif rel.startswith("agents/synthetic/"):
        role = "Synthetic Opponent Archetype"
    elif rel.startswith("agents/"):
        role = "Agent Strategy"
    elif rel.startswith("engine/"):
        role = "Modular Engine Subsystem"
    elif rel.startswith("benchmarks/"):
        role = "Benchmark Configuration"
    elif rel.endswith(".md"):
        role = "Documentation / Report"
    elif rel.endswith(".json"):
        role = "Replay / Forensic Log"
    elif rel == "submission.tar.gz":
        role = "Kaggle Package Tarball"
    elif rel == "main.py":
        role = "Compiled Production Entrypoint"
    elif rel == "compiler.py":
        role = "Production Compiler"
    elif rel.startswith("run_") or rel.endswith("_suite.py") or rel.endswith("_check.py") or rel in ["arena.py", "benchmark_harness.py", "diff_lab.py", "debug_forensic_divergence.py", "inspect_scratch_progression.py", "test_lab_reproducibility.py"]:
        role = "Test / Benchmark Runner"
    else:
        role = "Core Module / Tool"
        
    manifest_entries.append((rel, h, sz, mtime, role))

print(f"Total files cataloged: {len(manifest_entries)}")
print(f"{'File':52} | {'SHA256 (first 16)':16} | {'Size':8} | {'Modified':19} | {'Role'}")
print("-" * 120)
for rel, h, sz, mt, role in manifest_entries:
    print(f"{rel:52} | {h[:16]:16} | {sz:8d} | {mt:19} | {role}")

print("\n" + "="*90)
print("PART 2 — VERIFY THE FIVE CANDIDATES")
print("="*90)

candidates = [
    ("slot1_titan_control.py", "candidates/slot1_titan_control.py"),
    ("slot2_hybrid_6c3s_10m.py", "candidates/slot2_hybrid_6c3s_10m.py"),
    ("slot3_hybrid_dynamic.py", "candidates/slot3_hybrid_dynamic.py"),
    ("slot4_hybrid_lookahead.py", "candidates/slot4_hybrid_lookahead.py"),
    ("slot5_hybrid_8c4s.py", "candidates/slot5_hybrid_8c4s.py"),
]

for name, path in candidates:
    full_p = os.path.join(project_root, path)
    if os.path.exists(full_p):
        h = get_sha256(full_p)
        sz = os.path.getsize(full_p)
        with open(full_p, "r") as fp:
            lines = fp.readlines()
        print(f"Candidate: {name:28} | SHA256: {h} | Size: {sz:5d} B | Lines: {len(lines):4d}")
    else:
        print(f"Candidate: {name:28} | MISSING!")

print("\nLegacy Candidate Files in candidates/ directory:")
legacy = [
    "candidates/slot2_loss_fix_challenger.py",
    "candidates/slot3_opponent_adaptive.py",
    "candidates/slot4_market_planner.py",
    "candidates/slot5_local_champion.py"
]
for p in legacy:
    full_p = os.path.join(project_root, p)
    if os.path.exists(full_p):
        h = get_sha256(full_p)
        sz = os.path.getsize(full_p)
        print(f"Legacy: {p:42} | SHA256: {h} | Size: {sz:5d} B")

print("\n" + "="*90)
print("PART 3 — VERIFY PRODUCTION BUILD & COMPILER PIPELINE")
print("="*90)

main_p = os.path.join(project_root, "main.py")
main_h = get_sha256(main_p)
print(f"Root main.py SHA256: {main_h} (Size: {os.path.getsize(main_p)} B)")

tar_p = os.path.join(project_root, "submission.tar.gz")
if os.path.exists(tar_p):
    with tarfile.open(tar_p, "r:gz") as tar:
        for m in tar.getmembers():
            extracted = tar.extractfile(m).read()
            tar_main_h = hashlib.sha256(extracted).hexdigest()
            print(f"submission.tar.gz member: '{m.name}' | Size: {m.size} B | SHA256: {tar_main_h}")
            if tar_main_h == get_sha256(os.path.join(project_root, "agents/hybrid_6c3s_10m.py")):
                print("  -> MATCHES agents/hybrid_6c3s_10m.py exactly!")
            if tar_main_h == main_h:
                print("  -> MATCHES root main.py!")
            else:
                print("  -> DOES NOT MATCH root main.py!")

# Check compiler.py output
import subprocess
print("\nTesting compiler.py execution...")
res = subprocess.run(["python", "compiler.py"], cwd=project_root, capture_output=True, text=True)
print("compiler.py stdout:", res.stdout.strip())
new_main_h = get_sha256(main_p)
print(f"Compiled main.py SHA256: {new_main_h}")
if new_main_h == main_h:
    print("  -> compiler.py generates identical legacy Titan control main.py")
else:
    print("  -> compiler.py changed main.py!")
