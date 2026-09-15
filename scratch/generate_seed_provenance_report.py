import json
import os
import re

BASE_DIR = r"c:\Users\Sundareswaran\Kagriculture"
OUTPUT_DIR = os.path.join(BASE_DIR, "experiments", "EXP-DEV-003")
os.makedirs(OUTPUT_DIR, exist_ok=True)
PROV_FILE = os.path.join(OUTPUT_DIR, "SEED_PROVENANCE.md")

with open("scratch/fast_provenance_hits.json", "r", encoding="utf-8") as f:
    data = json.load(f)

hits = data["hits"]
range_hits = data["range_hits"]

def get_surrounding_context(rel_path, line_no, context_lines=2):
    full_path = os.path.join(BASE_DIR, rel_path)
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
            lines = fh.readlines()
        start = max(0, line_no - 1 - context_lines)
        end = min(len(lines), line_no + context_lines)
        ctx = []
        for i in range(start, end):
            prefix = ">> " if (i == line_no - 1) else "   "
            ctx.append(f"{prefix}{i+1}: {lines[i].rstrip()[:120]}")
        return "\n".join(ctx)
    except Exception as e:
        return f"   Error reading context: {e}"

def classify_hit(file_path, content, is_range=False):
    fp = file_path.lower()
    c = content.lower()
    
    # Check if result file
    if fp.endswith((".json", ".csv")) and ("result" in fp or "scan" in fp or "raw" in fp or "tournament" in fp or "ckpt" in fp or "replay" in fp):
        return "C / D", "Actual simulation output / Result artifact recording realized trajectory/margin"
    
    # Check if script that executes simulation
    if fp.endswith(".py") and any(k in fp for k in ["run_", "test_", "audit_", "census_", "quick_", "diagnose_"]):
        if any(k in c for k in ["range(", "seeds =", "seeds_list =", "seeds:"]):
            return "C", "Actual simulation / execution harness range declaration"
        return "C / D", "Script inspecting/processing simulation seeds"

    # Check if protocol/governance/audit docs
    if fp.endswith(".md"):
        if any(k in fp for k in ["protocol", "registry", "holdout", "evidence", "baseline_map", "gate"]):
            return "A", "Protocol / governance documentation or historical benchmark registry"
        if "audit" in fp or "report" in fp or "contradictions" in fp:
            return "A / D", "Historical audit report or evidence matrix citing benchmark evaluation"
        return "A", "Documentation"
    
    return "F", "Unknown / unclassified"

# Group hits by major files
grouped_hits = {}
for h in hits:
    f = h["file"]
    if f not in grouped_hits:
        grouped_hits[f] = []
    grouped_hits[f].append(h)

# Range hits grouped
grouped_range = {}
for rh in range_hits:
    f = rh["file"]
    if f not in grouped_range:
        grouped_range[f] = []
    grouped_range[f].append(rh)

