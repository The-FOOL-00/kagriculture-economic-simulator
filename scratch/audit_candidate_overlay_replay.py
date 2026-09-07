import os, sys
import ast

def audit_overlay_file():
    target = 'candidates/candidate_v2_adaptive_overlay.py'
    print("================================================================================")
    print("PHASE 11: REPLAY-CONTAMINATION & DEPENDENCY AUDIT")
    print("================================================================================")
    print(f"Target: {target}")
    
    with open(target, 'r', encoding='utf-8') as f:
        src = f.read()
        
    tree = ast.parse(src)
    
    # 1. Lexical checks in target
    forbidden = [
        '_TRACE', 'TRACE', 'replay', 'canonical', 'base64', 'b85', 'zlib', 'pickle'
    ]
    
    print("\n--- Lexical Token Check on candidate_v2_adaptive_overlay.py ---")
    violations = []
    for token in forbidden:
        count = src.count(token)
        print(f"  Token '{token}': {count} occurrences")
        if count > 0:
            violations.append(token)
            
    # 2. Dependency / Import inspection
    print("\n--- AST Import Inspection ---")
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module)
            
    print(f"  Imported modules: {imports}")
    
    # Check if imported modules contain replay traces
    imported_violations = {}
    for imp in imports:
        if imp.startswith('candidates.') or imp.startswith('agents.'):
            path = imp.replace('.', '/') + '.py'
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    imp_src = f.read()
                imp_hits = [tok for tok in forbidden if tok in imp_src]
                imported_violations[imp] = imp_hits
                print(f"  Imported module '{imp}' ({path}) forbidden tokens: {imp_hits}")
                
    print("\n--- Audit Summary & Architectural Reality ---")
    if violations:
        print(f"  Target direct violations: {violations}")
    else:
        print("  Target direct code: 100% CLEAN of _TRACE, base64, zlib, and serialized arrays.")
        
    if imported_violations:
        print(f"  Imported module contamination: {imported_violations}")
        print("  CRITICAL INSIGHT: Because candidate_v2_adaptive_overlay wraps V2's execution stream,")
        print("  it inherits V2's underlying reliance on _TRACE via import!")
    else:
        print("  Imported modules: CLEAN.")
        
    return len(violations) == 0, len(imported_violations) == 0

if __name__ == '__main__':
    audit_overlay_file()
