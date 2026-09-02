import os
import hashlib
import json
import datetime
from pathlib import Path

def compute_sha256(filepath):
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192 * 1024):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"

def classify_file(rel_path, filename):
    lower = (rel_path + "/" + filename).lower()
    if lower.endswith(".tar.gz") or lower.endswith(".zip"):
        return "Package / Tarball"
    elif lower.endswith(".md"):
        return "Report / Documentation"
    elif lower.endswith(".json") or lower.endswith(".csv"):
        if "result" in lower or "replay" in lower or "manifest" in lower or "episodes" in lower or "meta" in lower:
            return "Raw / Generated Data"
        return "Data / Configuration"
    elif lower.endswith(".py"):
        if "run_" in lower or "validate_" in lower or "test_" in lower or "trace_" in lower or "audit_" in lower or "verify_" in lower:
            return "Script / Test Harness"
        elif "candidate_" in lower or "agent" in lower or "slot" in lower or "apex" in lower or "aethel" in lower or "closer" in lower or "hydra" in lower:
            return "Agent / Candidate Code"
        return "Code / Module"
    return "Other"

def determine_experiment(rel_path, filename):
    lower = (rel_path + "/" + filename).lower()
    if "factorial" in lower:
        return "Factorial Experiment (Causal/Isolation)"
    elif "holdout" in lower:
        return "Holdout Validation"
    elif "gate" in lower:
        return "Challenger Gate Validation"
    elif "reference" in lower or "closer_cleo" in lower or "silas" in lower or "lena" in lower:
        return "Reference Suite / Opponent Benchmarks"
    elif "submission" in lower or "slot2" in lower or "slot1" in lower:
        return "Submission / Staged Portfolio"
    elif "replays" in lower or "replay" in lower:
        return "Replay Mining / Market Data"
    elif "ablation" in lower or "sweep" in lower:
        return "Historical Ablations / Sweeps"
    elif "aethel" in lower:
        return "Aethel Baseline & Evolution"
    elif "apex" in lower:
        return "Apex Baseline & Evaluation"
    elif "hydra" in lower:
        return "Hydra Baseline / Architecture"
    return "General / Utility"

def build_inventory(root_dir):
    records = []
    root = Path(root_dir).resolve()
    
    # Target directories and root files
    dirs_to_search = [
        "", "agents", "candidates", "scripts", "scratch", 
        "reports", "baseline_backup", "replays/raw/reference_agents",
        "engine", "generated_agents_1_32_7"
    ]
    
    seen_files = set()
    
    for d in dirs_to_search:
        target = root / d if d else root
        if not target.exists():
            continue
        
        # If searching root, only take immediate files; otherwise recurse
        if d == "":
            for item in target.iterdir():
                if item.is_file():
                    rel = item.relative_to(root).as_posix()
                    if rel not in seen_files:
                        seen_files.add(rel)
                        records.append(process_file(item, root))
        else:
            for item in target.rglob("*"):
                if item.is_file() and "__pycache__" not in item.parts:
                    rel = item.relative_to(root).as_posix()
                    if rel not in seen_files:
                        seen_files.add(rel)
                        records.append(process_file(item, root))
                        
    records.sort(key=lambda x: x["rel_path"])
    return records

def process_file(item, root):
    rel = item.relative_to(root).as_posix()
    size = item.stat().st_size
    mtime = datetime.datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    # For very large files (> 50MB), note size but compute hash only if relevant
    sha = compute_sha256(item) if size < 100 * 1024 * 1024 else "SKIPPED_LARGE_FILE"
    category = classify_file(rel, item.name)
    experiment = determine_experiment(rel, item.name)
    return {
        "rel_path": rel,
        "name": item.name,
        "size": size,
        "mtime": mtime,
        "sha256": sha,
        "category": category,
        "experiment": experiment
    }

def main():
    root = Path(r"c:\Users\Sundareswaran\Kagriculture")
    records = build_inventory(root)
    
    out_md = root / "reports" / "AETHEL_FINAL_AUDIT_INVENTORY.md"
    os.makedirs(out_md.parent, exist_ok=True)
    
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# AETHEL FINAL AUDIT INVENTORY\n\n")
        f.write(f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Tracked Artifacts:** {len(records)}\n\n")
        f.write("## 1. Key Agent, Candidate, and Submission Artifacts\n\n")
        f.write("| Relative Path | Size (bytes) | Modified Time | SHA-256 | Type | Experiment / Role |\n")
        f.write("| :--- | ---: | :--- | :--- | :--- | :--- |\n")
        
        # Priority list
        priority_keywords = [
            "aethel", "candidate_", "slot", "submission", "closer_cleo", 
            "apex", "hydra", "corrected", "factorial", "gate", "holdout"
        ]
        
        for r in records:
            if any(k in r["rel_path"].lower() for k in priority_keywords) and not r["rel_path"].startswith("replays/raw/georgymamarin"):
                f.write(f"| `{r['rel_path']}` | {r['size']} | {r['mtime']} | `{r['sha256']}` | {r['category']} | {r['experiment']} |\n")
                
        f.write("\n## 2. Complete File Inventory\n\n")
        f.write("| Relative Path | Size (bytes) | Modified Time | SHA-256 | Type | Experiment / Role |\n")
        f.write("| :--- | ---: | :--- | :--- | :--- | :--- |\n")
        for r in records:
            f.write(f"| `{r['rel_path']}` | {r['size']} | {r['mtime']} | `{r['sha256'][:16]}...` | {r['category']} | {r['experiment']} |\n")
            
    print(f"Inventory written to {out_md} with {len(records)} artifacts.")

if __name__ == "__main__":
    main()
