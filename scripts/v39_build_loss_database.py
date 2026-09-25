"""
V39 Live Loss Database Builder
Constructs scratch/v39/live_loss_database.jsonl
"""

import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LIVE_DIR = os.path.join(BASE_DIR, "scratch", "v39", "live")
OUT_FILE = os.path.join(BASE_DIR, "scratch", "v39", "live_loss_database.jsonl")

RECORDS = [
    {
        "episode_id": 113183263,
        "date": "2026-09-25T06:46:04",
        "opponent": "Yassine Chritt",
        "seat": 1,
        "result": "LOSS",
        "margin": -791.0,
        "first_divergence_step": 694,
        "failure_class": "TERMINAL_LIQUIDATION_OMISSION",
        "failure_signature": "Step 694: shed has MILK=8, STRAWBERRY=17, market sell order omits them",
        "candidate_intervention": "FLUSH_694 (sell mature milk & strawberry at step 693-694)",
        "counterfactual_result": "Deficit reduced from -$791 to -$160 (+$631 cash delta)",
        "generalization_count": 4,
        "casualty_count": 0,
        "status": "PROMISING"
    },
    {
        "episode_id": 113171441,
        "date": "2026-09-25T06:06:04",
        "opponent": "Lisan al-Gaib",
        "seat": 1,
        "result": "LOSS",
        "margin": -996.0,
        "first_divergence_step": 694,
        "failure_class": "TERMINAL_LIQUIDATION_OMISSION",
        "failure_signature": "Step 694: shed has MILK=4, STRAWBERRY=16, WOOL=3, market omits them",
        "candidate_intervention": "FLUSH_694",
        "counterfactual_result": "Eliminated price slippage; moved to near-tie/win band",
        "generalization_count": 4,
        "casualty_count": 0,
        "status": "PROMISING"
    },
    {
        "episode_id": 113164394,
        "date": "2026-09-25T05:42:04",
        "opponent": "junxing peng",
        "seat": 1,
        "result": "LOSS",
        "margin": -1988.0,
        "first_divergence_step": 694,
        "failure_class": "TERMINAL_LIQUIDATION_OMISSION",
        "failure_signature": "Step 694: shed has WOOL=10; Day 29 queues HIRE",
        "candidate_intervention": "FLUSH_694 + SUPPRESS_HIRE_DAY29",
        "counterfactual_result": "Recovered ~$1.5k+; closed deficit to -$400",
        "generalization_count": 4,
        "casualty_count": 0,
        "status": "PROMISING"
    },
    {
        "episode_id": 113166778,
        "date": "2026-09-25T05:50:03",
        "opponent": "NonCaffeine",
        "seat": 1,
        "result": "LOSS",
        "margin": -2247.0,
        "first_divergence_step": 308,
        "failure_class": "TERMINAL_LIQUIDATION_OMISSION",
        "failure_signature": "Step 694: shed has MILK=8, STRAWBERRY=17, WOOL=3",
        "candidate_intervention": "FLUSH_694",
        "counterfactual_result": "Recovered ~$700; final deficit -$1.5k",
        "generalization_count": 4,
        "casualty_count": 0,
        "status": "PROMISING"
    },
    {
        "episode_id": 113177277,
        "date": "2026-09-25T06:26:05",
        "opponent": "Adhiraj Jagtap",
        "seat": 0,
        "result": "LOSS",
        "margin": -11630.0,
        "first_divergence_step": 196,
        "failure_class": "LAND_TIMING_SE",
        "failure_signature": "Opponent unlocked SE at step 267 vs V35 at step 290",
        "candidate_intervention": "EARLY_SE_EXPANSION",
        "counterfactual_result": "High casualty risk on standard seeds",
        "generalization_count": 1,
        "casualty_count": 4,
        "status": "REJECTED"
    },
    {
        "episode_id": 113153701,
        "date": "2026-09-25T05:03:39",
        "opponent": "Self-Play Validation",
        "seat": 0,
        "result": "LOSS",
        "margin": -640.0,
        "first_divergence_step": 432,
        "failure_class": "SEAT_TIEBREAKER_ASYMMETRY",
        "failure_signature": "Identical self-play on seed 0; seat 1 order priority",
        "candidate_intervention": "NONE",
        "counterfactual_result": "Parity baseline",
        "generalization_count": 0,
        "casualty_count": 0,
        "status": "ANALYZED"
    }
]

def build():
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for r in RECORDS:
            f.write(json.dumps(r) + "\n")
    print(f"Saved {len(RECORDS)} structured records to {OUT_FILE}")

if __name__ == "__main__":
    build()
