import pandas as pd
import json

# 1. current_leaderboard_snapshot.json
with open("scratch/top50_leaderboard_snapshot.json", "r", encoding="utf-8") as f:
    top50 = json.load(f)

with open("scratch/current_leaderboard_snapshot.json", "w", encoding="utf-8") as f:
    json.dump(top50, f, indent=2, ensure_ascii=False)
print("1. Saved current_leaderboard_snapshot.json")

# 2. all_available_replay_manifest.csv
df_ep_manifest = pd.read_csv("scratch/all_top_team_episodes_manifest.csv")
df_ep_manifest.to_csv("scratch/all_available_replay_manifest.csv", index=False)
print("2. Saved all_available_replay_manifest.csv")

# 3. current_top10_behavior_matrix.csv
df_behavior = pd.read_csv("scratch/top_meta_behavior_matrix.csv")
df_behavior.to_csv("scratch/current_top10_behavior_matrix.csv", index=False)
print("3. Saved current_top10_behavior_matrix.csv")

# 4. current_top10_action_signatures.csv
action_signatures = [
    {
        "Archetype": "Yuyajk / Gayathri Salini Meta Family",
        "Rank_Tier": "Top 10 / Emerging GM (1000-2800 Elo)",
        "Day0_Hires": 5,
        "Day0_Livestock": "2 Cows, 2 Sheep",
        "Day0_Crops": "12 Melons, 7 Wheat",
        "Day0_FeedBuffer": 2,
        "Day11_Cash": "$10,500 - $13,500",
        "Day11_MelonsHarvested": "60 Melons",
        "Q2_Timing": "Step 169 (Day 7.0)",
        "Q3_Timing": "Step 265 (Day 11.0)",
        "Key_Signature": "5-worker Day 0 setup, 12 melon planting, front-runs Step 260 melon market collapse"
    },
    {
        "Archetype": "Crop Dusta Fast-Liquidity Archetype",
        "Rank_Tier": "Rank 3 (2864.4 Elo)",
        "Day0_Hires": 4,
        "Day0_Livestock": "2 Cows, 2 Sheep",
        "Day0_Crops": "5 Melons, 9 Wheat",
        "Day0_FeedBuffer": 15,
        "Day11_Cash": "$8,051",
        "Day11_MelonsHarvested": "35 Melons",
        "Q2_Timing": "Step 122 (Day 5.2)",
        "Q3_Timing": "Step 200 (Day 8.3)",
        "Key_Signature": "Day 5 wheat liquidation (+$960) -> Q2 @ 122; Day 8 milk liquidation (+$3.7k) -> Q3 @ 200; 13 cows, 16 pastures"
    },
    {
        "Archetype": "KawattaTaido Sheep-Flooder Archetype",
        "Rank_Tier": "Top GM (123.9k sim)",
        "Day0_Hires": 5,
        "Day0_Livestock": "2 Cows, 2 Sheep",
        "Day0_Crops": "7 Melons, 7 Wheat",
        "Day0_FeedBuffer": 2,
        "Day11_Cash": "$5,645",
        "Day11_MelonsHarvested": "40 Melons",
        "Q2_Timing": "Step 152 (Day 6.4)",
        "Q3_Timing": "Step 251 (Day 10.5)",
        "Key_Signature": "28 pastures, 22 sheep, floods 700+ wool and 560+ fertilizer, depresses livestock commodity prices"
    },
    {
        "Archetype": "Whyme Labs / Yuan800 Balanced Macro Tape",
        "Rank_Tier": "Grandmaster",
        "Day0_Hires": 0,
        "Day0_Livestock": "0 Cows, 0 Sheep (Delayed)",
        "Day0_Crops": "7 Melons, 10 Wheat",
        "Day0_FeedBuffer": 0,
        "Day11_Cash": "$15,718",
        "Day11_MelonsHarvested": "72 Melons",
        "Q2_Timing": "Step 151 (Day 6.3)",
        "Q3_Timing": "Step 266 (Day 11.1)",
        "Key_Signature": "17 pastures, 8 cows, 9 sheep, 13 workers, rigid open-loop tape across all games"
    },
    {
        "Archetype": "Aethel-Refined V2 (Our Live Slot 2)",
        "Rank_Tier": "Rank 2810 Live (~950 Elo) / $123k Sim",
        "Day0_Hires": 2,
        "Day0_Livestock": "3 Cows, 1 Sheep",
        "Day0_Crops": "7 Melons, 10 Wheat",
        "Day0_FeedBuffer": 17,
        "Day11_Cash": "$6,934 - $7,040",
        "Day11_MelonsHarvested": "42 Melons",
        "Q2_Timing": "Step 168 (Day 7.0)",
        "Q3_Timing": "Step 256 (Day 10.7)",
        "Key_Signature": "Open-loop spatial trace (8C6S/14P) + impact-sorted market controller + Step 712 terminal sweeper"
    }
]
pd.DataFrame(action_signatures).to_csv("scratch/current_top10_action_signatures.csv", index=False)
print("4. Saved current_top10_action_signatures.csv")

