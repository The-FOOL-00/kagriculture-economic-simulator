import json
import pandas as pd

def analyze_meta():
    with open("scratch/meta_top_agents_crosscheck.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"Total entries in crosscheck: {len(data)}")
    df = pd.DataFrame(data)
    
    # Summary by player
    grouped = []
    for player, group in df.groupby('player'):
        player_clean = player.encode('ascii', 'replace').decode('ascii')
        entry = {
            "player": player_clean,
            "matches": len(group),
            "mean_reward": round(group['reward'].mean(), 1),
            "max_reward": round(group['reward'].max(), 1),
            "min_reward": round(group['reward'].min(), 1),
            "mean_q2_step": round(group['q2_step'].mean(), 1),
            "mean_q3_step": round(group['q3_step'].mean(), 1),
            "mean_pastures": round(group['max_pastures'].mean(), 1),
            "mean_cows": round(group['max_cows'].mean(), 1),
            "mean_sheep": round(group['max_sheep'].mean(), 1),
            "mean_workers": round(group['max_workers'].mean(), 1),
            "mean_wheat_bought": round(group['wheat_bought'].mean(), 1),
            "mean_milk_sold": round(group['milk_sold'].mean(), 1),
            "mean_wool_sold": round(group['wool_sold'].mean(), 1),
        }
        grouped.append(entry)
        
    grouped.sort(key=lambda x: x['mean_reward'], reverse=True)
    
    print(f"{'Player':<20} | {'Matches':<8} | {'Mean Reward':<12} | {'Q2 Step':<8} | {'Q3 Step':<8} | {'Past':<5} | {'Cows':<5} | {'Sheep':<6} | {'Wkrs':<5} | {'WheatBuy':<9}")
    print("-" * 115)
    for g in grouped:
        print(f"{g['player'][:20]:<20} | {g['matches']:<8} | ${g['mean_reward']:<11.1f} | {g['mean_q2_step']:<8.1f} | {g['mean_q3_step']:<8.1f} | {g['mean_pastures']:<5.1f} | {g['mean_cows']:<5.1f} | {g['mean_sheep']:<6.1f} | {g['mean_workers']:<5.1f} | {g['mean_wheat_bought']:<9.1f}")
        
    with open("scratch/meta_player_summary.json", "w", encoding="utf-8") as f:
        json.dump(grouped, f, indent=2)

if __name__ == "__main__":
    analyze_meta()