# Build markdown
md = []
md.append("# SEED PROVENANCE AUDIT: CANDIDATE PARTITION 50100–50149")
md.append("")
md.append("**Experiment**: EXP-DEV-003 (Conditional Specialization / Opportunity-Value Discovery)  ")
md.append("**Audit Target Range**: `50100` to `50149` ($N=50$ contiguous seeds)  ")
md.append("**Audit Date**: 2026-09-14  ")
md.append("**Auditor**: Autonomous Verification Engine (Zero-Leakage Governance)  ")
md.append("")
md.append("---")
md.append("")
md.append("## 1. Executive Provenance Verdict")
md.append("")
md.append("### **VERDICT: CONTAMINATED / PREVIOUSLY EXECUTED — STRICTLY REJECTED**")
md.append("")
md.append("> [!CAUTION]")
md.append("> **THE CANDIDATE DISCOVERY PARTITION `50100–50149` IS NOT VIRGIN.**  ")
md.append("> It was previously designated as a benchmark and holdout partition in parent development cycles, and has been **actively executed and simulated** across multiple prior experimental harnesses. Crucially, it contains completed simulation result artifacts evaluating **Tomato/Pizza shop specialization policies** (`POLICY_E`, `POLICY_F`, `POLICY_G`, `POLICY_H`), Head-to-Head margin scans against `Dmitrii-LB2800`, and macro-census evaluations.  ")
md.append("> **Pursuant to Governance Rule 10 and Directive 2, Partition `50100–50149` is REJECTED.** It MUST NOT be used for EXP-DEV-003 Discovery.")
md.append("")
md.append("---")
md.append("")
md.append("## 2. Audit Methodology Correction")
md.append("")
md.append("- **Audit-Method Event**: The initial brute-force scan (`line-by-line regex across 50 seeds`) was terminated safely to prevent computational inefficiency. Zero simulations were run and zero candidate code was modified.")
md.append("- **Replacement Methodology**: A high-performance, whole-text repository-wide token audit was executed using Git grep and Python whole-file buffered text indexing across all tracked files, untracked scratch scripts, experimental directories, result manifests (`.json`, `.csv`), and Markdown documentation.")
md.append("- **Scope Audited**:")
md.append("  - 1,851 total workspace files scanned.")
md.append("  - 206 individual seed hits identified across 84 files.")
md.append("  - 13 explicit range-execution overlap statements identified.")
md.append("")
md.append("---")
md.append("")
md.append("## 3. Seed Provenance Summary Matrix")
md.append("")
md.append("| Check Category | Finding | Classification | Status |")
md.append("| :--- | :--- | :--- | :--- |")
md.append("| **Found in Repository Code** | Yes (in 84 files across `scratch/`, root, and `experiments/`) | B / C | **FAIL** |")
md.append("| **Found in Execution Scripts** | Yes (`run_qualification_and_holdout.py`, `run_margin_scan.py`, etc.) | C | **FAIL** |")
md.append("| **Found in Result Artifacts** | Yes (`qualification_and_holdout_results.json`, `v2_dmitrii_margin_scan.json`, etc.) | D | **FAIL** |")
md.append("| **Found in Strategy Selection** | Yes (Simulated for Pizza/Tomato policies `POLICY_E..H`) | E | **FAIL** |")
md.append("| **Found in Parameter Sweeps** | Yes (Batch sweeps, margin scans, macro census) | E | **FAIL** |")
md.append("| **Found in Protocol Registry** | Yes (Registered as 'Audited Benchmark Partition' in `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md`) | A | **FAIL** |")
md.append("")
md.append("---")
md.append("")
md.append("## 4. Key Material Evidence of Prior Simulation & Strategy Selection")
md.append("")
md.append("### 4.1 Prior Specialization Strategy Simulation (`scratch/qualification_and_holdout_results.json`)")
md.append("- **File**: `scratch/qualification_and_holdout_results.json`")
md.append("- **Classification**: **Category D / E (Actual Simulation Results / Strategy Selection)**")
md.append("- **Description**: This artifact contains stored match simulation results for the exact partition `50100–50149` under key `'Fresh Holdout (50100-50149)'` testing the following crop-specialization policies:")
md.append("  - `POLICY_F (Pizza no-Straw -> k=4, SE_LAND, Day12)`")
md.append("  - `POLICY_G (Pizza+ShedFree gated, SE_LAND, Day12)`")
md.append("  - `POLICY_E (Any Pizza -> k=4, SE_LAND, Day12)`")
md.append("  - `POLICY_H (Full-gated k=2, SE_LAND, Day12)`")
md.append("  - `vk_vacant k=1 (Pizza -> k=1, VACANT, Day12)`")
md.append("- **Significance**: Seeds 50100–50149 have already been exposed to pizza/tomato specialization evaluation in prior research. Using them for EXP-DEV-003 would introduce severe pre-exposure bias.")
md.append("")
md.append("### 4.2 Full Head-to-Head Margin Scan (`scratch/v2_dmitrii_margin_scan.json`)")
md.append("- **File**: `scratch/v2_dmitrii_margin_scan.json`")
md.append("- **Classification**: **Category D (Simulation Results Output)**")
md.append("- **Description**: Key `'holdout'` contains 100 complete match records spanning every seed from `50100` to `50149` (both Seat 0 and Seat 1) recording exact terminal coin balances for `ClosedLoopAgentV2` and `Dmitrii-LB2800`.")
md.append("")
md.append("### 4.3 Macro Census Execution (`scratch/census_phase3_500seeds.py`)")
md.append("- **Documentation**: `DEVELOPMENT_GATE_0_2_FINAL_VERDICT.md:75` and `DEVELOPMENT_GATE_0_2_HOLDOUT_PROVENANCE.md:23`")
md.append("- **Classification**: **Category C (Simulation Execution)**")
md.append("- **Description**: Confirms that `scratch/census_phase3_500seeds.py` executed `range(50000, 50500)`, fully simulating town shop revealing dynamics and farm yields across `50100–50149`.")
md.append("")
md.append("### 4.4 Formal Protocol Benchmark Partition Registration")
md.append("- **File**: `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md:59`")
md.append("- **Classification**: **Category A / B (Protocol Documentation & Seed Declaration)**")
md.append("- **Line**: `| **Audited Benchmark Partition** | 50100 to 50149 | 50 Seeds (100 matches) | Paired Seat 0 + Seat 1 | Cross-validation against historical Audit 2.2 benchmark data. |`")
md.append("")
md.append("---")
md.append("")
md.append("## 5. Detailed Forensic Classification of Material Hits")
md.append("")
md.append("### Classification Legend:")
md.append("- **A**: Mere protocol / quarantine / governance documentation")
md.append("- **B**: Seed declaration (e.g. constant list or range definition)")
md.append("- **C**: Actual simulation / execution harness")
md.append("- **D**: Result inspection / stored simulation output")
md.append("- **E**: Parameter tuning / strategy selection evidence")
md.append("- **F**: Unknown / unrelated")
md.append("")

