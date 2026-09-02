import difflib
from pathlib import Path
import sys

def audit_pair(file1_path, file2_path, name1, name2, expected_diffs):
    with open(file1_path, 'r', encoding='utf-8') as f:
        lines1 = f.readlines()
    with open(file2_path, 'r', encoding='utf-8') as f:
        lines2 = f.readlines()
        
    diff = list(difflib.unified_diff(lines1, lines2, fromfile=name1, tofile=name2, lineterm=''))
    
    print(f"\n=======================================================")
    print(f"DIFF AUDIT: {name1} vs {name2}")
    print(f"=======================================================")
    
    # Analyze hunks
    added_lines = [l[1:].strip() for l in diff if l.startswith('+') and not l.startswith('+++')]
    removed_lines = [l[1:].strip() for l in diff if l.startswith('-') and not l.startswith('---')]
    
    print(f"Lines removed from {name1}: {len(removed_lines)}")
    for l in removed_lines:
        print(f"  - {l}")
    print(f"Lines added to {name2}: {len(added_lines)}")
    for l in added_lines:
        print(f"  + {l}")
        
    diff_summary = []
    has_unexpected = False
    
    # Check each difference against expected
    all_diffs_accounted = True
    for r, a in zip(removed_lines, added_lines):
        pair_str = f"- {r} -> + {a}"
        matched_expected = False
        for exp in expected_diffs:
            if exp["old"] == r and exp["new"] == a:
                matched_expected = True
                diff_summary.append({"diff": pair_str, "class": exp["class"], "desc": exp["desc"]})
                break
        if not matched_expected:
            has_unexpected = True
            diff_summary.append({"diff": pair_str, "class": "UNEXPECTED / BEHAVIORAL", "desc": "Not in expected changes"})
            
    if len(removed_lines) != len(added_lines):
        has_unexpected = True
        diff_summary.append({"diff": "Mismatched line count diff", "class": "UNEXPECTED", "desc": "Line count changed"})
        
    print("\nClassification:")
    for d in diff_summary:
        print(f"  [{d['class']}] {d['diff']} ({d['desc']})")
        
    if has_unexpected:
        print(f"\n>>> RESULT: FAIL - Unexpected differences found between {name1} and {name2}")
        return False
    else:
        print(f"\n>>> RESULT: PASS - All differences strictly match expected factorial factor toggles.")
        return True

def main():
    root = Path(__file__).resolve().parent.parent
    agents_dir = root / "agents"
    
    cand_a = agents_dir / "candidate_a_aethel_v1.py"
    cand_b = agents_dir / "candidate_b_aethel_mc.py"
    cand_c = agents_dir / "candidate_c_aethel_t712.py"
    cand_d = agents_dir / "candidate_d_aethel_refined.py"
    staged = root / "candidates" / "slot2_aethel_refined_v2.py"
    base = agents_dir / "aethel_factorial_base.py"
    
    results = []
    
    # Base vs A (should be byte identical)
    print("Checking Base vs Candidate A (Identity check)...")
    with open(base, 'rb') as f1, open(cand_a, 'rb') as f2:
        if f1.read() == f2.read():
            print(">>> Base and Candidate A are 100% BYTE IDENTICAL (PASS)")
            results.append(True)
        else:
            print(">>> FAIL: Base and Candidate A differ!")
            results.append(False)
            
    # Candidate D vs Staged Slot 2 (should be byte identical)
    print("\nChecking Candidate D vs candidates/slot2_aethel_refined_v2.py (Identity check)...")
    with open(cand_d, 'rb') as f1, open(staged, 'rb') as f2:
        if f1.read() == f2.read():
            print(">>> Candidate D and staged slot 2 are 100% BYTE IDENTICAL (PASS)")
            results.append(True)
        else:
            print(">>> FAIL: Candidate D and staged slot 2 differ!")
            results.append(False)
            
    # A vs B (Market Controller toggle)
    exp_ab = [{
        "old": "_MARKET_CONTROLLER_ENABLED = False",
        "new": "_MARKET_CONTROLLER_ENABLED = True",
        "class": "EXPECTED",
        "desc": "Factor 1: Market Controller enabled"
    }]
    results.append(audit_pair(cand_a, cand_b, "Candidate A", "Candidate B", exp_ab))
    
    # A vs C (Terminal Controller toggle)
    exp_ac = [{
        "old": "_TERMINAL_START_STEP = 717",
        "new": "_TERMINAL_START_STEP = 712",
        "class": "EXPECTED",
        "desc": "Factor 2: Step-712 Terminal trigger enabled"
    }]
    results.append(audit_pair(cand_a, cand_c, "Candidate A", "Candidate C", exp_ac))
    
    # B vs D (Terminal Controller toggle with MC=ON)
    exp_bd = [{
        "old": "_TERMINAL_START_STEP = 717",
        "new": "_TERMINAL_START_STEP = 712",
        "class": "EXPECTED",
        "desc": "Factor 2: Step-712 Terminal trigger enabled"
    }]
    results.append(audit_pair(cand_b, cand_d, "Candidate B", "Candidate D", exp_bd))
    
    # C vs D (Market Controller toggle with T=712)
    exp_cd = [{
        "old": "_MARKET_CONTROLLER_ENABLED = False",
        "new": "_MARKET_CONTROLLER_ENABLED = True",
        "class": "EXPECTED",
        "desc": "Factor 1: Market Controller enabled"
    }]
    results.append(audit_pair(cand_c, cand_d, "Candidate C", "Candidate D", exp_cd))
    
    # A vs D (Both factors toggled)
    exp_ad = [
        {
            "old": "_MARKET_CONTROLLER_ENABLED = False",
            "new": "_MARKET_CONTROLLER_ENABLED = True",
            "class": "EXPECTED",
            "desc": "Factor 1: Market Controller enabled"
        },
        {
            "old": "_TERMINAL_START_STEP = 717",
            "new": "_TERMINAL_START_STEP = 712",
            "class": "EXPECTED",
            "desc": "Factor 2: Step-712 Terminal trigger enabled"
        }
    ]
    results.append(audit_pair(cand_a, cand_d, "Candidate A", "Candidate D", exp_ad))
    
    print("\n=======================================================")
    print("FINAL SOURCE AUDIT SUMMARY")
    print("=======================================================")
    if all(results):
        print("ALL SOURCE DIFFS ARE 100% FACTORIALLY ISOLATED AND VERIFIED (PASS)")
        sys.exit(0)
    else:
        print("SOURCE DIFF AUDIT FAILED - UNINTENDED BEHAVIORAL DIFFERENCES DETECTED")
        sys.exit(1)

if __name__ == "__main__":
    main()
