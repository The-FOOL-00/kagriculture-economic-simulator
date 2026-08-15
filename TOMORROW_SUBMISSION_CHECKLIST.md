# 📋 Kaggle Submission Checklist & Execution Status

---

## 🛑 Pre-Submission Verification
- [x] Golden Control `agents/golden_v1.py` verified immutable.
- [x] All 5 candidate files in `candidates/` validated with standalone syntax.
- [x] Automated release checker `python release_check.py` returns `RELEASE READY`.
- [x] Behavioral equivalence between modular engine and compiled `main.py` verified.
- [x] `submission.tar.gz` packaged and verified locally.

---

## 🚀 Execution Steps (Live Submissions)

### Step 1: Slot 1 — Control Baseline
- **File:** `candidates/slot1_titan_control.py`
- **Command:** `kaggle competitions submit -c kaggriculture -f candidates/slot1_titan_control.py -m "Slot 1: Titan Control Baseline (Live Reference)"`
- [x] **SUBMITTED** | **Submission ID:** `55519962` (Status: `PENDING`).

### Step 2: Slot 2 — High-Throughput Liquidation Challenger
- **File:** `candidates/slot2_loss_fix_challenger.py`
- **Command:** `kaggle competitions submit -c kaggriculture -f candidates/slot2_loss_fix_challenger.py -m "Slot 2: High-Throughput Liquidation Challenger (12-14 Batch Sell)"`
- [x] **SUBMITTED** | **Submission ID:** `55519966` (Status: `PENDING`).

### Step 3: Slot 3 — Opponent-Adaptive Challenger
- **File:** `candidates/slot3_opponent_adaptive.py`
- [ ] *(Held per user directive: slots 1 and 2 only)*

### Step 4: Slot 4 — Market Planner Challenger
- **File:** `candidates/slot4_market_planner.py`
- [ ] *(Held per user directive: slots 1 and 2 only)*

### Step 5: Slot 5 — Local Champion (Titan Apex v4)
- **File:** `main.py` / `candidates/slot5_local_champion.py`
- [ ] *(Held per user directive: slots 1 and 2 only)*

---

## 📈 Post-Submission Protocol
1. **DO NOT** modify code or submit further versions immediately.
2. Allow matchmaking ladder episodes to accumulate (minimum 10–20 matches per candidate).
3. Run `python analyze_live_submissions.py` to download episode logs and evaluate Elo trajectories.
