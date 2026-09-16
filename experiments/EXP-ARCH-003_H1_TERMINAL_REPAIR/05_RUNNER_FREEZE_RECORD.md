# EXP-ARCH-003_H1_TERMINAL_REPAIR — Runner Freeze Record

**Experiment ID:** EXP-ARCH-003_H1_TERMINAL_REPAIR  
**Runner Path:** `experiments/EXP-ARCH-003_H1_TERMINAL_REPAIR/run_arch003_execution.py`  
**Runner SHA-256:** `ece9c80f01b2c1ba1c3091a7409c26783e98810861caf431e2d652e382ff3426`  
**Date Frozen:** 2026-09-16  
**Status:** FROZEN — PENDING REVIEW PRIOR TO ANY PROSPECTIVE EXECUTION  

---

## 1. Runner Architecture & Protocol

The ARCH-003 runner `run_arch003_execution.py` is an authoritative, self-contained CRN evaluation harness designed specifically for the repaired terminal optimizer:

1. **Exact 2-Game CRN Evaluation per Seed:**
   - Game 0: Treatment on Seat 0 (`p0 = Treatment`), Baseline on Seat 1 (`p1 = Baseline`).
   - Game 1: Baseline on Seat 0 (`p0 = Baseline`), Treatment on Seat 1 (`p1 = Treatment`).
   - Both seats observe identical random game environments, engine step progressions, and market boards.

2. **Single-Invocation Execution Flow (No Baseline Double-Call Defect):**
   - Each agent is called exactly once per turn per seat:
     ```python
     action = agents[p](obs_p, config)
     ```
   - No duplicate calls to the baseline policy occur on either baseline seats or treatment seats.
   - Live telemetry and step accounting are preserved with zero divergence.

3. **Memory & State Isolation:**
   - Independent game engine instances per game (`Kagriculture(configuration=..., seed=seed)`).
   - Independent treatment agents instantiated per game (`build_agent(base)`).
   - Live baseline controllers reloaded per game (`load_baseline()`), eliminating any cross-game ledger or state persistence.

---

## 2. Hardened Quarantine Guardrails

The runner strictly enforces the following programmatic guardrails at startup:

1. **Cohort Boundary Guardrail:**
   ```python
   DEFAULT_START_SEED = 330000
   DEFAULT_END_SEED = 330499  # Inclusive
   ```
   If `--seed-start` or `--seed-end` fall outside `[330000, 330499]`, or touch the holdout seeds `[214200, 214249]`, execution aborts immediately with a safety violation.

2. **Frozen Baseline Cryptographic Check:**
   The runner calculates the SHA-256 hash of `candidates/compiled_v54_plus_residual.py` and asserts:
   ```python
   V54_PLUS_PLUS_SHA256 = "5ef81e4b8bb26c483a65191cf078a6aafe4d8721ad30303bfa82e850b924ea10"
   ```
   Execution refuses to start if any modification is detected.

3. **Output Directory Cleanliness:**
   The runner requires an unpolluted destination directory. If `--output-dir` contains previous run logs, it will not overwrite them unless explicitly instructed.

---

## 3. Output Schema & Artifacts

Upon authorized execution, the runner will produce:
- `game_records.jsonl`: Step-by-step game summary per seat, final money, final score, units sold, and activation indicators.
- `paired_deltas.csv`: Paired CRN delta table per seed ($s, \Delta_{\text{score}}, \Delta_{\text{money}}, \text{Act}_0, \text{Act}_1$).
- `telemetry_events.csv`: Detailed event logs of all candidate search evaluations, acceptance determinations, and step-718 market liquidations.
- `summary.json`: Aggregated activation rates, paired win rates, Wilcoxon signed-rank test statistics, and overflow counts.

---

## 4. Current Execution Status

- **Status:** FROZEN.
- **Prospective Runs Completed:** ZERO (0/500 seeds executed).
- **Authorized Next Step:** Code review and user approval.
