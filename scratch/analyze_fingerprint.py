import json
import numpy as np

def analyze_fingerprint():
    with open("scratch/deep_behavioral_fingerprint_m1_v2.json") as f:
        data = json.load(f)

    m1_list = data["M1"]
    v2_list = data["V2"]
    n_seeds = len(m1_list)

    print("=" * 105)
    print(f"DEEP BEHAVIORAL & LIFECYCLE FORENSICS: M1 vs FROZEN V2 (N={n_seeds} SEEDS, 1000-1049)")
    print("=" * 105)

    # -------------------------------------------------------------
    # 1. Action-level Comparison & Top 10 Behavioral Differences
    # -------------------------------------------------------------
    all_action_keys = set()
    for item in m1_list + v2_list:
        all_action_keys.update(item["actions"].keys())

    action_diffs = []
    for ak in sorted(all_action_keys):
        m1_vals = [x["actions"].get(ak, 0) for x in m1_list]
        v2_vals = [x["actions"].get(ak, 0) for x in v2_list]
        m_m1 = np.mean(m1_vals)
        m_v2 = np.mean(v2_vals)
        diff = m_v2 - m_m1
        action_diffs.append((ak, m_m1, m_v2, diff, abs(diff)))

    # Sort by absolute difference
    action_diffs.sort(key=lambda x: x[4], reverse=True)

    print("\n--- PHASE 3: ACTION-LEVEL BEHAVIORAL PROFILE & TOP 10 DIFFERENCES ---")
    print(f"{'Action Name':<24} | {'M1 Mean':<14} | {'V2 Mean':<14} | {'Delta (V2 - M1)':<16} | {'Abs Delta':<10}")
    print("-" * 85)
    for ak, m_m1, m_v2, diff, abs_d in action_diffs[:15]:
        print(f"{ak:<24} | {m_m1:>14.1f} | {m_v2:>14.1f} | {diff:>+16.1f} | {abs_d:>10.1f}")

    # -------------------------------------------------------------
    # 2. Wheat Mass Balance
    # -------------------------------------------------------------
    print("\n--- PHASE 5: WHEAT MASS BALANCE ---")
    w_pl_m1 = np.mean([x["wheat"]["planted_plots"] for x in m1_list])
    w_pl_v2 = np.mean([x["wheat"]["planted_plots"] for x in v2_list])

    w_hv_m1 = np.mean([x["wheat"]["harvested_units"] for x in m1_list])
    w_hv_v2 = np.mean([x["wheat"]["harvested_units"] for x in v2_list])

    w_bt_m1 = np.mean([x["wheat"]["bought_units"] for x in m1_list])
    w_bt_v2 = np.mean([x["wheat"]["bought_units"] for x in v2_list])

    w_sd_m1 = np.mean([x["wheat"]["sold_units"] for x in m1_list])
    w_sd_v2 = np.mean([x["wheat"]["sold_units"] for x in v2_list])

    w_sh_m1 = np.mean([x["wheat"]["term_shed"] for x in m1_list])
    w_sh_v2 = np.mean([x["wheat"]["term_shed"] for x in v2_list])

    w_pk_m1 = np.mean([x["wheat"]["term_pockets"] for x in m1_list])
    w_pk_v2 = np.mean([x["wheat"]["term_pockets"] for x in v2_list])

    # Animal feed eaten = total supply (harvested + bought) - (sold + term_shed + term_pockets)
    w_eaten_m1 = (w_hv_m1 + w_bt_m1) - (w_sd_m1 + w_sh_m1 + w_pk_m1)
    w_eaten_v2 = (w_hv_v2 + w_bt_v2) - (w_sd_v2 + w_sh_v2 + w_pk_v2)

    print(f"{'Wheat Mass Balance Metric':<32} | {'M1 Mean':<14} | {'V2 Mean':<14} | {'Delta (V2 - M1)':<16}")
    print("-" * 80)
    print(f"{'Wheat Plots Planted':<32} | {w_pl_m1:>14.1f} | {w_pl_v2:>14.1f} | {w_pl_v2 - w_pl_m1:>+16.1f}")
    print(f"{'Wheat Units Harvested':<32} | {w_hv_m1:>14.1f} | {w_hv_v2:>14.1f} | {w_hv_v2 - w_hv_m1:>+16.1f}")
    print(f"{'Wheat Purchased (Feed)':<32} | {w_bt_m1:>14.1f} | {w_bt_v2:>14.1f} | {w_bt_v2 - w_bt_m1:>+16.1f}")
    print(f"{'Total Wheat Inflow (Harv+Buy)':<32} | {w_hv_m1 + w_bt_m1:>14.1f} | {w_hv_v2 + w_bt_v2:>14.1f} | {(w_hv_v2 + w_bt_v2) - (w_hv_m1 + w_bt_m1):>+16.1f}")
    print(f"{'Wheat Sold on Market':<32} | {w_sd_m1:>14.1f} | {w_sd_v2:>14.1f} | {w_sd_v2 - w_sd_m1:>+16.1f}")
    print(f"{'Wheat Eaten by Livestock':<32} | {w_eaten_m1:>14.1f} | {w_eaten_v2:>14.1f} | {w_eaten_v2 - w_eaten_m1:>+16.1f}")
    print(f"{'Terminal Wheat in Shed':<32} | {w_sh_m1:>14.1f} | {w_sh_v2:>14.1f} | {w_sh_v2 - w_sh_m1:>+16.1f}")
    print(f"{'Terminal Wheat in Pockets':<32} | {w_pk_m1:>14.1f} | {w_pk_v2:>14.1f} | {w_pk_v2 - w_pk_m1:>+16.1f}")
    print(f"{'Yield per Planted Plot (u/plot)':<32} | {w_hv_m1/max(1, w_pl_m1):>14.2f} | {w_hv_v2/max(1, w_pl_v2):>14.2f} | {(w_hv_v2/max(1, w_pl_v2)) - (w_hv_m1/max(1, w_pl_m1)):>+16.2f}")

    # -------------------------------------------------------------
    # 3. Sheep & Wool Lifecycle
    # -------------------------------------------------------------
    print("\n--- PHASE 6: SHEEP & WOOL LIFECYCLE ---")
    s_cnt_m1 = np.mean([x["sheep_wool"]["sheep_bought"] for x in m1_list])
    s_cnt_v2 = np.mean([x["sheep_wool"]["sheep_bought"] for x in v2_list])

    s_fst_m1 = np.mean([x["sheep_wool"]["first_sheep_day"] for x in m1_list])
    s_fst_v2 = np.mean([x["sheep_wool"]["first_sheep_day"] for x in v2_list])

    s_lst_m1 = np.mean([x["sheep_wool"]["last_sheep_day"] for x in m1_list])
    s_lst_v2 = np.mean([x["sheep_wool"]["last_sheep_day"] for x in v2_list])

    s_mn_m1 = np.mean([x["sheep_wool"]["mean_sheep_day"] for x in m1_list])
    s_mn_v2 = np.mean([x["sheep_wool"]["mean_sheep_day"] for x in v2_list])

    w_shr_m1 = np.mean([x["sheep_wool"]["wool_shears"] for x in m1_list])
    w_shr_v2 = np.mean([x["sheep_wool"]["wool_shears"] for x in v2_list])

    w_harv_m1 = np.mean([x["sheep_wool"]["wool_units_harvested"] for x in m1_list])
    w_harv_v2 = np.mean([x["sheep_wool"]["wool_units_harvested"] for x in v2_list])

    w_sold_m1 = np.mean([x["sheep_wool"]["wool_sold"] for x in m1_list])
    w_sold_v2 = np.mean([x["sheep_wool"]["wool_sold"] for x in v2_list])

    print(f"{'Sheep / Wool Metric':<32} | {'M1 Mean':<14} | {'V2 Mean':<14} | {'Delta (V2 - M1)':<16}")
    print("-" * 80)
    print(f"{'Total Sheep Purchased':<32} | {s_cnt_m1:>14.2f} | {s_cnt_v2:>14.2f} | {s_cnt_v2 - s_cnt_m1:>+16.2f}")
    print(f"{'First Sheep Day':<32} | {s_fst_m1:>14.2f} | {s_fst_v2:>14.2f} | {s_fst_v2 - s_fst_m1:>+16.2f}")
    print(f"{'Last Sheep Day':<32} | {s_lst_m1:>14.2f} | {s_lst_v2:>14.2f} | {s_lst_v2 - s_lst_m1:>+16.2f}")
    print(f"{'Mean Sheep Purchase Day':<32} | {s_mn_m1:>14.2f} | {s_mn_v2:>14.2f} | {s_mn_v2 - s_mn_m1:>+16.2f}")
    print(f"{'Shearing Actions (CARE sheep)':<32} | {w_shr_m1:>14.2f} | {w_shr_v2:>14.2f} | {w_shr_v2 - w_shr_m1:>+16.2f}")
    print(f"{'Wool Units Harvested':<32} | {w_harv_m1:>14.2f} | {w_harv_v2:>14.2f} | {w_harv_v2 - w_harv_m1:>+16.2f}")
    print(f"{'Wool Units Sold':<32} | {w_sold_m1:>14.2f} | {w_sold_v2:>14.2f} | {w_sold_v2 - w_sold_m1:>+16.2f}")
    print(f"{'Shears per Sheep':<32} | {w_shr_m1/max(1, s_cnt_m1):>14.2f} | {w_shr_v2/max(1, s_cnt_v2):>14.2f} | {(w_shr_v2/max(1, s_cnt_v2)) - (w_shr_m1/max(1, s_cnt_m1)):>+16.2f}")

    # -------------------------------------------------------------
    # 4. Strawberry Lifecycle Waterfall
    # -------------------------------------------------------------
    print("\n--- PHASE 7: STRAWBERRY LIFECYCLE WATERFALL ---")
    st_pl_m1 = np.mean([x["strawberry"]["planted_plots"] for x in m1_list])
    st_pl_v2 = np.mean([x["strawberry"]["planted_plots"] for x in v2_list])

    st_plday_m1 = np.mean([x["strawberry"]["mean_plant_day"] for x in m1_list])
    st_plday_v2 = np.mean([x["strawberry"]["mean_plant_day"] for x in v2_list])

    st_pot_m1 = np.mean([x["strawberry"]["potential_cycles"] for x in m1_list])
    st_pot_v2 = np.mean([x["strawberry"]["potential_cycles"] for x in v2_list])

    st_fert_m1 = np.mean([x["strawberry"]["fert_cycles"] for x in m1_list])
    st_fert_v2 = np.mean([x["strawberry"]["fert_cycles"] for x in v2_list])

    st_unfert_m1 = np.mean([x["strawberry"]["unfert_cycles"] for x in m1_list])
    st_unfert_v2 = np.mean([x["strawberry"]["unfert_cycles"] for x in v2_list])

    st_hv_m1 = np.mean([x["strawberry"]["harvested_units"] for x in m1_list])
    st_hv_v2 = np.mean([x["strawberry"]["harvested_units"] for x in v2_list])

    st_sd_m1 = np.mean([x["strawberry"]["sold_units"] for x in m1_list])
    st_sd_v2 = np.mean([x["strawberry"]["sold_units"] for x in v2_list])

    print(f"{'Strawberry Waterfall Stage':<32} | {'M1 Mean':<14} | {'V2 Mean':<14} | {'Delta (V2 - M1)':<16}")
    print("-" * 80)
    print(f"{'1. Bushes Planted':<32} | {st_pl_m1:>14.1f} | {st_pl_v2:>14.1f} | {st_pl_v2 - st_pl_m1:>+16.1f}")
    print(f"{'   Mean Planting Day':<32} | {st_plday_m1:>14.1f} | {st_plday_v2:>14.1f} | {st_plday_v2 - st_plday_m1:>+16.1f}")
    print(f"{'2. Potential Cycles (< Day 30)':<32} | {st_pot_m1:>14.1f} | {st_pot_v2:>14.1f} | {st_pot_v2 - st_pot_m1:>+16.1f}")
    print(f"{'3. Realized Fertilized (+2)':<32} | {st_fert_m1:>14.1f} | {st_fert_v2:>14.1f} | {st_fert_v2 - st_fert_m1:>+16.1f}")
    print(f"{'4. Realized Unfertilized (+1)':<32} | {st_unfert_m1:>14.1f} | {st_unfert_v2:>14.1f} | {st_unfert_v2 - st_unfert_m1:>+16.1f}")
    print(f"{'5. Physical Yield Harvested (u)':<32} | {st_hv_m1:>14.1f} | {st_hv_v2:>14.1f} | {st_hv_v2 - st_hv_m1:>+16.1f}")
    print(f"{'6. Total Sold on Market (u)':<32} | {st_sd_m1:>14.1f} | {st_sd_v2:>14.1f} | {st_sd_v2 - st_sd_m1:>+16.1f}")

    # -------------------------------------------------------------
    # 5. Movement & Logistics
    # -------------------------------------------------------------
    print("\n--- PHASE 8: MOVEMENT & LOGISTICS COMPARISON ---")
    mv_tot_m1 = np.mean([x["logistics"]["moves_total"] for x in m1_list])
    mv_tot_v2 = np.mean([x["logistics"]["moves_total"] for x in v2_list])

    mv_c_m1 = np.mean([x["logistics"]["moves_with_cargo"] for x in m1_list])
    mv_c_v2 = np.mean([x["logistics"]["moves_with_cargo"] for x in v2_list])

    mv_e_m1 = np.mean([x["logistics"]["moves_empty"] for x in m1_list])
    mv_e_v2 = np.mean([x["logistics"]["moves_empty"] for x in v2_list])

    dr_m1 = np.mean([x["logistics"]["shed_drops"] for x in m1_list])
    dr_v2 = np.mean([x["logistics"]["shed_drops"] for x in v2_list])

    dr_u_m1 = np.mean([x["logistics"]["shed_units_dropped"] for x in m1_list])
    dr_u_v2 = np.mean([x["logistics"]["shed_units_dropped"] for x in v2_list])

    avg_dp_m1 = np.mean([x["logistics"]["avg_drop_size"] for x in m1_list])
    avg_dp_v2 = np.mean([x["logistics"]["avg_drop_size"] for x in v2_list])

    pass_m1 = np.mean([x["logistics"]["worker_passes"] for x in m1_list])
    pass_v2 = np.mean([x["logistics"]["worker_passes"] for x in v2_list])

    print(f"{'Logistics Metric':<32} | {'M1 Mean':<14} | {'V2 Mean':<14} | {'Delta (V2 - M1)':<16}")
    print("-" * 80)
    print(f"{'Total Movement Actions':<32} | {mv_tot_m1:>14.1f} | {mv_tot_v2:>14.1f} | {mv_tot_v2 - mv_tot_m1:>+16.1f}")
    print(f"{'Moves with Cargo in Pocket':<32} | {mv_c_m1:>14.1f} | {mv_c_v2:>14.1f} | {mv_c_v2 - mv_c_m1:>+16.1f}")
    print(f"{'Moves with Empty Pockets':<32} | {mv_e_m1:>14.1f} | {mv_e_v2:>14.1f} | {mv_e_v2 - mv_e_m1:>+16.1f}")
    print(f"{'Total Shed DROP Actions':<32} | {dr_m1:>14.1f} | {dr_v2:>14.1f} | {dr_v2 - dr_m1:>+16.1f}")
    print(f"{'Total Units Dropped into Shed':<32} | {dr_u_m1:>14.1f} | {dr_u_v2:>14.1f} | {dr_u_v2 - dr_u_m1:>+16.1f}")
    print(f"{'Average Units per Drop (Batch)':<32} | {avg_dp_m1:>14.2f} | {avg_dp_v2:>14.2f} | {avg_dp_v2 - avg_dp_m1:>+16.2f}")
    print(f"{'Worker PASS (Idle) Turns':<32} | {pass_m1:>14.1f} | {pass_v2:>14.1f} | {pass_v2 - pass_m1:>+16.1f}")

if __name__ == "__main__":
    analyze_fingerprint()