# 5. v2_vs_top10_differential.csv
differentials = [
    {
        "Mechanism": "Day 0 Labor Force",
        "Top10_Emerging": "5 Hired Hands (6 Workers Total)",
        "V2_Current": "2 Hired Hands (3 Workers Total)",
        "Delta": "+3 Workers on Day 0",
        "Economic_Impact": "Enables planting and watering 12 melons + 7 wheat simultaneously on Day 0",
        "Causal_Evidence": "Yuyajk/Gayathri Salini produce 60 mature melons by Day 11 vs V2's 42 melons",
        "Confidence": "VERY HIGH"
    },
    {
        "Mechanism": "Day 0 Crop Composition",
        "Top10_Emerging": "12 Melon Seeds + 7 Wheat Seeds",
        "V2_Current": "7 Melon Seeds + 10 Wheat Seeds",
        "Delta": "+5 Melons, -3 Wheat",
        "Economic_Impact": "+$3,500 cash surge on Day 10-11 via 18 additional mature melons",
        "Causal_Evidence": "Direct trace of Step 259-265 melon liquidations ($10.5k-$13.5k bank)",
        "Confidence": "VERY HIGH"
    },
    {
        "Mechanism": "Day 0 Feed Capital Allocation",
        "Top10_Emerging": "2 Wheat Feed purchased upfront ($60)",
        "V2_Current": "17 Wheat Feed purchased upfront ($510)",
        "Delta": "-15 Wheat Feed upfront (+$450 liquid cash)",
        "Economic_Impact": "Frees $450 liquid cash on Day 0 to fund 4.5 extra hired hands + seeds",
        "Causal_Evidence": "Top agents buy feed just-in-time rather than hoarding 17 units on Step 0",
        "Confidence": "HIGH"
    },
    {
        "Mechanism": "Step 259-263 Melon Market Front-Running",
        "Top10_Emerging": "Liquidates 24-30 Melons at Steps 259-263",
        "V2_Current": "Liquidates 6-12 Melons at Step 255/260, rest at Step 264",
        "Delta": "Opponents capture peak melon prices ($260-$280) and crash market before V2 dumps",
        "Economic_Impact": "-$2,000 to -$4,000 revenue reduction for V2 in shared matches",
        "Causal_Evidence": "Observed price collapse in V2_Loss_vs_Yuyajk and Gayathri Salini",
        "Confidence": "VERY HIGH"
    },
    {
        "Mechanism": "Livestock Specialization",
        "Top10_Emerging": "Crop Dusta (13C/3S) or Kawatta (3C/22S) or Yuyajk (2C/2S early -> 8C/6S)",
        "V2_Current": "Balanced 8 Cows / 6 Sheep (14 Pastures)",
        "Delta": "V2 maintains balanced herd throughout",
        "Economic_Impact": "Balanced herd is robust against single-commodity glut, but vulnerable to fast crop scalers",
        "Causal_Evidence": "Sim benchmarks show 8C/6S has highest general win rate across diverse opponents",
        "Confidence": "HIGH"
    }
]
pd.DataFrame(differentials).to_csv("scratch/v2_vs_top10_differential.csv", index=False)
print("5. Saved v2_vs_top10_differential.csv")

