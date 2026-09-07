import sys, os
import ast

target_file = os.path.abspath("candidates/candidate_closed_loop_execution_v1.py")
print(f"Auditing file for replay contamination: {target_file}")

with open(target_file, "r", encoding="utf-8") as f:
    code = f.read()

forbidden_terms = [
    "_TRACE", "TRACE", "b85decode", "b64decode", "zlib.decompress",
    "pickle.", "candidates.slot2", "slot2_aethel", "candidate_a_aethel",
    "base85", "base64"
]

found = []
for term in forbidden_terms:
    if term in code:
        found.append(term)

print(f"Forbidden terms scan: {len(found)} found: {found}")

# Inspect imports via AST
tree = ast.parse(code)
imports = []
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for alias in node.names:
            imports.append(alias.name)
    elif isinstance(node, ast.ImportFrom):
        imports.append(f"from {node.module} import {', '.join(a.name for a in node.names)}")

print(f"Transitive Imports: {imports}")
is_clean = (len(found) == 0) and all(imp in ("sys", "os", "math", "random", "copy", "json", "collections") or imp.startswith("from collections") for imp in imports)
print(f"Replay Contamination Verdict: {'100% CLEAN' if is_clean else 'CONTAMINATED'}")