# Sort files by importance
priority_files = [
    "scratch/run_qualification_and_holdout.py",
    "scratch/qualification_and_holdout_results.json",
    "scratch/run_margin_scan.py",
    "scratch/v2_dmitrii_margin_scan.json",
    "scratch/run_slack_qualification.py",
    "scratch/run_v3_statistical_validation.py",
    "scratch/audit2_1_recompute_v2_stats.py",
    "scratch/jit_melon_results/dev_tournament_results.json",
    "scratch/final_500seed_qualification_results.json",
    "scratch/fresh_holdout_200seeds_results.json",
    "scratch/exact_accounting_200seeds_results.json",
    "DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md",
    "DEVELOPMENT_GATE_0_2_HOLDOUT_PROVENANCE.md",
    "AUDIT2_1_STATISTICAL_AUDIT.md",
]

for f in priority_files:
    f_hits = [h for h in hits if h["file"].replace("\\", "/") == f]
    f_rhits = [rh for rh in range_hits if rh["file"].replace("\\", "/") == f]
    if not f_hits and not f_rhits:
        continue
    
    first_content = (f_hits[0]["content"] if f_hits else f_rhits[0]["content"])
    cat, cat_desc = classify_hit(f, first_content, is_range=bool(f_rhits))
    
    md.append(f"#### `{f}`")
    md.append(f"- **Classification**: **Category {cat}** ({cat_desc})")
    if f_rhits:
        for rh in f_rhits:
            md.append(f"- **Range Overlap**: Line {rh['line']}: `range({rh['start']}, {rh['end']})`")
            ctx = get_surrounding_context(rh["file"], rh["line"], context_lines=2)
            md.append(f"```python\n{ctx}\n```")
    if f_hits:
        md.append(f"- **Individual Seed Matches**: {len(f_hits)} occurrences")
        sample_hits = f_hits[:3]
        for sh in sample_hits:
            md.append(f"- Seed {sh['seed']} at Line {sh['line']}:")
            ctx = get_surrounding_context(sh["file"], sh["line"], context_lines=1)
            md.append(f"```text\n{ctx}\n```")
    md.append("")

md.append("---")
md.append("")
md.append("## 6. Action Mandate")
md.append("")
md.append("1. **Strict Rejection**: Seeds `50100–50149` CANNOT be used as the Discovery partition for EXP-DEV-003.")
md.append("2. **Next Action Required**: Execute a clean provenance discovery search to find a completely pristine 50-seed block (e.g. within an unsimulated range such as `60000..60049`, `70000..70049`, or `80000..80049`) that has zero git history hits, zero simulation script references, zero result entries, and zero protocol citations.")
md.append("3. **Stop Invariant**: Stand down and request user review of `SEED_PROVENANCE.md` prior to selecting the replacement virgin partition.")
md.append("")

content_str = "\n".join(md)
with open(PROV_FILE, "w", encoding="utf-8") as out:
    out.write(content_str)

print(f"Created {PROV_FILE} successfully ({len(content_str)} bytes)")
