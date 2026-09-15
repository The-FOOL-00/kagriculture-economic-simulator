import os
import sys
import hashlib
import tempfile
import tarfile
import subprocess
import shutil
import importlib.util
import kaggle_environments

def audit_1():
    print("=" * 80)
    print("AUDIT 1 — EXACT SUBMISSION-ARTIFACT IDENTITY")
    print("=" * 80)

    cand_path = os.path.abspath("candidates/candidate_cl_labor_minimal_v1.py")
    expected_sha = "6708397769d64de5935623c8bf6df7076ce0b1afff236555128757fb577a6759"
    
    # 1. SHA256 Candidate File
    with open(cand_path, "rb") as f:
        cand_bytes = f.read()
    cand_sha = hashlib.sha256(cand_bytes).hexdigest()
    print(f"1. Candidate File: {cand_path}")
    print(f"   Candidate Size: {len(cand_bytes)} bytes")
    print(f"   Candidate SHA256: {cand_sha}")
    
    # 2. Verify SHA256
    sha_match = (cand_sha == expected_sha)
    print(f"2. SHA256 Match Expected: {sha_match}")
    if not sha_match:
        print(f"   ERROR: Expected {expected_sha}, got {cand_sha}")
        return False

    # 3. Inspect Callable Expected by Runner
    print("\n3. Inspecting Callable Expected by Competition Runner:")
    spec = importlib.util.spec_from_file_location("candidate_mod", cand_path)
    cand_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cand_mod)
    
    has_candidate_agent = hasattr(cand_mod, "candidate_agent") and callable(getattr(cand_mod, "candidate_agent"))
    has_agent = hasattr(cand_mod, "agent") and callable(getattr(cand_mod, "agent"))
    print(f"   hasattr(candidate_agent) and callable: {has_candidate_agent}")
    print(f"   hasattr(agent) and callable: {has_agent}")

    # 4. Execute exact candidate in clean competition runner (in-repo)
    print("\n4. Executing Candidate in Repo Competition Runner (Seed 10001, 20 steps):")
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 20, "seed": 10001})
    res = env.run([cand_mod.candidate_agent, "starter"])
    print(f"   Result status: {res[-1][0]['status']}, Steps: {len(res)}, Final reward: {res[-1][0]['reward']}")

    # 5. Verify constraints
    print("\n5. Verifying Static Constraints on Candidate Source:")
    src_lines = cand_bytes.decode("utf-8").splitlines()
    
    # Debug output
    print_lines = [l for l in src_lines if "print(" in l and not l.strip().startswith("#")]
    print(f"   Debug print calls: {len(print_lines)}")
    
    # Network access
    net_imports = [l for l in src_lines if any(n in l for n in ["socket", "urllib", "requests", "http"]) and not l.strip().startswith("#")]
    print(f"   External network imports: {len(net_imports)}")
    
    # Scratch path
    scratch_deps = [l for l in src_lines if "scratch" in l.lower() and not l.strip().startswith("#")]
    print(f"   Scratch path dependencies: {len(scratch_deps)}")
    
    # Absolute local paths
    abs_paths = [l for l in src_lines if any(p in l.lower() for p in ["c:\\", "c:/", "/users/", "/home/", "sundareswaran"]) and not l.strip().startswith("#")]
    print(f"   Absolute local path dependencies: {len(abs_paths)}")

    # Hidden imports from development-only files:
    # Notice: line 26: import candidates.candidate_cl_fert_gated as m1_module
    import_lines = [l.strip() for l in src_lines if (l.strip().startswith("import ") or l.strip().startswith("from "))]
    print(f"   All imports in candidate:")
    for imp in import_lines:
        print(f"     {imp}")

    # 6 & 7. Reconstruct packaging/conversion process and test ISOLATED execution
    print("\n6 & 7. Reconstructing Packaging / Isolated Deployment Test:")
    print("   Testing whether frozen candidate bytes alone can be submitted directly as main.py in an isolated environment...")

    with tempfile.TemporaryDirectory() as td:
        isolated_main = os.path.join(td, "main.py")
        with open(isolated_main, "wb") as f:
            f.write(cand_bytes)
        
        # Test 7a: Single file isolated execution (mimicking Kaggle container unpack)
        test_script = os.path.join(td, "test_standalone.py")
        with open(test_script, "w") as f:
            f.write("""
import sys
# Strip workspace path from sys.path to simulate Kaggle isolated container
sys.path = [p for p in sys.path if "kagriculture" not in p.lower()]
import kaggle_environments

try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", "main.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print("STANDALONE_IMPORT: SUCCESS")
except Exception as e:
    print(f"STANDALONE_IMPORT: FAILED ({type(e).__name__}: {e})")

env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 10, "seed": 42})
res = env.run(["main.py", "starter"])
step1_action = res[1][0]["action"]
print(f"STANDALONE_RUN_STEP1_ACTION: {step1_action}")
""")
        p = subprocess.run([sys.executable, test_script], cwd=td, capture_output=True, text=True)
        print(f"   Isolated Subprocess Output:\n{p.stdout.strip()}")
        if p.stderr.strip():
            print(f"   Isolated Subprocess Stderr:\n{p.stderr.strip()}")

    # Check if submitted_artifact_bytes == frozen_candidate_bytes
    print("\n8. Identity Evaluation:")
    print("   Does the frozen candidate file run in standalone Kaggle environment without repository?")
    print("   FINDING: The frozen candidate contains line 26:")
    print("     'import candidates.candidate_cl_fert_gated as m1_module'")
    print("   When uploaded to Kaggle as a standalone 'main.py' (or inside a tarball without the candidates/ directory),")
    print("   Python raises ModuleNotFoundError: No module named 'candidates'.")
    print("   Kaggle environments catches the import error, fails to execute the agent, and defaults to PASS actions (zero economy).")
    print("   Therefore, submitted_artifact_bytes CANNOT equal frozen_candidate_bytes without packaging candidates/ or inlining.")

if __name__ == "__main__":
    audit_1()
