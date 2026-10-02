# V37 Dependency Closure Audit

## 1. Import Trace of Development Candidate (`candidates/v35_a7_opening/main.py`)

A recursive dependency walk of `candidates/v35_a7_opening/main.py` yields the following import graph:

```text
candidates/v35_a7_opening/main.py
├── __future__ (Standard Library)
├── copy (Standard Library)
├── os (Standard Library)
├── sys (Standard Library)
├── typing (Standard Library)
└── scripts.v32_common (Repository-Local Research Module)
    ├── copy, hashlib, json, os, sys, uuid (Standard Library)
    ├── candidates/v30_a7_standalone/main.py (Repository-Local Agent Chassis via FileAgent)
    │   ├── hashlib, os, tarfile (Standard Library)
    │   └── _V3_SRC (Embedded byte string of V3 engine)
    ├── aec.backbone.v27_ablation_adapters (Unnecessary Research Dependency)
    ├── aec.backbone.v25_p3_adapter (Unnecessary Research Dependency)
    ├── aec.backbone.v3_adapter (Unnecessary Research Dependency)
    ├── aec.backbone.v31r2_wash_adapter (Unnecessary Research Dependency)
    └── kaggle_environments (Runtime-provided Competition Package)
```

---

## 2. Dependency Classification Table

| Component | Nature / Source | In Dev Candidate? | Required for Production? | Production Staging Strategy |
| :--- | :--- | :---: | :---: | :--- |
| `copy`, `os`, `sys`, `typing` | Standard Library | Yes | **Yes** | Native Python stdlib (zero install needed) |
| `scripts.v32_common` | Repository-Local Harness | Yes | **No** (Research Only) | Eliminated by self-contained embedding |
| `aec.backbone.*` | Repository-Local Harness | Indirect | **No** (Research Only) | Eliminated |
| `kaggle_environments` | Runtime Sandbox | Indirect | **Provided by Kaggle** | Provided by host evaluation environment |
| `candidates/v30_a7_standalone` | Verified A7 Chassis | Indirect | **Yes** (Chassis Logic) | Embedded verbatim in production `main.py` |
| V3 Engine (`_V3_SRC`) | Base Engine Source | Indirect | **Yes** (Game Dynamics) | Pre-embedded inside A7 chassis |

---

## 3. Production Staging Closure Architecture

To satisfy Kaggle competition sandbox requirements and eliminate all path-resolution vulnerabilities:
1. The production bundle packages a self-contained `main.py` in `submission_final_v35/`.
2. The verified A7 standalone chassis (`candidates/v30_a7_standalone/main.py`, SHA-256 `51c1d25245f6...`) is embedded verbatim as `_A7_SRC` inside production `main.py`.
3. The V35 25/25 opening controller wraps `_A7_AGENT` directly in memory without file system operations.
4. **Resulting Dependency Count**: 0 external packages, 0 repository-local files, 0 filesystem lookups. Pure Standard Library closure.
