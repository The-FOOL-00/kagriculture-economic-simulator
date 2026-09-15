import os
import sys
import json
from collections import defaultdict
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

def analyze_worst_losses():
    with open('scratch/final_500seed_qualification_results.json') as f:
        qdata = json.load(f)
    with open('scratch/instrumented_validation_500seeds.json') as f:
        idata = json.load(f)

    detailed = qdata['detailed']
    seeds = qdata['seeds']

    deltas = []
    for s in seeds:
        s_str = str(s)
        c_entry = detailed['Frozen_Candidate'][s_str]
        q_entry = detailed['Raw_Q50'][s_str]
        d = c_entry['reward'] - q_entry['reward']
        deltas.append((d, s, c_entry, q_entry))

    deltas.sort(key=lambda x: x[0])
    worst_25 = deltas[:25]

    print("=" * 100)
    print("AUDIT 2: TOP 25 WORST NEGATIVE-DELTA SEEDS FORENSIC TABLE")
    print("=" * 100)

    results_table = []
    for rank, (d, s, c_e, q_e) in enumerate(worst_25, 1):
        s_str = str(s)
        c_inst = idata['Frozen_Candidate'].get(s_str, {})
        q_inst = idata['Raw_Q50'].get(s_str, {})

        c_led = c_e['ledger']
        q_led = q_e['ledger']
        c_qty = c_e['sold_qty']
        q_qty = q_e['sold_qty']

        # Revenues
        rev_straw_d = c_led.get('REV_STRAWBERRY', 0) - q_led.get('REV_STRAWBERRY', 0)
        rev_wool_d = c_led.get('REV_WOOL', 0) - q_led.get('REV_WOOL', 0)
        rev_milk_d = c_led.get('REV_MILK', 0) - q_led.get('REV_MILK', 0)
        rev_melon_d = c_led.get('REV_MELON', 0) - q_led.get('REV_MELON', 0)
        rev_fert_d = c_led.get('REV_FERTILIZER', 0) - q_led.get('REV_FERTILIZER', 0)
        rev_wheat_d = c_led.get('REV_WHEAT', 0) - q_led.get('REV_WHEAT', 0)

        # Expenses
        exp_cow_d = c_led.get('EXP_ANIMAL_COW', 0) - q_led.get('EXP_ANIMAL_COW', 0)
        exp_shp_d = c_led.get('EXP_ANIMAL_SHEEP', 0) - q_led.get('EXP_ANIMAL_SHEEP', 0)
        exp_feed_d = c_led.get('EXP_FEED_WHEAT', 0) - q_led.get('EXP_FEED_WHEAT', 0)
        exp_wseed_d = c_led.get('EXP_SEED_WHEAT', 0) - q_led.get('EXP_SEED_WHEAT', 0)
        exp_mseed_d = c_led.get('EXP_SEED_MELON', 0) - q_led.get('EXP_SEED_MELON', 0)
        exp_sseed_d = c_led.get('EXP_SEED_STRAWBERRY', 0) - q_led.get('EXP_SEED_STRAWBERRY', 0)
        exp_land_d = c_led.get('EXP_LAND', 0) - q_led.get('EXP_LAND', 0)
        exp_hire_d = c_led.get('EXP_HIRE', 0) - q_led.get('EXP_HIRE', 0)

        total_rev_d = sum(v for k, v in c_led.items() if k.startswith('REV_')) - sum(v for k, v in q_led.items() if k.startswith('REV_'))
        total_exp_d = sum(v for k, v in c_led.items() if k.startswith('EXP_')) - sum(v for k, v in q_led.items() if k.startswith('EXP_'))

        # Quantities
        straw_q_d = c_qty.get('STRAWBERRY', 0) - q_qty.get('STRAWBERRY', 0)
        wool_q_d = c_qty.get('WOOL', 0) - q_qty.get('WOOL', 0)
        milk_q_d = c_qty.get('MILK', 0) - q_qty.get('MILK', 0)
        melon_q_d = c_qty.get('MELON', 0) - q_qty.get('MELON', 0)
        fert_q_d = c_qty.get('FERTILIZER', 0) - q_qty.get('FERTILIZER', 0)
        wheat_q_d = c_qty.get('WHEAT', 0) - q_qty.get('WHEAT', 0)

        # Actions
        dig_d = c_inst.get('dig', 0) - q_inst.get('dig', 0)
        move_d = c_inst.get('move', 0) - q_inst.get('move', 0)
        water_d = c_inst.get('water', 0) - q_inst.get('water', 0)
        harv_d = c_inst.get('harvest', 0) - q_inst.get('harvest', 0)
        care_d = c_inst.get('care', 0) - q_inst.get('care', 0)
        feed_d = c_inst.get('feed', 0) - q_inst.get('feed', 0)

        entry = {
            "rank": rank,
            "seed": s,
            "cand_reward": c_e['reward'],
            "q50_reward": q_e['reward'],
            "delta": d,
            "rev_deltas": {
                "STRAWBERRY": rev_straw_d, "WOOL": rev_wool_d, "MILK": rev_milk_d,
                "MELON": rev_melon_d, "FERTILIZER": rev_fert_d, "WHEAT": rev_wheat_d,
                "TOTAL_REV_D": total_rev_d
            },
            "exp_deltas": {
                "COW": exp_cow_d, "SHEEP": exp_shp_d, "FEED": exp_feed_d,
                "SEED_W": exp_wseed_d, "SEED_M": exp_mseed_d, "SEED_S": exp_sseed_d,
                "LAND": exp_land_d, "HIRE": exp_hire_d, "TOTAL_EXP_D": total_exp_d
            },
            "qty_deltas": {
                "STRAWBERRY": straw_q_d, "WOOL": wool_q_d, "MILK": milk_q_d,
                "MELON": melon_q_d, "FERTILIZER": fert_q_d, "WHEAT": wheat_q_d
            },
            "action_deltas": {
                "dig": dig_d, "move": move_d, "water": water_d, "harvest": harv_d,
                "care": care_d, "feed": feed_d
            },
            "c_inst": c_inst,
            "q_inst": q_inst,
            "c_led": c_led,
            "q_led": q_led,
            "c_qty": c_qty,
            "q_qty": q_qty,
        }
        results_table.append(entry)

    with open('scratch/worst_25_detailed_analysis.json', 'w') as f:
        json.dump(results_table, f, indent=2)

    print(f"Saved detailed 25 worst losses to scratch/worst_25_detailed_analysis.json")

if __name__ == '__main__':
    analyze_worst_losses()
