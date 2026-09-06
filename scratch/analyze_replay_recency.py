import os
import glob
import json
import pandas as pd
from datetime import datetime

def analyze_recency():
    # 1. Check daily stats from georgymamarin / manifest
    manifest_df = pd.read_csv("replays/raw/kaggle_index/manifest.csv")
    print("Daily Dataset Range:")
    print(f"Earliest daily dump: {manifest_df['date'].min()}")
    print(f"Latest daily dump: {manifest_df['date'].max()}")
    print(f"Total days indexed: {len(manifest_df)}")
    print(f"Total episodes in daily index: {manifest_df['episode_count'].sum():,}")
    
    # 2. Check local replay files timestamps
    replays = glob.glob("replays/**/*.json", recursive=True) + glob.glob("scratch/replays/*.json")
    print(f"\nTotal local replay JSON files: {len(replays)}")
    
    # Extract episode dates or file modification dates
    # Current date anchor is 2026-09-06
    current_date = datetime(2026, 9, 6)
    
    # Check our submission dates:
    # V1: 2026-09-01
    # V2: 2026-09-02
    
    # Categorize dates in manifest:
    # Recent: within 1 week (Aug 30 - Sep 6)
    # 1-2 weeks: Aug 23 - Aug 29
    # 2-3 weeks: Aug 16 - Aug 22
    # > 3 weeks: before Aug 16
    
    manifest_df['dt'] = pd.to_datetime(manifest_df['date'])
    
    d_recent = manifest_df[manifest_df['dt'] >= datetime(2026, 8, 30)]['episode_count'].sum()
    d_1_2w = manifest_df[(manifest_df['dt'] >= datetime(2026, 8, 23)) & (manifest_df['dt'] < datetime(2026, 8, 30))]['episode_count'].sum()
    d_2_3w = manifest_df[(manifest_df['dt'] >= datetime(2026, 8, 16)) & (manifest_df['dt'] < datetime(2026, 8, 23))]['episode_count'].sum()
    d_older = manifest_df[manifest_df['dt'] < datetime(2026, 8, 16)]['episode_count'].sum()
    total_episodes = manifest_df['episode_count'].sum()
    
    print("\n--- REPLAY CORPUS RECENCY BREAKDOWN ---")
    print(f"Recent (< 1 week, Aug 30 - Sep 06):  {d_recent:5d} ({d_recent/total_episodes*100:5.1f}%)")
    print(f"1-2 weeks old (Aug 23 - Aug 29):     {d_1_2w:5d} ({d_1_2w/total_episodes*100:5.1f}%)")
    print(f"2-3 weeks old (Aug 16 - Aug 22):     {d_2_3w:5d} ({d_2_3w/total_episodes*100:5.1f}%)")
    print(f"> 3 weeks old (July 30 - Aug 15):    {d_older:5d} ({d_older/total_episodes*100:5.1f}%)")
    print(f"Total Episodes in Corpus Index:      {total_episodes:5d} (100.0%)")

if __name__ == "__main__":
    analyze_recency()
