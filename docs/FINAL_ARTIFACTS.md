# Kagriculture Final Competition Artifacts

This document records the authoritative final submissions, highest-performing candidate agents, teammate artifacts, and build integrity verification checksums for the Kagriculture project.

---

## 1. Incumbent Production Submission (Final Agent)

- **Agent Name**: **V49 Meta Fusion**
- **Canonical Source Path**: [`candidates/v49_meta_fusion/main.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/v49_meta_fusion/main.py)
- **Packaged Submission Path**: [`submissions/v49_meta_fusion_submission/main.py`](file:///c:/Users/Sundareswaran/Kagriculture/submissions/v49_meta_fusion_submission/main.py)
- **Archive File**: [`submissions/v49_meta_fusion_20260929_2212.zip`](file:///c:/Users/Sundareswaran/Kagriculture/submissions/v49_meta_fusion_20260929_2212.zip)
- **SHA256 (main.py)**: `8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11`
- **SHA256 (ZIP bundle)**: `37F10DEE73C7E01BE1FE240FBFC5344F254D2FE29FB0764FB14B2C69AB99306D`
- **Submission Status**: **SUBMITTED & LOCKED AS INCUMBENT**
- **Environment Specification**: `kaggle-environments == 1.32.7`, Python 3.11/3.12 (A100/Kaggle Runtime)
- **Performance Benchmark**:
  - **99.31% Win Rate** across 576 fresh validation legs (572W / 4L / 0T / 0 casualties).
  - **100% Win Rate** against the August 3100+ public elite replay corpus (400/400 legs).
  - **92.19% Panel Win Rate** against diverse adversarial test gauntlets.
- **Key Mechanisms**:
  1. *2945 Base Chassis*: High-throughput, deterministic micro-choreography with cow->goose and shed-room guard.
  2. *V44 CapEx Cutoff*: Strict step >= 520 capital expenditure guard forbidding animal and land purchases.
  3. *V48 Surgical Overrides*: Route 105 selectively activated for Brunch/Farmers, Bakery/Brunch, and PetCafe/Farmers shop combinations.
  4. *V49 E402 Late Seed-Cap Overlay*: Strict upper bound on `BUY_SEED` for wheat and carrots after step 624 to prevent stranded inventory.
- **Known Limitations**:
  - Exactly 4 losses observed across 576 matches, isolated to seeds 250617 and 250621 against V44 at step 697 due to a lockstep market queue collision in the synchronous transaction interpreter. Forensic analysis in V56/V57 confirmed that attempted queue padding interventions induced negative alpha on control seeds, making the V49 baseline Pareto-optimal.

---

## 2. Best Teammate Submissions

### A. Teammate Vj Culture v24
- **Archive Path**: [`team_submissions/submission_Vj_kc_v24.tar.gz`](file:///c:/Users/Sundareswaran/Kagriculture/team_submissions/submission_Vj_kc_v24.tar.gz)
- **SHA256**: `4C9EF1DC189DE6185AFADE682CB8A758139390E4BAA8B6A010500443C75BD5CE`
- **Evaluation**: Proved superior to Vj_kc_v27 by +500 cash margin and 7/8 head-to-head wins due to `room_guard`, `dead_stock`, PET_CAFE tilt, and stranded wheat pickup fix.
- **Status**: Preserved as benchmark control and teammate baseline.

### B. Teammate Vj Culture v27
- **Archive Path**: [`team_submissions/submission_Vj_kc_v27.tar.gz`](file:///c:/Users/Sundareswaran/Kagriculture/team_submissions/submission_Vj_kc_v27.tar.gz)
- **SHA256**: `EEE5AD4D7C67B27D7713E70B4B9E56220E92A8E8B90E6C59656A93ECE74B9A6C`
- **Evaluation**: Disabling room_guard and dead_stock in this variant caused sheep worker starvation on stranded wheat, losing 55.2 cash per game compared to v24.

---

## 3. Earlier Milestone Submissions

### A. V35 Production Milestone
- **Archive Path**: [`final_submission/V35_FINAL_SUBMISSION.tar.gz`](file:///c:/Users/Sundareswaran/Kagriculture/final_submission/V35_FINAL_SUBMISSION.tar.gz)
- **SHA256**: `9D2DB0C688E127BA3526008BBE08D09B28FBFE389D11A8FADA16606EC1ADC9FA`
- **Agent Code**: [`submission_final_v35/main.py`](file:///c:/Users/Sundareswaran/Kagriculture/submission_final_v35/main.py) (SHA256: `92B29C3CE75F2306...`)
- **Significance**: Official mid-competition submission featuring A7 opening wash controller.

### B. V22R1 Baseline Release
- **Git Commit**: `33763a8` (tagged base for V23–V26 research branches)
- **Significance**: Stable baseline release prior to modern meta-route restructuring.

---

## 4. Evaluated Post-V49 Research Prototypes

| Prototype | Location | SHA256 | Outcome | Reason |
| :--- | :--- | :--- | :---: | :--- |
| **Final Meta Synthesis** | `research/final_synthesis/final_candidate/main.py` | `076AB444...` | REJECTED | Severe panel generalization drop (48.9% WR vs V49's 92.2%). |
| **V50 Dead Action Guard** | `candidates/v50_dead_action_guard/main.py` | `E3DC43B5...` | REJECTED | Fertilizer suppression starved late crops and slashed terminal payouts. |
| **V51 Blocked Action Repair** | `candidates/v51_blocked_repair/main.py` | `1F0E9222...` | REJECTED | Weed repair buffer fired 0 times across 92k turns; inert on 2945 chassis. |

---

## 5. Standalone Execution of Incumbent (V49)

To test the final agent locally with `kaggle-environments`:
```bash
python -c "
from kaggle_environments import make
env = make('kaggriculture', configuration={'episodeSteps': 700})
env.run(['candidates/v49_meta_fusion/main.py', 'candidates/v49_meta_fusion/main.py'])
print('Match complete. Rewards:', [agent.reward for agent in env.state])
"
```
