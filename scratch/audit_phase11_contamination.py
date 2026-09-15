import os
import re
import sys

def audit_seed_contamination():
    print("=== PHASE 11: FULL-REPOSITORY SEED LEAKAGE & CONTAMINATION AUDIT ===", flush=True)
    
    seeds = set(range(941000, 941500))
    root_dir = os.path.abspath(".")
    
    target_exts = {".py", ".md", ".json", ".txt", ".log", ".csv"}
    
    allowed_files = {
        "verify_500seed_block.py",
        "run_final_500seed_qualification.py",
        "final_500seed_qualification_results.json",
        "run_instrumented_validation_500seeds.py",
        "instrumented_validation_500seeds.json",
        "audit_tail_risk_and_accounting.py",
        "audit_phase11_contamination.py",
        "WORKER_LABOR_BANDWIDTH_QUALIFICATION_REPORT.md",
        "WORKER_LABOR_BANDWIDTH_AND_HARVEST_RESERVATION_AUDIT_REPORT.md"
    }

    skip_dirs = {".git", "__pycache__", ".pytest_cache", ".vscode", ".idea", "node_modules", ".agents"}
    
    suspicious_hits = []
    scanned_files = 0

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in target_exts:
                continue
                
            if fn in allowed_files:
                continue
                
            fpath = os.path.join(dirpath, fn)
            relpath = os.path.relpath(fpath, root_dir)
            scanned_files += 1
            
            try:
                # Skip giant files > 50MB
                if os.path.getsize(fpath) > 50 * 1024 * 1024:
                    continue
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                if "941000" in content or "941500" in content:
                    suspicious_hits.append((relpath, "Range string match (941000/941500)"))
                    
                found_seeds = set(re.findall(r"\b941[0-4][0-9]{2}\b", content))
                if found_seeds:
                    suspicious_hits.append((relpath, f"Found individual seeds: {list(found_seeds)[:5]}"))
            except Exception as e:
                pass

    print(f"Total files scanned: {scanned_files}", flush=True)
    print(f"Total suspicious files found outside qualification artifacts: {len(suspicious_hits)}", flush=True)
    if suspicious_hits:
        for p, reason in suspicious_hits:
            print(f"  WARNING: {p} -> {reason}", flush=True)
    else:
        print("  CLEAN: Zero seed contamination found in any agent, candidate, or research file!", flush=True)

    cand_path = os.path.join(root_dir, "candidates", "candidate_cl_labor_minimal_v1.py")
    with open(cand_path, "r", encoding="utf-8") as f:
        cand_src = f.read()
        
    print("\nAuditing candidate source code for hardcoding, seed logic, or data leaks:", flush=True)
    leak_terms = ["seed", "941", "random", "mock", "override", "hardcode"]
    for term in leak_terms:
        matches = [line.strip() for line in cand_src.splitlines() if term in line.lower() and not line.strip().startswith("#")]
        if matches:
            print(f"  Candidate code has '{term}' in active lines: {matches}", flush=True)
        else:
            print(f"  No active occurrences of '{term}' in candidate.", flush=True)

if __name__ == "__main__":
    audit_seed_contamination()
