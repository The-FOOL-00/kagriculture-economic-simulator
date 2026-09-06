import sys, os
sys.path.insert(0, os.path.abspath("."))
import numpy as np
from kaggle_environments import make
import scratch.v2_jit_melon_experiment as exp
import opponents.live_flooder_v1 as lf

print("=== TESTING CANDIDATE H VS TOP-META & BENCHMARKS ===")
for opp_key, opp_name in [("live_flooder", "LiveFlooder_V1"), ("starter", "Starter_Baseline")]:
    margins = []
    wins = []
    scores_h = []
    scores_opp = []
    for s in [42, 100, 2026, 777, 999]:
        for swapped in [False, True]:
            res = exp.run_single_game(("H", opp_key, s, swapped))
            margins.append(res["margin"])
            wins.append(res["win"])
            scores_h.append(res["reward_us"])
            scores_opp.append(res["reward_opp"])
    print(f"Vs {opp_name:18s}: WinRate={np.mean(wins)*100:5.1f}% | CandScore=${np.mean(scores_h):,.1f} | OppScore=${np.mean(scores_opp):,.1f} | Margin=${np.mean(margins):+,.1f}")
