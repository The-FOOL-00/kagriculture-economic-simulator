import pandas as pd
import json

def merge_and_build_matrix():
    df_gt = pd.read_csv("scratch/ground_truth_replays_dataset.csv")
    with open("scratch/meta_top_agents_crosscheck.json", "r", encoding="utf-8") as f:
        meta_cross = json.load(f)
        
    df_meta = pd.DataFrame(meta_cross)
    
    # Merge on file and p_idx
    df_merged = pd.merge(df_gt, df_meta[['file', 'player', 'p_idx']], on=['file', 'p_idx'], how='left')
    
    # If player is still nan, infer from filename
    def infer_player(row):
        if pd.notna(row['player_y']):
            return row['player_y']
        fname = row['file'].lower()
        if 'crop_dusta' in fname:
            return 'Crop Dusta'
        if 'whyme' in fname:
            return 'Whyme Labs'
        if 'yuan800' in fname:
            return 'Yuan800'
        if 'mtn' in fname:
            return 'MtN'
        if 'kawattataido' in fname:
            return 'KawattaTaido'
        if '3junghoon' in fname:
            return '3JungHoon'
        if 'aethel' in fname or 'v2' in fname:
            return 'Aethel V2'
        return f"Unknown_P{row['p_idx']}"
        
    df_merged['player'] = df_merged.apply(infer_player, axis=1)
    
    # Clean player name
    df_merged['player_clean'] = df_merged['player'].apply(lambda x: str(x).encode('ascii', 'replace').decode('ascii'))
    
    print("Total rows:", len(df_merged))
    print("\nUnique players and counts:")
    print(df_merged['player_clean'].value_counts())
    
    metrics = [
        'final_reward', 'day0_money', 'day0_hires', 'day0_pastures', 'day0_cows', 'day0_sheep',
        'q2_step', 'q3_step', 'q4_step',
        'pastures_d5', 'pastures_d11', 'pastures_d29',
        'cows_d5', 'cows_d11', 'cows_d29',
        'sheep_d5', 'sheep_d11', 'sheep_d29',
        'workers_d5', 'workers_d11', 'workers_d29',
        'money_d5', 'money_d11', 'money_d20', 'money_d29',
        'wheat_bought', 'wheat_sold', 'milk_sold', 'wool_sold', 'fertilizer_sold',
        'melons_sold', 'strawberries_sold', 'tomatoes_sold', 'carrots_sold', 'eggs_sold',
        'fert_sale_hours_mode', 'fert_avg_batch', 'milk_first_sale_step',
        'sells_before_buys_turns', 'buys_before_sells_turns',
        'last_seed_buy_step', 'last_animal_buy_step'
    ]
    
    grouped = df_merged.groupby('player_clean')[metrics].mean().round(1)
    grouped['matches'] = df_merged.groupby('player_clean').size()
    grouped = grouped.sort_values(by='final_reward', ascending=False)
    
    print("\n--- BEHAVIOR MATRIX SUMMARY ---")
    cols_to_show = ['matches', 'final_reward', 'q2_step', 'q3_step', 'pastures_d29', 'cows_d29', 'sheep_d29', 'workers_d29', 'wheat_bought', 'milk_sold', 'wool_sold', 'fertilizer_sold', 'melons_sold', 'strawberries_sold']
    print(grouped[cols_to_show])
    
    grouped.to_csv("scratch/top_meta_behavior_matrix.csv")
    grouped.to_json("scratch/top_meta_behavior_matrix.json", orient="index", indent=2)
    df_merged.to_csv("scratch/ground_truth_replays_dataset_complete.csv", index=False)
    print("\nSuccessfully saved complete matrices.")

if __name__ == "__main__":
    merge_and_build_matrix()
