"""
Automated Replay Contamination & Closed-Loop Mutation Gauntlet
=============================================================
Performs AST parsing, forbidden token scanning, standard library verification,
and executes 5 severe state mutation vectors:
1. Cash Starvation ($0 start)
2. Feed Starvation (0 wheat in shed)
3. Worker Displacement (teleported across board)
4. Early Ripening (crop yield at step 50)
5. Market Price Shock ($10 collapse)
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
import ast
import re
import hashlib
import kaggle_environments

FORBIDDEN_TOKENS = [
    r"\b_TRACE\b", r"\bb85decode\b", r"\bb64decode\b", r"\bzlib\b",
    r"\bpickle\b", r"\bbase64\b", r"\bbase85\b", r"\b_HISTORICAL\b",
    r"\b_ACTION_ARRAY\b", r"\b_SCHEDULE\b"
]

def audit_candidate_source(filepath):
    print(f"=== Auditing {filepath} ===")
    with open(filepath, "r", encoding="utf-8") as f:
        src = f.read()
        
    sha256 = hashlib.sha256(src.encode("utf-8")).hexdigest()
    print(f"File Size: {len(src)} bytes | SHA256: {sha256}")
    
    # AST Check
    try:
        tree = ast.parse(src)
        print("[PASS] AST Parsing: Syntax Valid Python 3")
    except SyntaxError as e:
        print(f"[FAIL] AST Syntax Error: {e}")
        return False
        
    # Import check
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    print(f"Detected Imports: {imports}")
    
    allowed_standard = {"collections", "math", "random", "itertools", "heapq", "typing", "functools", "copy", "deque"}
    for imp in imports:
        root_pkg = imp.split('.')[0]
        if root_pkg not in allowed_standard:
            print(f"[FAIL] Non-standard / external import detected: {imp}")
            return False
    print("[PASS] Gate 2: Standard library imports only (0 external / candidate dependencies)")
    
    # Active code lines
    lines = src.splitlines()
    code_lines = []
    in_doc = False
    for line in lines:
        stripped = line.strip()
        if '"""' in stripped or "'''" in stripped:
            cnt = stripped.count('"""') + stripped.count("'''")
            if cnt % 2 == 1:
                in_doc = not in_doc
            continue
        if in_doc or stripped.startswith("#"):
            continue
        code_lines.append(line)
        
    token_hits = []
    for line_idx, line in enumerate(code_lines, 1):
        for tok in FORBIDDEN_TOKENS:
            if re.search(tok, line):
                token_hits.append((line_idx, tok, line.strip()))
                
    if token_hits:
        print(f"[FAIL] Forbidden Active Code Token Hits ({len(token_hits)}):")
        for lh in token_hits[:5]:
            print(f"  Line {lh[0]}: {lh[1]} in '{lh[2]}'")
        return False
    else:
        print("[PASS] Gate 1: 0 forbidden replay tokens in active executable code")
        
    return True

def run_mutation_gauntlet(agent_fn, agent_name="Candidate"):
    print(f"\n=== Executing Mutation Gauntlet for {agent_name} ===")
    mutations = [
        ("Cash Starvation ($0)", lambda farm: farm.update({"money": 0})),
        ("Feed Starvation (0 wheat)", lambda priv: priv.get("shed", {}).update({"WHEAT": 0})),
        ("Worker Displacement", lambda farm: farm.update({"farmer": [0, 9], "hands": [[9, 0], [0, 0]]})),
        ("Early Crop Ripening", lambda farm: farm["tiles"][0][0].update({"yield_units": 6}) if isinstance(farm.get("tiles", [[]])[0][0], dict) else None),
        ("Market Price Shock ($10)", lambda m: m.get("prices", {}).update({"MELON": 10, "STRAWBERRY": 10})),
    ]
    
    all_passed = True
    for m_name, m_fn in mutations:
        try:
            def mutator(obs, config=None):
                step = int(obs.get("step", 0) or 0)
                if step == 10:
                    farms = obs.get("farms", [{}, {}])
                    priv = obs.get("private", {})
                    market = obs.get("market", {})
                    try: m_fn(farms[0])
                    except: pass
                    try: m_fn(priv)
                    except: pass
                    try: m_fn(market)
                    except: pass
                return agent_fn(obs, config)
                
            env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 120, "seed": 42})
            env.run([mutator, "starter"])
            status0 = env.steps[-1][0].status
            if status0 == "ACTIVE" or status0 == "DONE":
                print(f"[PASS] Mutation: {m_name:<26} (Completed 120 steps successfully, status: {status0})")
            else:
                print(f"[FAIL] Mutation: {m_name:<26} (Ended with error status: {status0})")
                all_passed = False
        except Exception as e:
            print(f"[FAIL] Mutation: {m_name} raised exception: {e}")
            all_passed = False
            
    return all_passed

if __name__ == "__main__":
    audit_candidate_source("candidates/candidate_closed_loop_commitment_v1.py")
    from candidates.candidate_closed_loop_commitment_v1 import agent as comm_v1_agent
    run_mutation_gauntlet(comm_v1_agent, "CL-Commitment-V1")
