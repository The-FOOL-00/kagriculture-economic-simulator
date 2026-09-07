import sys, os
import re

SUSPECT_PATTERNS = [
    r"_TRACE",
    r"\bTRACE\b",
    r"base64",
    r"b85decode",
    r"b64decode",
    r"\bzlib\b",
    r"\bpickle\b",
    r"replay",
    r"canonical",
    r"serialized",
    r"step_indexed",
    r"lookup_table",
    r"future_state",
    r"\[\s*\[\s*['\"](?:NORTH|SOUTH|EAST|WEST|PASS|PLANT|WATER|HARVEST)['\"].*?\]\s*\]" # raw nested action list
]

def scan_file(filepath):
    print(f"Auditing file: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    findings = []
    lines = content.splitlines()
    for line_no, line in enumerate(lines, 1):
        # Ignore comments or docstrings explaining anti-patterns
        if line.strip().startswith("#") or line.strip().startswith("*") or "Zero Replay" in line:
            continue
        for pat in SUSPECT_PATTERNS:
            matches = re.findall(pat, line, re.IGNORECASE)
            if matches:
                findings.append((line_no, pat, line.strip()))
                
    if not findings:
        print(f"  [PASS] 100% Clean! Zero replay contamination detected.")
        return True
    else:
        print(f"  [FAIL] Detected {len(findings)} suspicious patterns:")
        for lno, pat, ltxt in findings:
            print(f"    L{lno}: pattern '{pat}' -> {ltxt}")
        return False

if __name__ == '__main__':
    target = "candidates/candidate_cl_aethel_grandmaster.py"
    res = scan_file(target)
    sys.exit(0 if res else 1)
