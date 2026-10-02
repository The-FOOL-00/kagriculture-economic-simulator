# V37 Cleanroom Execution Test

## 1. Execution Context

- **Execution Directory (CWD)**: `submission_final_v35/`
- **Module Loaded**: `main.py`
- **Environment**: Isolated cleanroom execution without repository root on `PYTHONPATH` or `sys.path`.
- **Target Evaluation Seed**: `249675` (Safe internal development cohort, non-holdout).

---

## 2. Verification Steps & Log Output

### Step 1: Agent Import & Callable Check
- `import main` loaded cleanly.
- `assert callable(main.agent)` passed.
- No `ModuleNotFoundError`, no relative path errors, no missing dependencies.

### Step 2: Observation 0 Execution
- First observation (`step = 0`) processed.
- Market action verified:
  ```json
  {"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]]}
  ```
- Opening intervention verified exactly at 25/25 wash.

### Step 3: Observation 1..718 Execution
- Subsequent observation (`step = 1`) processed without error.
- Full 720-step episode executed under `kaggle_environments`.

### Step 4: Episode Result
- **Steps Simulated**: 720 / 720
- **Terminal Cash**: $144,114.00
- **Opponent Cash**: $3,000.00
- **Outcome**: WIN
- **Status**: **PASS**

---

## 3. Cleanroom Verdict

**PASS**. The candidate executes cleanly from within the isolated staging directory with zero missing dependencies and valid Kaggle action schema.
