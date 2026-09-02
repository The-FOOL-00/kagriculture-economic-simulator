import os
import json
import numpy as np

def analyze_losses():
    with open(r'scratch\aethel_full_forensics_reconciled.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    aethel_dir = r'replays\Aethel_prime_v1'
    
    losses = [r for r in data if r['outcome'] == 'LOSS']
    print(f"Total Losses: {len(losses)}")
    
    loss_classifications = []
    
    for l in losses:
        rf = l['replay_file']
        rpath = os.path.join(aethel_dir, rf)
        with open(rpath, 'r', encoding='utf-8') as f:
            rep = json.load(f)
            
        our_seat = l['our_seat']
        opp_seat = 1 - our_seat
        steps = rep.get('steps', [])
        
        # Turn-by-turn detailed telemetry
        # Track: money, cows, sheep, workers, crops, feed/fertilizer, town visits, market sales
        our_trace = []
        opp_trace = []
        
        # We want to identify the exact mechanism of loss
        final_our_cows, final_opp_cows = 0, 0
        final_our_sheep, final_opp_sheep = 0, 0
        final_our_workers, final_opp_workers = 0, 0
        final_our_land, final_opp_land = 0, 0
        final_our_crops, final_opp_crops = 0, 0
        
        market_price_impact = 0
        town_purchases_opp = 0
        town_purchases_our = 0
        
        for step_idx, step_data in enumerate(steps):
            if len(step_data) < 2:
                continue
            obs0 = step_data[0].get('observation', {})
            obs1 = step_data[1].get('observation', {})
            our_obs = obs0 if our_seat == 0 else obs1
            opp_obs = obs1 if our_seat == 0 else obs0
            
            our_farm = our_obs.get('farms', [{}])[our_seat] if 'farms' in our_obs and len(our_obs['farms']) > our_seat else {}
            opp_farm = opp_obs.get('farms', [{}])[opp_seat] if 'farms' in opp_obs and len(opp_obs['farms']) > opp_seat else {}
            
            def count_assets(farm):
                tiles = farm.get('tiles', [])
                cows, sheep, geese, crops, plowed = 0, 0, 0, 0, 0
                for r in tiles:
                    for c in r:
                        if isinstance(c, dict):
                            if 'COW' in str(c): cows += 1
                            elif 'SHEEP' in str(c): sheep += 1
                            elif 'GOOSE' in str(c) or 'GEESE' in str(c): geese += 1
                            elif c.get('crop') is not None or c.get('stage') is not None: crops += 1
                            elif c.get('plowed'): plowed += 1
                return cows, sheep, geese, crops, plowed
            
            oc, os_, og, ocr, opl = count_assets(our_farm)
            ec, es_, eg, ecr, epl = count_assets(opp_farm)
            
            if step_idx == len(steps) - 1:
                final_our_cows, final_opp_cows = oc, ec
                final_our_sheep, final_opp_sheep = os_, es_
                final_our_workers = len(our_farm.get('hands', [])) + 1
                final_opp_workers = len(opp_farm.get('hands', [])) + 1
                final_our_land = len(our_farm.get('unlocked_quadrants', []))
                final_opp_land = len(opp_farm.get('unlocked_quadrants', []))

        # Classification rules based on telemetry:
        margin = l['margin']
        abs_margin = abs(margin)
        
        category = 'UNKNOWN'
        explanation = ''
        
        # Case 1: High negative margin with livestock scaling gap
        if final_opp_cows >= final_our_cows + 2 or (final_opp_cows >= 8 and final_our_cows <= 6):
            category = 'LIVESTOCK SCALING'
            explanation = f"Opponent scaled to {final_opp_cows} cows (vs our {final_our_cows} cows), compounding passive milk revenue."
        elif final_opp_workers >= final_our_workers + 2 and abs_margin > 5000:
            category = 'WORKER THROUGHPUT'
            explanation = f"Opponent scaled labor to {final_opp_workers} workers (vs our {final_our_workers}), generating higher cycle throughput."
        elif final_opp_land > final_our_land and abs_margin > 4000:
            category = 'LAND'
            explanation = f"Opponent expanded to {final_opp_land} quadrants vs our {final_our_land} quadrants, enabling superior spatial footprint."
        elif abs_margin < 1000:
            # Marginal loss (< 1000 margin)
            # Check endgame / liquidation / timing
            category = 'ENDGAME'
            explanation = f"Close loss (margin {margin:.0f}). Determined by final 50-turn liquidation timing and unsold crop/feed salvage."
        elif l['first_divergence_turn'] and l['first_divergence_turn'] < 50:
            category = 'OPENING'
            explanation = f"Opening divergence at turn {l['first_divergence_turn']}: {l['divergence_reason']}"
        elif final_opp_sheep >= 3 and final_our_sheep == 0:
            category = 'ROUTE SELECTION'
            explanation = f"Opponent played a diversified livestock route (sheep+cows) that captured superior price dynamics vs our fixed cow trace."
        elif abs_margin > 10000:
            category = 'LIVESTOCK SCALING'
            explanation = f"Major economic blowout (margin {margin:.0f}). Opponent achieved superior compounding livestock/feed cycle."
        else:
            category = 'ROUTE SELECTION'
            explanation = f"Macro route mismatch against opponent strategy: {l['divergence_reason']}"
            
        loss_classifications.append({
            'episode_id': l['episode_id'],
            'opponent': l['opp_name'],
            'our_score': l['our_score'],
            'opp_score': l['opp_score'],
            'margin': l['margin'],
            'category': category,
            'explanation': explanation,
            'our_cows': final_our_cows,
            'opp_cows': final_opp_cows,
            'our_workers': final_our_workers,
            'opp_workers': final_opp_workers,
            'our_land': final_our_land,
            'opp_land': final_opp_land
        })

    # Aggregate by category
    cats = {}
    for lc in loss_classifications:
        c = lc['category']
        if c not in cats:
            cats[c] = []
        cats[c].append(lc)
        
    print("\n--- LOSS CLASSIFICATION BREAKDOWN ---")
    print(f"{'Category':<22} | {'Count':<5} | {'Pct':<6} | {'Mean Margin':<12} | {'Median Margin':<14} | {'Worst Loss'}")
    print("-" * 80)
    for c, items in sorted(cats.items(), key=lambda x: len(x[1]), reverse=True):
        margins = [it['margin'] for it in items]
        cnt = len(items)
        pct = (cnt / len(losses)) * 100
        mean_m = np.mean(margins)
        med_m = np.median(margins)
        worst_m = min(margins)
        print(f"{c:<22} | {cnt:<5} | {pct:<5.1f}% | {mean_m:<12.1f} | {med_m:<14.1f} | {worst_m:<.1f}")

    with open(r'scratch\aethel_loss_classifications.json', 'w', encoding='utf-8') as f:
        json.dump(loss_classifications, f, indent=2)

if __name__ == '__main__':
    analyze_losses()
