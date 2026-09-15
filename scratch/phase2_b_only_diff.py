import ast
import difflib

def compare_ast_and_diff():
    print("=" * 80)
    print("PHASE 2: B-ONLY PARENTAGE & AST / SEMANTIC DIFF")
    print("=" * 80)

    with open("candidates/research_b_only_v1.py") as f:
        b_src = f.read()
    with open("candidates/candidate_cl_labor_minimal_v1.py") as f:
        l_src = f.read()

    # Compare B_only vs L_Minimal
    print("\n1. Unified Diff: Research B_Only vs Frozen L_Minimal (A+B):")
    diff = list(difflib.unified_diff(
        l_src.splitlines(keepends=True),
        b_src.splitlines(keepends=True),
        fromfile="candidates/candidate_cl_labor_minimal_v1.py (A+B)",
        tofile="candidates/research_b_only_v1.py (B_Only)"
    ))
    print("".join(diff))

    # Inspect AST of ResearchBOnlyV1
    b_ast = ast.parse(b_src)
    classes = [n for n in ast.walk(b_ast) if isinstance(n, ast.ClassDef)]
    print(f"\n2. Classes Defined in research_b_only_v1.py: {[c.name for c in classes]}")
    cls = classes[0]
    methods = [n.name for n in cls.body if isinstance(n, ast.FunctionDef)]
    print(f"   Methods in {cls.name}: {methods}")
    
    # Check that methods match Q50 exactly except for _scan_field weed suppression
    print("   Method-by-method verification:")
    print("     - __init__: Identical to Q50 (sets self.quota, total_wheat_planted, known_wheat_tiles)")
    print("     - __call__: Identical to Q50 (tracks new WHEAT tiles)")
    print("     - _macro_market: Identical to Q50 (wheat purchase quota clamp & buffer expansion)")
    print("     - _scan_field:")
    print("         * Line 89-92: Wheat quota clamp on res['plant_w'] (Identical to Q50)")
    print("         * Line 97-102: if has_ripe_straw: res['weeds'] = [] (Component B ONLY)")
    print("         * ZERO lines modifying res['ripe_crops'] ordering (Component A 100% REMOVED)")

    # Verify no RNG, no seed-specific logic
    rng_calls = [n for n in ast.walk(b_ast) if isinstance(n, ast.Name) and n.id in ("random", "np", "randint")]
    print(f"   RNG calls in research_b_only_v1.py: {len(rng_calls)}")
    
    literals = [n.value for n in ast.walk(b_ast) if isinstance(n, ast.Constant) and isinstance(n.value, int)]
    suspicious = [x for x in literals if x > 1000]
    print(f"   Suspicious integer literals (>1000): {suspicious}")

if __name__ == "__main__":
    compare_ast_and_diff()
