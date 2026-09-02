import os
import pandas as pd
import numpy as np
import json

def analyze_large_scale_corpus():
    base = r'replays\raw\georgymamarin'
    if not os.path.exists(base):
        print(f"Directory {base} not found.")
        return

    print("Loading episodes and features from georgymamarin dataset...")
    episodes_path = os.path.join(base, 'episodes.csv')
    features_path = os.path.join(base, 'episode_features.csv')
    agents_path = os.path.join(base, 'agents.csv')
    daily_stats_path = os.path.join(base, 'daily_stats.csv')
    
    ep_df = pd.read_csv(episodes_path, nrows=50000)
    print(f"Loaded {len(ep_df)} episodes from episodes.csv")
    print(f"Columns in episodes.csv: {list(ep_df.columns)}")
    
    feat_df = pd.read_csv(features_path, nrows=100000)
    print(f"Loaded {len(feat_df)} feature rows from episode_features.csv")
    print(f"Columns in episode_features.csv: {list(feat_df.columns)}")

    # Summary statistics
    # Check top agents by win rate and final score
    top_agents_feat = feat_df.groupby('agent_id').agg({
        'final_bank': ['count', 'mean', 'median', 'std'],
        'win': 'mean',
        'peak_crew': 'mean',
        'cows': 'mean' if 'cows' in feat_df.columns else lambda x: 0,
        'sheep': 'mean' if 'sheep' in feat_df.columns else lambda x: 0,
        'first_land_day': 'mean' if 'first_land_day' in feat_df.columns else lambda x: 0
    })
    
    print("\nSample top agent aggregations:")
    print(top_agents_feat.head(10))

    # Identify strategy clusters based on asset counts
    print("\nFeature correlations with win and final bank:")
    num_cols = [c for c in feat_df.columns if feat_df[c].dtype in (np.float64, np.int64)]
    corr = feat_df[num_cols].corr()
    if 'win' in corr:
        print(corr['win'].sort_values(ascending=False))

    results = {
        'total_episodes_sampled': len(ep_df),
        'total_feature_rows_sampled': len(feat_df),
        'top_correlations_with_win': corr['win'].to_dict() if 'win' in corr else {},
        'top_correlations_with_bank': corr['final_bank'].to_dict() if 'final_bank' in corr else {}
    }
    
    with open(r'scratch\large_scale_corpus_summary.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

if __name__ == '__main__':
    analyze_large_scale_corpus()
