# Kaggle Execution Guide: EXP-ARCH-002 H1 Dominance Terminal

This guide provides the complete, manual step-by-step instructions for uploading and running the prospective **EXP-ARCH-002_H1_DOMINANCE_TERMINAL** experiment in a Kaggle Notebook using Kaggle's GPU T4 × 2 compute environment.

> [!IMPORTANT]
> **Zero Kaggle CLI Required**: This procedure uses the Kaggle web UI directly and does not depend on `kaggle auth login` or the Kaggle CLI.

---

## 1. Create a New Kaggle Notebook
1. Navigate to [kaggle.com/code](https://www.kaggle.com/code) in your browser.
2. Click **New Notebook**.
3. In the Notebook editor, click the **Settings** / **Notebook Options** panel (three dots in upper right or right sidebar).

---

## 2. Select Hardware Accelerator: GPU T4 × 2
1. In the **Accelerator** dropdown, select:
   ```
   GPU T4 × 2
   ```
2. Verify that **Persistence** is enabled (optional, but recommended).
3. Verify that **Internet** is turned on (or off; the experiment runs entirely offline without network access).

---

## 3. Upload the Prepared Source Bundle
You have two simple upload options:

### Option A: Upload as a Kaggle Dataset (Recommended)
1. Go to [kaggle.com/datasets](https://www.kaggle.com/datasets) -> **New Dataset**.
2. Drag and drop `kaggle_arch002_source.tar.gz` (or the contents of `kaggle_arch002_bundle/source/`).
3. Title the dataset: `kagriculture-arch002-source`.
4. Click **Create**.
5. Back in your Kaggle Notebook, click **+ Add Input** (top right) -> Select `kagriculture-arch002-source`.
   The dataset will appear mounted at `/kaggle/input/kagriculture-arch002-source/`.

### Option B: Direct Upload via Notebook File Browser
1. In the notebook file browser pane (left sidebar), click **Upload** and upload `kaggle_arch002_source.tar.gz` directly into `/kaggle/working/`.

---

## 4. Open the Prepared Notebook
1. In your Kaggle notebook, click **File** -> **Import Notebook** (or upload `kaggle_arch002_bundle/notebook/arch002_h1_kaggle.ipynb`).
2. Alternatively, open the local `arch002_h1_kaggle.ipynb` in any text editor, or upload it to Kaggle.

---

## 5. Canonical Working Root
The notebook is hardwired to use:
```python
/kaggle/working/Kagriculture
```
as the canonical project root.

Cell 3 (**SOURCE INSTALLATION**) automatically locates the uploaded source (whether in `/kaggle/input/` or `/kaggle/working/`), extracts or copies the files to `/kaggle/working/Kagriculture`, switches the working directory, and asserts:
```python
assert Path.cwd() == Path("/kaggle/working/Kagriculture")
```

---

## 6. Execution Workflow: Automated Gates
Run the notebook from the first cell (**Run All** or execute cell-by-cell):

1. **RUN IDENTITY**: Displays experiment metadata, cohort `320000–320499`, and 1,000 intended games.
2. **KAGGLE ENVIRONMENT**: Detects Python version, OS, vCPUs, RAM, and NVIDIA Tesla T4 × 2 GPUs. Records simulator CPU execution mode.
3. **SOURCE INSTALLATION**: Unpacks source bundle into `/kaggle/working/Kagriculture`.
4. **HASH VERIFICATION**: G-HASH check verifying bit-identity of baseline, preregistration, H1 modules, runner, and unit model.
5. **DEPENDENCY VERIFICATION**: Confirms pure-Python simulator and agent imports.
6. **SIMULATOR VERIFICATION**: Asserts `kagsim_py` engine 1.32.7 port.
7. **RUNNER INTEGRITY**: Asserts quarantine boundaries (holdout 214200–214249, DEV-007 310000–310499). Executes Phase G re-execution validation suite.
8. **PRE-ENTRY PURITY TEST**: Runs consumed seeds (248000–248002) proving zero double-calls and 100% pre-E action identity.
9. **TERMINAL-WINDOW TEST**: Verifies micro-transitions around steps 710–718.
10. **MEMORY / WORKER CONFIGURATION**: Allocates 4 worker processes matching Kaggle vCPUs, sets up continuous incremental checkpointing to `/kaggle/working/Kagriculture/experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/kaggle_execution/`.

> [!CAUTION]
> **Fail-Safe Gate**: If any preflight check (hashes, quarantine, purity, simulator) fails, execution **STOPS IMMEDIATELY** before running a single prospective seed.

---

## 7. Prospective Execution (The Real Run)
Once all preflight gates pass, the notebook automatically proceeds to Section 11 (**PROSPECTIVE EXECUTION**):
- Executes seeds `320000` to `320499` (N = 500 seeds, 2 games per seed = 1,000 total games).
- Common Random Numbers (CRN) treatment vs baseline in both seat permutations.
- Real-time progress logging every 10 seeds.
- Incremental checkpointing: if disconnected, rerunning the cell automatically resumes from the last completed seed.
- Expected execution time on Kaggle 4-vCPU runtime: ~20 to 35 minutes.

---

## 8. Post-Execution Analysis & Download
After all 1,000 games complete:
1. Section 13 validates complete execution integrity (exactly 500 unique seeds, 1,000 games, zero duplicates, zero holdout leakage, 100% P-PURE pass).
2. Section 14 performs preregistered statistical analysis (activation rate, reason codes, paired delta mean, 95% CI, p-values).
3. Section 15 generates the final report and output archive:
   ```
   ARCH002_KAGGLE_RESULTS_<timestamp>.tar.gz
   ```
4. Download the generated `.tar.gz` archive from `/kaggle/working/` to your local machine.
