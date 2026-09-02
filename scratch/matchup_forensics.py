import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# Load Leaderboard mapping
lb_df = pd.read_csv("scratch/leaderboard_csv/kaggriculture-publicleaderboard-2026-09-02T12_38_23.csv")
lb_map = {}
for idx, row in lb_df.iterrows():
    lb_map[row['TeamId']] = {
        'rank': idx + 1,
        'teamName': row['TeamName'],
        'score': float(row['Score']),
        'submissionCount': row['SubmissionCount']
    }

def analyze_submission_episodes(sub_id, sub_name):
    ep_file = f"scratch/episodes_{sub_id}.json"
    if not os.path.exists(ep_file):
        print(f"File not found: {ep_file}")
        return None
    with open(ep_file, "r", encoding="utf-8") as f:
        episodes = json.load(f)
    
    print(f"\n================================================================================")
    print(f"EPISODE FORENSICS: {sub_name} (Submission ID: {sub_id})")
    print(f"Total Episodes Loaded: {len(episodes)}")
    print(f"================================================================================")
    
    parsed = []
    for ep in episodes:
        ep_id = ep.get('id')
        create_time = ep.get('createTime')
        agents = ep.get('agents', [])
        if len(agents) < 2:
            continue
        
        # Identify our agent and opponent
        our_agent = None
        opp_agent = None
        for a in agents:
            if a.get('submissionId') == sub_id:
                our_agent = a
            else:
                opp_agent = a
                
        if not our_agent or not opp_agent:
            continue
            
        our_reward = our_agent.get('reward')
        opp_reward = opp_agent.get('reward')
        
        if our_reward is None or opp_reward is None:
            # Game incomplete or error
            continue
            
        our_index = our_agent.get('index', 0)
        opp_team_id = opp_agent.get('teamId')
        opp_team_name = opp_agent.get('teamName')
        opp_sub_id = opp_agent.get('submissionId')
        
        opp_meta = lb_map.get(opp_team_id, {'rank': 9999, 'score': 0.0, 'teamName': opp_team_name})
        
        margin = our_reward - opp_reward
        win = 1 if margin > 0 else (0.5 if margin == 0 else 0)
        
        parsed.append({
            'ep_id': ep_id,
            'create_time': create_time,
            'our_index': our_index,
            'our_reward': our_reward,
            'opp_reward': opp_reward,
            'margin': margin,
            'win': win,
            'opp_team_id': opp_team_id,
            'opp_team_name': opp_team_name,
            'opp_sub_id': opp_sub_id,
            'opp_rank': opp_meta['rank'],
            'opp_score': opp_meta['score'],
            'opp_tier': 'Top-10' if opp_meta['rank'] <= 10 else ('Top-20' if opp_meta['rank'] <= 20 else ('Top-50' if opp_meta['rank'] <= 50 else ('Top-100' if opp_meta['rank'] <= 100 else ('Mid-Tier' if opp_meta['score'] >= 1000 else 'Weak'))))
        })
        
    df = pd.DataFrame(parsed)
    if df.empty:
        print("No completed episodes parsed!")
        return None
        
    df['create_time'] = pd.to_datetime(df['create_time'])
    df = df.sort_values(by='create_time').reset_index(drop=True)
    df['game_num'] = df.index + 1
    
    # Calculate cumulative metrics
    df['cum_wins'] = df['win'].cumsum()
    df['cum_win_rate'] = df['cum_wins'] / df['game_num']
    
    total_games = len(df)
    total_wins = (df['win'] == 1.0).sum()
    total_draws = (df['win'] == 0.5).sum()
    total_losses = (df['win'] == 0.0).sum()
    overall_wr = total_wins / total_games if total_games > 0 else 0
    
    print(f"\nRecord: {total_wins}W - {total_losses}L - {total_draws}D in {total_games} games (Win Rate: {overall_wr*100:.1f}%)")
    print(f"Mean Reward: {df['our_reward'].mean():.1f} (Opponent Mean: {df['opp_reward'].mean():.1f}, Margin: {df['margin'].mean():+.1f})")
    print(f"Time Range: {df['create_time'].min()} to {df['create_time'].max()}")
    
    # Tier breakdown
    print("\n--- PERFORMANCE BY OPPONENT TIER ---")
    tier_summary = []
    for tier in ['Top-10', 'Top-20', 'Top-50', 'Top-100', 'Mid-Tier', 'Weak']:
        tdf = df[df['opp_tier'] == tier]
        if not tdf.empty:
            t_games = len(tdf)
            t_wins = (tdf['win'] == 1.0).sum()
            t_losses = (tdf['win'] == 0.0).sum()
            t_draws = (tdf['win'] == 0.5).sum()
            t_wr = (t_wins + 0.5 * t_draws) / t_games
            t_mean_our = tdf['our_reward'].mean()
            t_mean_opp = tdf['opp_reward'].mean()
            t_mean_margin = tdf['margin'].mean()
            tier_summary.append({
                'Tier': tier,
                'Games': t_games,
                'Wins': t_wins,
                'Losses': t_losses,
                'Draws': t_draws,
                'WinRate': f"{t_wr*100:.1f}%",
                'MeanOurReward': f"{t_mean_our:,.0f}",
                'MeanOppReward': f"{t_mean_opp:,.0f}",
                'MeanMargin': f"{t_mean_margin:+,.0f}"
            })
    print(pd.DataFrame(tier_summary).to_string(index=False))
    
    # Opponent Breakdown
    print("\n--- INDIVIDUAL OPPONENT BREAKDOWN ---")
    opp_summary = []
    for opp_name, odf in df.groupby('opp_team_name'):
        o_games = len(odf)
        o_wins = (odf['win'] == 1.0).sum()
        o_losses = (odf['win'] == 0.0).sum()
        o_draws = (odf['win'] == 0.5).sum()
        o_wr = (o_wins + 0.5 * o_draws) / o_games
        first_row = odf.iloc[0]
        opp_summary.append({
            'Opponent': opp_name,
            'Rank': first_row['opp_rank'],
            'Score': first_row['opp_score'],
            'Tier': first_row['opp_tier'],
            'Games': o_games,
            'Wins': o_wins,
            'Losses': o_losses,
            'Draws': o_draws,
            'WinRate': o_wr,
            'MeanOur': odf['our_reward'].mean(),
            'MeanOpp': odf['opp_reward'].mean(),
            'MeanMargin': odf['margin'].mean()
        })
    opp_df = pd.DataFrame(opp_summary).sort_values(by=['Rank', 'Score'], ascending=[True, False]).reset_index(drop=True)
    
    print(opp_df[['Opponent', 'Rank', 'Score', 'Tier', 'Games', 'Wins', 'Losses', 'WinRate', 'MeanMargin']].to_string(index=False))
    
    # Save processed dataframe
    df.to_csv(f"scratch/analyzed_episodes_{sub_id}.csv", index=False)
    opp_df.to_csv(f"scratch/opponent_breakdown_{sub_id}.csv", index=False)
    
    return df, opp_df

v1_df, v1_opp = analyze_submission_episodes(55944418, "Slot 1: Aethel-Prime V1")
v2_df, v2_opp = analyze_submission_episodes(55958978, "Slot 2: Aethel-Refined V2")

