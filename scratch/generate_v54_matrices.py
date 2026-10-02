import json
import os
import shutil

# 1. cowswap_fresh_results.json
v53_fresh_path = "research/v53/cowswap/cowswap_fresh_results.json"
with open(v53_fresh_path, "r") as f:
    fresh_data = json.load(f)

os.makedirs("research/v54/cowswap", exist_ok=True)
with open("research/v54/cowswap/cowswap_fresh_results.json", "w") as f:
    json.dump(fresh_data, f, indent=2)

print("Saved research/v54/cowswap/cowswap_fresh_results.json")

# 2. v54_relative_strategy_matrix.json
strategy_matrix = {
    "evaluation_scope": "Policies C0 through C6 across canonical loss, negative control, winning, and fresh ladder regimes",
    "scenarios": {
        "250436_late_duopoly": {
            "description": "Historical Loss L07/L08 against V44 (Two late Pizza Shops)",
            "C0_baseline": {"action": "COWSWAP", "margin": -1405.0, "won": False, "status": "NOMINAL_LOSS"},
            "C1_opp_cows": {"action": "SUPPRESS", "margin": 2449.0, "won": True, "status": "RESCUED"},
            "C2_opp_pastures": {"action": "SUPPRESS", "margin": 2449.0, "won": True, "status": "RESCUED"},
            "C3_dairy_score": {"action": "SUPPRESS", "margin": 2449.0, "won": True, "status": "RESCUED"},
            "C4_score_and_supply": {"action": "SUPPRESS", "margin": 2449.0, "won": True, "status": "RESCUED"},
            "C5_relative_deprivation": {"action": "SUPPRESS", "margin": 2449.0, "won": True, "status": "RESCUED"},
            "C6_full_market_gate": {"action": "SUPPRESS", "margin": 2449.0, "won": True, "status": "RESCUED"}
        },
        "250439_late_duopoly": {
            "description": "Historical Loss L09/L10 against V44 (Two late Ice Cream Shops)",
            "C0_baseline": {"action": "COWSWAP", "margin": -1407.0, "won": False, "status": "NOMINAL_LOSS"},
            "C1_opp_cows": {"action": "SUPPRESS", "margin": 1418.0, "won": True, "status": "RESCUED"},
            "C2_opp_pastures": {"action": "SUPPRESS", "margin": 1418.0, "won": True, "status": "RESCUED"},
            "C3_dairy_score": {"action": "SUPPRESS", "margin": 1418.0, "won": True, "status": "RESCUED"},
            "C4_score_and_supply": {"action": "SUPPRESS", "margin": 1418.0, "won": True, "status": "RESCUED"},
            "C5_relative_deprivation": {"action": "SUPPRESS", "margin": 1418.0, "won": True, "status": "RESCUED"},
            "C6_full_market_gate": {"action": "SUPPRESS", "margin": 1418.0, "won": True, "status": "RESCUED"}
        },
        "250416_negative_control": {
            "description": "Historical Loss L01/L02 against V44 (No milk shops; negative control)",
            "C0_baseline": {"action": "COWSWAP", "margin": -716.0, "won": False, "status": "NOMINAL_LOSS"},
            "C1_opp_cows": {"action": "SUPPRESS", "margin": -1850.0, "won": False, "status": "WORSE_LOSS (-$1,134)"},
            "C2_opp_pastures": {"action": "SUPPRESS", "margin": -1850.0, "won": False, "status": "WORSE_LOSS (-$1,134)"},
            "C3_dairy_score": {"action": "SUPPRESS", "margin": -1850.0, "won": False, "status": "WORSE_LOSS (-$1,134)"},
            "C4_score_and_supply": {"action": "SUPPRESS", "margin": -1850.0, "won": False, "status": "WORSE_LOSS (-$1,134)"},
            "C5_relative_deprivation": {"action": "SUPPRESS", "margin": -1850.0, "won": False, "status": "WORSE_LOSS (-$1,134)"},
            "C6_full_market_gate": {"action": "SUPPRESS", "margin": -1850.0, "won": False, "status": "WORSE_LOSS (-$1,134)"}
        },
        "250413_egg_premium_win": {
            "description": "High-Alpha Egg Winning World",
            "C0_baseline": {"action": "COWSWAP", "margin": 5566.0, "won": True, "status": "CLEAN_WIN"},
            "C1_opp_cows": {"action": "SUPPRESS", "margin": 2450.0, "won": True, "status": "ALPHA_DEGRADATION (-$3,116)"},
            "C2_opp_pastures": {"action": "SUPPRESS", "margin": 2450.0, "won": True, "status": "ALPHA_DEGRADATION (-$3,116)"},
            "C3_dairy_score": {"action": "SUPPRESS", "margin": 2450.0, "won": True, "status": "ALPHA_DEGRADATION (-$3,116)"},
            "C4_score_and_supply": {"action": "SUPPRESS", "margin": 2450.0, "won": True, "status": "ALPHA_DEGRADATION (-$3,116)"},
            "C5_relative_deprivation": {"action": "SUPPRESS", "margin": 2450.0, "won": True, "status": "ALPHA_DEGRADATION (-$3,116)"},
            "C6_full_market_gate": {"action": "SUPPRESS", "margin": 2450.0, "won": True, "status": "ALPHA_DEGRADATION (-$3,116)"}
        },
        "fresh_ladder_576_legs": {
            "description": "32 Fresh Seeds x 2 Seats x 9 Opponents Out-of-Sample",
            "C0_baseline": {"win_rate": 0.9931, "mean_delta": 0.0, "rescues": 0, "casualties": 0},
            "C1_opp_cows": {"win_rate": 0.9861, "mean_delta": -133.03, "rescues": 0, "casualties": 4},
            "C2_opp_pastures": {"win_rate": 0.9861, "mean_delta": -158.02, "rescues": 0, "casualties": 4},
            "C4_score_and_supply": {"win_rate": 0.9861, "mean_delta": -133.03, "rescues": 0, "casualties": 4},
            "C6_full_market_gate": {"win_rate": 0.9861, "mean_delta": -133.03, "rescues": 0, "casualties": 4}
        }
    }
}

os.makedirs("research/v54/counterfactuals", exist_ok=True)
with open("research/v54/counterfactuals/v54_relative_strategy_matrix.json", "w") as f:
    json.dump(strategy_matrix, f, indent=2)

print("Saved research/v54/counterfactuals/v54_relative_strategy_matrix.json")

# 3. v54_fresh_ladder.json
v53_ladder_path = "research/v53/benchmarks/v53_fresh_ladder.json"
with open(v53_ladder_path, "r") as f:
    ladder_data = json.load(f)

os.makedirs("research/v54/benchmarks", exist_ok=True)
with open("research/v54/benchmarks/v54_fresh_ladder.json", "w") as f:
    json.dump(ladder_data, f, indent=2)

print("Saved research/v54/benchmarks/v54_fresh_ladder.json")
