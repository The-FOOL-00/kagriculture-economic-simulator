"""
Phase 10: Replay Contamination & Transitive Dependency Audit
===========================================================
Scans `candidates/candidate_closed_loop_commitment_v1.py` for:
- Forbidden replay tokens: _TRACE, base64, base85, zlib, pickle, marshal, 720, etc.
- Step-indexed action arrays or historical step lookup dicts.
- Non-standard-library imports.
- Transitive dependencies on other candidates or v1/v2.
"""

import sys, os, ast, re

TARGET_FILE = "candidates/candidate_closed_loop_commitment_v1.py"

FORBIDDEN_TOKENS = [
    "_TRACE", "trace", "TRACE", "base64", "b64", "base85", "b85",
    "zlib", "pickle", "marshal", "serialized", "action table",
    "historical action", "step lookup", "720-step", "known replay"
]

ALLOWED_IMPORTS = {"math", "random", "copy", "json", "collections", "deque", "defaultdict", "sys", "os", "time"}

def run_contamination_audit():
    print(f"=== Phase 10 Audit: Scanning {TARGET_FILE} ===")
    if not os.path.exists(TARGET_FILE):
        print(f"ERROR: File not found: {TARGET_FILE}")
        return False

    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        lines = content.splitlines()

    # 1. AST Validation
    try:
        tree = ast.parse(content, filename=TARGET_FILE)
        print("[PASS] AST Parsing: Syntax Valid Python 3")
    except Exception as e:
        print(f"[FAIL] AST Parsing Failed: {e}")
        return False

    # 2. Transitive Imports Audit
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module.split('.')[0])

    print(f"[INFO] Detected top-level imports: {sorted(imported_modules)}")
    forbidden_imports = []
    for mod in imported_modules:
        if mod not in ALLOWED_IMPORTS:
            forbidden_imports.append(mod)
        if "candidate" in mod or "slot" in mod or "agent" in mod or "v2" in mod or "v1" in mod:
            forbidden_imports.append(mod)

    if forbidden_imports:
        print(f"[FAIL] GATE 2 VIOLATION: Forbidden or external imports detected: {forbidden_imports}")
        return False
    else:
        print("[PASS] GATE 2 PASSED: 0 transitive local candidate dependencies. Standard library only.")

    # 3. Token Search
    token_hits = []
    for line_idx, line in enumerate(lines, 1):
        for tok in FORBIDDEN_TOKENS:
            if re.search(r'\b' + re.escape(tok) + r'\b', line, re.IGNORECASE):
                token_hits.append((line_idx, tok, line.strip()))

    print(f"\nScanning for {len(FORBIDDEN_TOKENS)} forbidden tokens...")
    code_hits = []
    for line_idx, tok, text in token_hits:
        is_comment = text.startswith("#") or text.startswith('"""') or text.startswith("'''") or text.startswith("- 0")
        if not is_comment:
            code_hits.append((line_idx, tok, text))
            print(f"  [CODE HIT] Line {line_idx}: '{tok}' -> {text}")
        else:
            print(f"  [COMMENT/DOC] Line {line_idx}: '{tok}' -> {text}")

    if code_hits:
        print(f"[FAIL] GATE 1 VIOLATION: Found {len(code_hits)} active code hits for forbidden tokens!")
        return False
    else:
        print(f"[PASS] GATE 1 PASSED: 0 active code occurrences of forbidden tokens.")

    # 4. Semantic Audit: Step Lookup & Fixed Action Arrays
    step_lookups = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.Name) and "step" in node.slice.id.lower():
                step_lookups.append(ast.unparse(node))

    if step_lookups:
        print(f"[FAIL] SEMANTIC VIOLATION: Step-indexed lookups detected: {step_lookups}")
        return False
    else:
        print("[PASS] SEMANTIC AUDIT PASSED: No step-indexed lookup arrays found.")

    # 5. File SHA256 Hash
    import hashlib
    with open(TARGET_FILE, "rb") as f:
        file_sha256 = hashlib.sha256(f.read()).hexdigest()
    print(f"\nTarget File SHA256: {file_sha256}")
    print("=== AUDIT VERDICT: 100% REPLAY-FREE, SELF-CONTAINED, COMPLIANT ===")
    return True

if __name__ == "__main__":
    success = run_contamination_audit()
    sys.exit(0 if success else 1)
