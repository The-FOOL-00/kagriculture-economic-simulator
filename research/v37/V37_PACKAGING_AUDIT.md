# V37 Packaging Audit: Kaggle / Kaggriculture Submission Conventions

## 1. Executive Summary & Verification Context

This document establishes the repository-validated submission packaging conventions for the Kaggle Kaggriculture competition, based on:
1. Official Kaggle environment documentation (`env_backup_1_30_1/AGENTS.md`)
2. Historical successful submission archives (`submission_a7_v30.tar.gz`, `submission_aec_v22r1.tar.gz`, `submission_Vj_kc_v3.tar.gz`)
3. Historical build and packaging scripts (`scripts/v30_build_a7_standalone.py`, `scripts/v30_package_a7.py`)
4. Verified execution rules and container sandbox constraints

---

## 2. Competition Submission Specification

### 2.1 Entry Point Specification
- **Required Filename**: `main.py`
- **Required Callable**: `agent(observation, configuration=None)` (or `agent(observation)` with optional `configuration`).
- **Signature & Return Type**:
  - Input: `observation` (`dict`), `configuration` (`dict` or `None`).
  - Output: `dict` conforming strictly to schema:
    ```python
    {
        "farmer": list,   # e.g., ["PASS"], ["MOVE", "NORTH"], etc.
        "hands": list,    # list of hand actions, e.g. [["PASS"]]
        "market": list    # max 10 market orders, e.g. [["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]]
    }
    ```
- **Fallback Requirement**: Fail-closed safe response `{"farmer": ["PASS"], "hands": [], "market": []}` on any unhandled exception.

### 2.2 Archive & Packaging Format
- **Archive Format**: `.tar.gz` (gzip-compressed POSIX tarball) or a standalone `.py` file.
- **Archive Root Layout**:
  - `main.py` MUST be located at the root of the archive (i.e. `./main.py` or `main.py`), NOT nested inside a subfolder.
  - Multi-file bundles are supported by Kaggle (`tar -czf submission.tar.gz main.py helper.py ...`), but standard practice in this repo is a standalone `main.py` packaged into `submission.tar.gz` to ensure zero-risk import resolution.
- **Historical Precedents**:
  - `submission_a7_v30.tar.gz` (143,296 bytes): Contains solely `['main.py']` (standalone compiled chassis embedding V3 and A7 30/30 rewrite).
  - `submission_Vj_kc_v3.tar.gz` (139,812 bytes): Contains `['._main.py', 'main.py']`.
  - `submission_aec_v22r1.tar.gz` (173,040 bytes): Contains multi-file `aec/` package with root `main.py`.

### 2.3 Dependency & Environment Constraints
- **Python Version**: Python 3.8+ (Kaggle simulation runner uses Python 3.10 / 3.11).
- **External Packages**: Only Python Standard Library and competition-provided packages (`kaggle_environments`) are guaranteed to exist in the execution sandbox.
- **Network Access**: NONE. The evaluation container has no internet access during match simulation.
- **Filesystem Constraints**: Submissions run in an isolated temporary directory (e.g. `/kaggle_simulations/agent/`). Code must NOT depend on absolute host paths (e.g. `c:/Users/...` or `/home/...`), nor assume parent directories exist relative to the submission root.

### 2.4 Extra Files & Metadata
- **Extra Files**: Permitted if referenced via relative imports from `main.py`, but extraneous files (research scripts, notebooks, datasets, test logs, git directories) increase archive size, trigger security flags, and increase failure risk.
- **Metadata**: No separate metadata JSON or manifest file is required by Kaggle; only the archive and the CLI description string.

### 2.5 Historical Build Commands
In V30 (`scripts/v30_package_a7.py`), the archive was built using Python `tarfile`:
```python
with tarfile.open(OUT, "w:gz") as tar:
    tar.add(CAND, arcname="main.py")
```
This guarantees canonical POSIX tar header creation without OS-specific metadata artifacts.

---

## 3. Packaging Decision for V35

- **Submission Structure**: **Option C** (`.tar.gz` archive containing self-contained `main.py` at root), which also serves as **Option A** (`main.py` standalone).
- **Target Archive Name**: `V35_FINAL_SUBMISSION.tar.gz` inside `final_submission/`.
- **Staging Directory**: `submission_final_v35/` containing clean production `main.py`.
- **Zero-Risk Invariance**: The production `main.py` will embed the frozen A7 standalone chassis (`candidates/v30_a7_standalone/main.py`) and apply the exact, validated V35 Step-0 25/25 opening intervention, guaranteeing 100% bit-identical actions to `candidates/v35_a7_opening/main.py` with zero filesystem or path vulnerabilities.
