import os
import re
import ast
import json

def audit9():
    print("=" * 80)
    print("AUDIT 9: COMPREHENSIVE SEED-CONTAMINATION & LEAKAGE AUDIT")
    print("=" * 80)

    # 1. Inspect candidate_cl_labor_minimal_v1.py AST and source
    cand_path = "candidates/candidate_cl_labor_minimal_v1.py"
    with open(cand_path, "r", encoding="utf-8") as f:
        cand_src = f.read()

    print(f"1. Deep AST Inspection of {cand_path}:")
    cand_ast = ast.parse(cand_src)

    seed_refs = []
    condition_types = []
    literals = []

    for node in ast.walk(cand_ast):
        # Check variable names
        if isinstance(node, ast.Name):
            if "seed" in node.id.lower():
                seed_refs.append((node.lineno, node.id))
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, int):
                literals.append((node.lineno, node.value))
        elif isinstance(node, (ast.If, ast.IfExp)):
            condition_types.append(node.lineno)

    print(f"   AST walk complete: {len(literals)} integer literals found.")
    
    # Check if any integer literal is in qualification range 941000-941499
    qual_literals = [l for l in literals if 941000 <= l[1] <= 941499]
    print(f"   Literals in range [941000, 941499]: {qual_literals}")
    
    # Check if any integer literal is in discovery range 1300-1399
    disc_literals = [l for l in literals if 1300 <= l[1] <= 1399]
    print(f"   Literals in range [1300, 1399]: {disc_literals}")

    # Check all seed_refs: verify they refer to crop seeds (seeds['WHEAT'], etc.) not RNG seeds
    rng_seed_uses = []
    for line, name in seed_refs:
        # inspect surrounding line
        line_txt = cand_src.splitlines()[line - 1]
        if "obs.get(\"seed\")" in line_txt or "config.get(\"seed\")" in line_txt or "random.seed" in line_txt:
            rng_seed_uses.append((line, line_txt))
    print(f"   RNG/Episode seed references found: {rng_seed_uses}")

    # 2. Check for modulo tricks, hash tables, or hidden state fingerprints
    print("\n2. Checking for Modulo Tricks, Hash Fingerprints, or State Lookup Tables:")
    modulo_ops = []
    for node in ast.walk(cand_ast):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
            modulo_ops.append(node.lineno)
    print(f"   Modulo operations in candidate: lines {modulo_ops}")
    # In candidate, modulo is only hour % 24 or similar? Let's check:
    for l in modulo_ops:
        print(f"     Line {l}: {cand_src.splitlines()[l-1].strip()}")

    # 3. Repository-wide scan across all agents and candidates for qualification range 941000-941499
    print("\n3. Scanning all .py files in agents/ and candidates/ for qualification seeds:")
    found_in_agents = []
    for folder in ["agents", "candidates"]:
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(".py"):
                    fpath = os.path.join(root, file)
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    for s in range(941000, 941500):
                        if str(s) in content:
                            found_in_agents.append((fpath, s))
                            break
    print(f"   Occurrences in agents/ or candidates/: {len(found_in_agents)}")
    if found_in_agents:
        for fa in found_in_agents:
            print(f"     FAIL: {fa[0]} contains seed {fa[1]}")
    else:
        print("     PASS: Zero occurrences of qualification seeds in any candidate or agent.")

    out = {
        "candidate_file": cand_path,
        "qual_literals_found": qual_literals,
        "disc_literals_found": disc_literals,
        "rng_seed_uses": rng_seed_uses,
        "found_in_agents": found_in_agents,
        "is_seed_agnostic": (len(qual_literals) == 0 and len(rng_seed_uses) == 0 and len(found_in_agents) == 0)
    }
    with open("scratch/audit9_results.json", "w") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    audit9()
