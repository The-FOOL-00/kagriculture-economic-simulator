"""
Candidate Audit & Purity Verification Script
Audits AST parse, imports, and replay token scan across all candidate arms.
"""
import ast
import os
import sys

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

FILES_TO_AUDIT = [
    "candidates/candidate_cl_economic_v1.py",
    "candidates/candidate_cl_fixed_straw_control.py",
    "candidates/candidate_cl_fixed_sheep_control.py",
    "candidates/candidate_cl_fixed_straw_sheep_control.py",
    "candidates/candidate_cl_temporal_v1.py",
    "candidates/candidate_cl_temporal_v2.py",
    "candidates/candidate_cl_temporal_v3.py"
]

FORBIDDEN_TOKENS = ["_TRACE", "base64", "base85", "zlib", "pickle", "sched"]

def audit():
    print("=" * 80)
    print("CANDIDATE REPLAY & STATIC PURITY AUDIT")
    print("=" * 80)
    for f in FILES_TO_AUDIT:
        if not os.path.exists(f):
            print(f"[FAIL] Missing file: {f}")
            sys.exit(1)
            
        content = open(f, "r", encoding="utf-8").read()
        
        # AST parse
        try:
            ast.parse(content)
            print(f"[PASS] AST Parse: {f}")
        except Exception as e:
            print(f"[FAIL] AST Parse Error in {f}: {e}")
            sys.exit(1)
            
        # Forbidden tokens scan
        for tok in FORBIDDEN_TOKENS:
            if tok in content:
                print(f"[FAIL] Forbidden token '{tok}' found in {f}")
                sys.exit(1)
                
    print("[PASS] All files 100% clean of forbidden replay tokens.")
    
    # Import check
    from candidates.candidate_cl_fixed_straw_control import agent_fn as fn_straw
    from candidates.candidate_cl_fixed_sheep_control import agent_fn as fn_sheep
    from candidates.candidate_cl_fixed_straw_sheep_control import agent_fn as fn_both
    from candidates.candidate_cl_temporal_v1 import agent_fn as fn_temp_v1
    from candidates.candidate_cl_temporal_v2 import agent_fn as fn_temp_v2
    print("[PASS] All 5 candidate agent functions imported successfully.")

if __name__ == "__main__":
    audit()
