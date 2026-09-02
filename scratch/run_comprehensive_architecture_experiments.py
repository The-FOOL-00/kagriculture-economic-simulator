import os
import sys
import json
import time
import numpy as np
from kaggle_environments import make

def run_experiments():
    seeds = [1001, 2024, 3037, 4099, 5012, 6077, 7088, 8099, 9011, 12345]
    print(f"Running tournament across {len(seeds)} seeds, both seats P0 and P1 (20 paired games per matchup)...")

    # Load agent modules
    agents_to_test = {
        'Aethel_V1': 'replays/raw/reference_agents/closer_cleo.py',
        'Broker_Bea': 'replays/raw/reference_agents/broker_bea.py',
        'Rancher_Rita': 'replays/raw/reference_agents/rancher_rita.py',
        'Ledger_Lena': 'replays/raw/reference_agents/ledger_lena.py',
        'Slotter_Silas': 'replays/raw/reference_agents/slotter_silas.py',
        'Melon_Mateo': 'replays/raw/reference_agents/melon_mateo.py',
        'Fallow_Finn': 'replays/raw/reference_agents/fallow_finn.py',
        'Wheat_Walter': 'replays/raw/reference_agents/wheat_walter.py'
    }

    # Also check if hybrid_8c4s exists
    if os.path.exists('candidates/slot5_hybrid_8c4s.py'):
        agents_to_test['Hybrid_8c4s'] = 'candidates/slot5_hybrid_8c4s.py'
    if os.path.exists('agents/hybrid_8c4s_15m_feed_insulated.py'):
        agents_to_test['Hybrid_8c4s_Insulated'] = 'agents/hybrid_8c4s_15m_feed_insulated.py'
    if os.path.exists('candidates/slot2_hybrid_6c3s_10m.py'):
        agents_to_test['Hybrid_6c3s'] = 'candidates/slot2_hybrid_6c3s_10m.py'

    matchup_results = {}

    control_agent = agents_to_test['Aethel_V1']

    for opp_name, opp_path in agents_to_test.items():
        if opp_name == 'Aethel_V1':
            continue
        print(f"\nEvaluating Aethel_V1 vs {opp_name}...")
        scores_aethel = []
        scores_opp = []
        wins_aethel = 0
        wins_opp = 0
        ties = 0
        margins = []

        for seed in seeds:
            for p_seat in [0, 1]:
                agents = [control_agent, opp_path] if p_seat == 0 else [opp_path, control_agent]
                env = make('kaggriculture', configuration={'seed': seed}, debug=False)
                env.run(agents)
                last_step = env.steps[-1]
                r0 = last_step[0]['reward'] or 0
                r1 = last_step[1]['reward'] or 0
                
                aethel_score = r0 if p_seat == 0 else r1
                opp_score = r1 if p_seat == 0 else r0
                margin = aethel_score - opp_score
                
                scores_aethel.append(aethel_score)
                scores_opp.append(opp_score)
                margins.append(margin)
                
                if margin > 0:
                    wins_aethel += 1
                elif margin < 0:
                    wins_opp += 1
                else:
                    ties += 1

        total_games = len(margins)
        win_rate = (wins_aethel / total_games) * 100
        mean_margin = float(np.mean(margins))
        median_margin = float(np.median(margins))
        
        matchup_results[opp_name] = {
            'total_games': total_games,
            'aethel_wins': wins_aethel,
            'opp_wins': wins_opp,
            'ties': ties,
            'win_rate_pct': win_rate,
            'mean_aethel_score': float(np.mean(scores_aethel)),
            'mean_opp_score': float(np.mean(scores_opp)),
            'mean_margin': mean_margin,
            'median_margin': median_margin,
            'min_margin': float(np.min(margins)),
            'max_margin': float(np.max(margins))
        }
        print(f"Result vs {opp_name}: {wins_aethel}W - {wins_opp}L - {ties}T ({win_rate:.1f}% Win Rate) | Mean Margin: {mean_margin:+.1f} | Median: {median_margin:+.1f}")

    out_file = r'scratch\comprehensive_arena_results_fresh.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(matchup_results, f, indent=2)
    print(f"\nSaved all tournament results to {out_file}")

if __name__ == '__main__':
    run_experiments()
