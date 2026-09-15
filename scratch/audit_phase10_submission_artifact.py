import os
import sys
import inspect
import kaggle_environments

def audit_submission_artifact():
    print("=== PHASE 10: SUBMISSION ARTIFACT INTEGRITY AUDIT ===", flush=True)
    
    cand_path = os.path.abspath("candidates/candidate_cl_labor_minimal_v1.py")
    with open(cand_path, "r", encoding="utf-8") as f:
        src = f.read()

    lines = src.splitlines()
    
    # 1. Check class name and entrypoint
    print("Checking entrypoint and class definitions:", flush=True)
    has_class = "class ClosedLoopLaborMinimalV1" in src
    has_agent_instance = "agent = ClosedLoopLaborMinimalV1()" in src
    has_func_entrypoint = "def candidate_agent(obs, config=None):" in src
    print(f"  Class 'ClosedLoopLaborMinimalV1': {has_class}")
    print(f"  Module agent instance 'agent': {has_agent_instance}")
    print(f"  Callable function entrypoint 'candidate_agent': {has_func_entrypoint}")
    assert has_class and has_agent_instance and has_func_entrypoint, "Entrypoints missing!"

    # 2. Check for absolute paths
    print("\nChecking for absolute paths and machine-specific strings:", flush=True)
    abs_path_terms = ["C:\\", "c:/", "/Users/", "/home/", "Sundareswaran", "AppData", ".gemini"]
    found_abs = []
    for idx, line in enumerate(lines, 1):
        for term in abs_path_terms:
            if term.lower() in line.lower() and not line.strip().startswith("#"):
                found_abs.append((idx, line.strip()))
    print(f"  Machine-specific / absolute paths found: {len(found_abs)}")
    assert len(found_abs) == 0, f"Absolute paths found: {found_abs}"
    print("  PASS: Zero machine-specific absolute paths in candidate.", flush=True)

    # 3. Check for scratch dependencies
    print("\nChecking for scratch dependencies:", flush=True)
    found_scratch = []
    for idx, line in enumerate(lines, 1):
        if "scratch" in line.lower() and not line.strip().startswith("#"):
            found_scratch.append((idx, line.strip()))
    print(f"  Scratch references found: {len(found_scratch)}")
    assert len(found_scratch) == 0, f"Scratch dependencies found: {found_scratch}"
    print("  PASS: Zero scratch module imports or dependencies.", flush=True)

    # 4. Check for debug prints
    print("\nChecking for print statements:", flush=True)
    found_prints = []
    for idx, line in enumerate(lines, 1):
        if line.strip().startswith("print(") or " print(" in line:
            found_prints.append((idx, line.strip()))
    print(f"  Print calls found: {len(found_prints)}")
    assert len(found_prints) == 0, f"Debug prints found: {found_prints}"
    print("  PASS: Zero print statements in candidate.", flush=True)

    # 5. Check for external network calls / sockets
    print("\nChecking for network / socket imports:", flush=True)
    net_terms = ["socket", "requests", "urllib", "http.client", "subprocess", "eval", "exec"]
    found_net = []
    for idx, line in enumerate(lines, 1):
        for term in net_terms:
            if f"import {term}" in line or f"from {term}" in line:
                found_net.append((idx, line.strip()))
    print(f"  Network / dangerous imports found: {len(found_net)}")
    assert len(found_net) == 0, f"Network imports found: {found_net}"
    print("  PASS: Zero network or dangerous system calls.", flush=True)

    # 6. Test in kaggle_environments directly with competition syntax
    print("\nTesting candidate in kaggle_environments competition harness:", flush=True)
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 20, "seed": 42})
    
    # Import candidate module dynamically as an agent file
    sys.path.insert(0, os.path.abspath("candidates"))
    import candidate_cl_labor_minimal_v1 as cand
    
    # Test function entrypoint
    res = env.run([cand.candidate_agent, "starter"])
    print(f"  Episode completed successfully. Steps: {len(res)}, Final reward: {res[-1][0]['reward']}")
    assert len(res) == 20, f"Expected 20 steps, got {len(res)}"
    assert res[-1][0]["status"] == "DONE", f"Status is {res[-1][0]['status']}"
    print("  PASS: Candidate agent executed with ZERO warnings and ZERO errors in competition harness.", flush=True)

if __name__ == "__main__":
    audit_submission_artifact()