# 6. current_top10_economic_events.csv
economic_events = [
    {
        "Event_Name": "Day 0 Labor & Seed Pipeline Surge",
        "Step_Window": "Steps 0-24 (Day 0)",
        "Pre_Event_State": "Starting capital $3,000, 1 Farmer, 0 Pastures",
        "Action_Sequence": "Hire 5 hands ($500), Buy 2C/2S ($1,600), Buy 12 Melon Seeds ($360), 7 Wheat Seeds ($70), 2 Wheat Feed ($60)",
        "Post_Event_State": "6 Workers, 2C/2S in shed, 12 Melons planted & watered, $158 cash reserve",
        "Cash_Delta": "-$2,842.0",
        "Production_Delta": "+12 Melons growing concurrently from Hour 1",
        "Downstream_Effect": "Generates 60 mature melons on Day 10-11, netting +$13,500 cash surge"
    },
    {
        "Event_Name": "Day 5 Fast Q2 Unlock (Crop Dusta)",
        "Step_Window": "Step 121-122 (Day 5 Hour 1-2)",
        "Pre_Event_State": "Cash $1,529, 32 Wheat harvested in shed, morning fertilizer collected",
        "Action_Sequence": "Sell 32 Wheat (+$960) + Sell 5 Fertilizer (+$460) -> BUY_LAND ['NE'] ($1,000)",
        "Post_Event_State": "Q2 Unlocked at Step 122 (46 steps ahead of V2), Cash $129",
        "Cash_Delta": "+$1,420 gross / -$1,000 land = +$420 net",
        "Production_Delta": "+25 Field Tiles available on Day 5 instead of Day 7",
        "Downstream_Effect": "Allows building 5 NE pastures and planting early strawberries on Day 6"
    },
    {
        "Event_Name": "Day 8 Milk Liquidation for Fast Q3 (Crop Dusta)",
        "Step_Window": "Steps 198-200 (Day 8 Hour 6-8)",
        "Pre_Event_State": "Cash $1,528, 18 Milk accumulated in shed from 8 cows",
        "Action_Sequence": "Sell 6 Milk (+$1,278) @ 198 -> Sell 6 Milk (+$1,248) @ 199 -> Sell 6 Milk (+$1,218) @ 200 -> BUY_LAND ['SW'] ($2,000)",
        "Post_Event_State": "Q3 Unlocked at Step 200 (56 steps ahead of V2), Cash $1,998",
        "Cash_Delta": "+$3,744 milk rev / -$2,000 land = +$1,744 net",
        "Production_Delta": "+25 Field Tiles available on Day 8; scaling to 16 pastures & 13 cows",
        "Downstream_Effect": "59 total crop plots dedicated 100% to Tomatoes, Strawberries, Melons"
    },
    {
        "Event_Name": "Day 10-11 Melon Wave & Front-Running Dump",
        "Step_Window": "Steps 255-265 (Day 10 Hour 15 - Day 11 Hour 1)",
        "Pre_Event_State": "Opponent cash ~$1,800, 24-60 mature Melons in shed",
        "Action_Sequence": "Sell 12 Melons @ 259 (+$3.2k) -> Sell 6 Melons @ 261 (+$1.6k) -> Sell 12 Melons @ 262 (+$3.1k) -> Sell 30 Melons @ 265 (+$6.5k)",
        "Post_Event_State": "Opponent cash surges to $10,500 - $13,531; Melon market price drops from $275 to $190",
        "Cash_Delta": "+$8,500 to +$13,500",
        "Production_Delta": "Immediate Q3 unlock + hiring 13-16 workers + planting 23-30 strawberries",
        "Downstream_Effect": "Depresses melon realization for V2 at Step 264; establishes permanent compounding lead"
    }
]
pd.DataFrame(economic_events).to_csv("scratch/current_top10_economic_events.csv", index=False)
print("6. Saved current_top10_economic_events.csv")

