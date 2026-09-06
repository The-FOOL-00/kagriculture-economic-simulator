import os
import glob
import json
import pandas as pd
import numpy as np

def parse_single_replay(fpath):
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    steps = data.get("steps")
    if not steps or len(steps) < 100:
        return []
        
    agents = data.get("agents") or data.get("info", {}).get("Agents") or []
    
    records = []
    
    for p_idx in [0, 1]:
        name = f"Player_{p_idx}"
        if len(agents) > p_idx:
            ag = agents[p_idx]
            name = ag.get("name") if isinstance(ag, dict) else str(ag)
            
        # Track timeline variables
        day0_money = None
        day0_hires = 0
        day0_pastures = 0
        day0_cows = 0
        day0_sheep = 0
        
        q2_step = None
        q3_step = None
        q4_step = None
        
        cows_by_day = {}
        sheep_by_day = {}
        pastures_by_day = {}
        workers_by_day = {}
        money_by_day = {}
        
        # Cumulative transactions
        sales_units = {}
        sales_rev = {}
        buys_units = {}
        buys_cost = {}
        
        # Fertilizer sales analysis
        fert_sale_hours = []
        fert_sale_batches = []
        
        # Milk sales analysis
        milk_sale_steps = []
        milk_sale_batches = []
        
        # Check order queue priority (sells before buys in same turn)
        sells_before_buys_count = 0
        buys_before_sells_count = 0
        
        # Terminal cease step
        last_seed_buy_step = 0
        last_animal_buy_step = 0
        
        for step_idx, step in enumerate(steps):
            if not isinstance(step, list) or len(step) <= p_idx:
                continue
            p_data = step[p_idx]
            obs = p_data.get("observation", {})
            act = p_data.get("action", {})
            
            day = obs.get("day", step_idx // 24)
            hour = obs.get("hour", step_idx % 24)
            
            farms = obs.get("farms", [])
            my_farm = farms[p_idx] if len(farms) > p_idx and isinstance(farms[p_idx], dict) else {}
            
            money = my_farm.get("money", 0)
            quads = my_farm.get("unlocked_quadrants", ["NW"])
            hands = my_farm.get("hands", [])
            tiles = my_farm.get("tiles", [])
            
            # Count pastures and animals from tiles / private
            pasture_count = 0
            cow_count = 0
            sheep_count = 0
            
            if tiles:
                for row in tiles:
                    for tile in row:
                        if isinstance(tile, dict):
                            ttype = tile.get("type", "")
                            if ttype == "PASTURE" or "PASTURE" in str(tile):
                                pasture_count += 1
                            animals = tile.get("animals", [])
                            if isinstance(animals, list):
                                for a in animals:
                                    atype = a.get("type", "") if isinstance(a, dict) else str(a)
                                    if "COW" in atype: cow_count += 1
                                    elif "SHEEP" in atype: sheep_count += 1
                                    
            num_workers = len(hands) + 1 # Hands + Farmer
            
            # Record day snapshots at hour 0
            if hour == 0 or step_idx == 0:
                cows_by_day[day] = cow_count
                sheep_by_day[day] = sheep_count
                pastures_by_day[day] = pasture_count
                workers_by_day[day] = num_workers
                money_by_day[day] = money
                
            if step_idx == 1:
                day0_money = money
                day0_hires = len(hands)
                day0_pastures = pasture_count
                day0_cows = cow_count
                day0_sheep = sheep_count
                
            # Check quadrant unlocks
            if len(quads) >= 2 and q2_step is None:
                q2_step = step_idx
            if len(quads) >= 3 and q3_step is None:
                q3_step = step_idx
            if len(quads) >= 4 and q4_step is None:
                q4_step = step_idx
                
            # Process actions for transactions
            if act and isinstance(act, dict):
                market_acts = act.get("market", [])
                if isinstance(market_acts, list):
                    # Check order of sells vs buys
                    turn_sells = []
                    turn_buys = []
                    for ma in market_acts:
                        if not isinstance(ma, list) or len(ma) < 2:
                            continue
                        mtype = ma[0]
                        if mtype in ["SELL", "SELL_PRODUCT"]:
                            turn_sells.append(ma)
                            item = ma[1]
                            amt = ma[2] if len(ma) > 2 else 1
                            sales_units[item] = sales_units.get(item, 0) + amt
                            if item == "FERTILIZER":
                                fert_sale_hours.append(hour)
                                fert_sale_batches.append(amt)
                            elif item == "MILK":
                                milk_sale_steps.append(step_idx)
                                milk_sale_batches.append(amt)
                        elif mtype in ["BUY", "BUY_PRODUCT", "BUY_ANIMAL", "BUY_LAND"]:
                            turn_buys.append(ma)
                            item = ma[1] if len(ma) > 1 else "LAND"
                            amt = ma[2] if len(ma) > 2 else 1
                            buys_units[item] = buys_units.get(item, 0) + amt
                            if "SEED" in str(item):
                                last_seed_buy_step = max(last_seed_buy_step, step_idx)
                            if mtype == "BUY_ANIMAL":
                                last_animal_buy_step = max(last_animal_buy_step, step_idx)
                                
                    if turn_sells and turn_buys:
                        first_sell_idx = min(market_acts.index(s) for s in turn_sells)
                        first_buy_idx = min(market_acts.index(b) for b in turn_buys)
                        if first_sell_idx < first_buy_idx:
                            sells_before_buys_count += 1
                        else:
                            buys_before_sells_count += 1
                            
        final_reward = steps[-1][p_idx].get("reward", 0.0)
        
        record = {
            "file": os.path.basename(fpath),
            "player": name,
            "p_idx": p_idx,
            "final_reward": final_reward,
            "day0_money": day0_money,
            "day0_hires": day0_hires,
            "day0_pastures": day0_pastures,
            "day0_cows": day0_cows,
            "day0_sheep": day0_sheep,
            "q2_step": q2_step,
            "q3_step": q3_step,
            "q4_step": q4_step,
            "cows_d5": cows_by_day.get(5, 0),
            "cows_d8": cows_by_day.get(8, 0),
            "cows_d11": cows_by_day.get(11, 0),
            "cows_d20": cows_by_day.get(20, 0),
            "cows_d29": cows_by_day.get(29, cows_by_day.get(len(cows_by_day)-1, 0)),
            "sheep_d5": sheep_by_day.get(5, 0),
            "sheep_d8": sheep_by_day.get(8, 0),
            "sheep_d11": sheep_by_day.get(11, 0),
            "sheep_d20": sheep_by_day.get(20, 0),
            "sheep_d29": sheep_by_day.get(29, sheep_by_day.get(len(sheep_by_day)-1, 0)),
            "pastures_d5": pastures_by_day.get(5, 0),
            "pastures_d8": pastures_by_day.get(8, 0),
            "pastures_d11": pastures_by_day.get(11, 0),
            "pastures_d20": pastures_by_day.get(20, 0),
            "pastures_d29": pastures_by_day.get(29, pastures_by_day.get(len(pastures_by_day)-1, 0)),
            "workers_d5": workers_by_day.get(5, 0),
            "workers_d8": workers_by_day.get(8, 0),
            "workers_d11": workers_by_day.get(11, 0),
            "workers_d20": workers_by_day.get(20, 0),
            "workers_d29": workers_by_day.get(29, workers_by_day.get(len(workers_by_day)-1, 0)),
            "money_d5": money_by_day.get(5, 0),
            "money_d8": money_by_day.get(8, 0),
            "money_d11": money_by_day.get(11, 0),
            "money_d20": money_by_day.get(20, 0),
            "money_d29": money_by_day.get(29, money_by_day.get(len(money_by_day)-1, 0)),
            "wheat_bought": buys_units.get("WHEAT", 0),
            "wheat_sold": sales_units.get("WHEAT", 0),
            "milk_sold": sales_units.get("MILK", 0),
            "wool_sold": sales_units.get("WOOL", 0),
            "fertilizer_sold": sales_units.get("FERTILIZER", 0),
            "melons_sold": sales_units.get("MELON", 0),
            "strawberries_sold": sales_units.get("STRAWBERRY", 0),
            "tomatoes_sold": sales_units.get("TOMATO", 0),
            "carrots_sold": sales_units.get("CARROT", 0),
            "eggs_sold": sales_units.get("EGG", 0),
            "fert_sale_hours_mode": int(pd.Series(fert_sale_hours).mode()[0]) if fert_sale_hours else None,
            "fert_avg_batch": round(float(np.mean(fert_sale_batches)), 1) if fert_sale_batches else 0,
            "milk_first_sale_step": milk_sale_steps[0] if milk_sale_steps else None,
            "milk_avg_batch": round(float(np.mean(milk_sale_batches)), 1) if milk_sale_batches else 0,
            "sells_before_buys_turns": sells_before_buys_count,
            "buys_before_sells_turns": buys_before_sells_count,
            "last_seed_buy_step": last_seed_buy_step,
            "last_animal_buy_step": last_animal_buy_step
        }
        records.append(record)
        
    return records

def main():
    files = glob.glob("scratch/replays/*.json")
    print(f"Parsing {len(files)} replays...")
    all_records = []
    for f in files:
        if os.path.getsize(f) < 1000:
            continue
        try:
            recs = parse_single_replay(f)
            all_records.extend(recs)
        except Exception as e:
            # print(f"Error {f}: {e}")
            pass
            
    print(f"Extracted {len(all_records)} ground-truth player records.")
    with open("scratch/ground_truth_replays_dataset.json", "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2)
        
    df = pd.DataFrame(all_records)
    df.to_csv("scratch/ground_truth_replays_dataset.csv", index=False)
    print("Saved ground_truth_replays_dataset.csv successfully.")

if __name__ == "__main__":
    main()