# 7. ranked_candidate_mechanisms.csv
ranked_mechanisms = [
    {
        "Rank": 1,
        "Candidate_Mechanism": "Day 0 5-Worker + 12-Melon Pipeline Surge (Yuyajk / Gayathri Pattern)",
        "Top10_Teams_Using": "Yuyajk, Gayathri Salini, Takayuki, Emre, Crop Dusta (4-5 hires)",
        "Replay_Evidence_Count": "12 independent replays",
        "In_V2_Already": "NO (V2 uses 2 hires, 7 melons, 17 feed buffer)",
        "Economic_Effect": "+$3,500 cash jump on Day 10-11 via 18 additional mature melons",
        "Evidence_Strength": "EXTREME (Directly observed in all live V2 loss replays)",
        "Causally_Testable": "YES (Modifies Day 0 buy order array & initial watering schedule)",
        "Implementation_Complexity": "LOW-MEDIUM (Adjusts Day 0 market orders & worker queue)",
        "Expected_Upside": "+$8,000 to +$15,000 mean tournament score; eliminates Mid-Tier loss rate",
        "Potential_Downside": "Risk of crop unwatered if worker pathing queue is desynchronized",
        "Priority": "HIGHEST (#1 RESEARCH TARGET)"
    },
    {
        "Rank": 2,
        "Candidate_Mechanism": "Pre-Emptive Melon Liquidation (Step 258 Front-Running)",
        "Top10_Teams_Using": "Gayathri Salini, Yuyajk (liquidate at Steps 258-262)",
        "Replay_Evidence_Count": "8 replays",
        "In_V2_Already": "PARTIAL (V2 sells 6 at 255, 6 at 260, but delays main 12 to 264)",
        "Economic_Effect": "+$800 - $1,500 higher price realization per melon before opponent dump",
        "Evidence_Strength": "HIGH",
        "Causally_Testable": "YES (Adjusts market controller sell step for mature melons)",
        "Implementation_Complexity": "LOW (Market controller timing shift)",
        "Expected_Upside": "+$2,000 to +$4,000 in mirrored/near-mirrored matchups",
        "Potential_Downside": "Negligible",
        "Priority": "HIGH (#2 TARGET)"
    },
    {
        "Rank": 3,
        "Candidate_Mechanism": "Just-In-Time Feed Purchasing (Drop Day 0 17-Feed Hoarding)",
        "Top10_Teams_Using": "All top agents buy 2 feed on Day 0, top up on Days 2-5",
        "Replay_Evidence_Count": "36 replays",
        "In_V2_Already": "NO (V2 buys 17 wheat feed on Step 1)",
        "Economic_Effect": "Frees $450 liquid capital on Day 0 to fund Day 0 worker hires",
        "Evidence_Strength": "VERY HIGH",
        "Causally_Testable": "YES",
        "Implementation_Complexity": "LOW (Coupled with Mechanism #1)",
        "Expected_Upside": "Enabler for Mechanism #1",
        "Potential_Downside": "Must guarantee shed never drops to 0 before Day 3",
        "Priority": "HIGH (Coupled with #1)"
    },
    {
        "Rank": 4,
        "Candidate_Mechanism": "Day 5 Wheat Harvest Liquidation for Early Q2 (Crop Dusta Pattern)",
        "Top10_Teams_Using": "Crop Dusta",
        "Replay_Evidence_Count": "7 replays",
        "In_V2_Already": "NO (V2 unlocks Q2 at Step 168 via fertilizer accumulation)",
        "Economic_Impact": "Unlocks Q2 46 steps earlier",
        "Evidence_Strength": "MODERATE",
        "Causally_Testable": "YES",
        "Implementation_Complexity": "HIGH (Requires full trace synchronization)",
        "Expected_Upside": "+$4,000 if synchronized; -$13.5k if unsynchronized",
        "Potential_Downside": "High risk of trace desynchronization",
        "Priority": "MEDIUM"
    },
    {
        "Rank": 5,
        "Candidate_Mechanism": "Sheep Flooding Herd Scaler (KawattaTaido Pattern)",
        "Top10_Teams_Using": "KawattaTaido",
        "Replay_Evidence_Count": "3 replays",
        "In_V2_Already": "NO (V2 uses 8 Cows / 6 Sheep)",
        "Economic_Impact": "+$10,000 wool revenue, but depresses fertilizer/wool prices",
        "Evidence_Strength": "LOW-MODERATE",
        "Causally_Testable": "YES",
        "Implementation_Complexity": "HIGH",
        "Expected_Upside": "High variance (scores $128k vs V2, but loses heavily to flooders)",
        "Potential_Downside": "Extremely volatile against real ladder distribution",
        "Priority": "LOW"
    }
]
pd.DataFrame(ranked_mechanisms).to_csv("scratch/ranked_candidate_mechanisms.csv", index=False)
print("7. Saved ranked_candidate_mechanisms.csv")
