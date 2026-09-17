import sys, os
sys.path.insert(0, os.path.abspath("."))

import copy
from aec.config import AECConfig, ENABLED_FOUNDATION_MECHANISMS
from aec.ir.economic_state import EconomicState
from aec.ir.farm_state import FarmState
from aec.ir.worker_state import WorkerState, WorkerEntity
from aec.ir.market_state import MarketState
from aec.ir.opponent_state import OpponentState
from aec.opportunities import OpportunityEngine
from aec.opportunities.route import RouteOpportunityAnalyzer
from aec.opportunities.market import MarketOpportunityAnalyzer
from aec.opportunities.terminal import TerminalOpportunityAnalyzer
from aec.patches.generator import PatchGenerator
from aec.patches.pruning import prune_patches
from aec.counterfactual.simulator import CounterfactualSimulator
from aec.evaluation.win_model import WinModel
from aec.safety.checks import SafetyChecker

config = AECConfig()

print("ENABLED FOUNDATION MECHANISMS:", config.enabled_mechanisms)

# -------------------------------------------------------------
# 1. LOCAL_WEED_DIG
# -------------------------------------------------------------
print("\n" + "="*60)
print("MECHANISM 1: LOCAL_WEED_DIG")
print("="*60)

# Build a mock EconomicState where worker 0 is standing on a weed tile
tiles = [[{"kind": "SOIL"} for _ in range(20)] for _ in range(20)]
tiles[5][5] = {"kind": "WEED"}

workers = [WorkerEntity(worker_id=0, position=(5, 5), cargo={}, deposit_path_len=5)]
farm = FarmState(tiles=tiles, cash=1000.0, shed_inventory={})
market = MarketState(current_prices={"WHEAT": 10}, market_inventory={}, unlocked_shops=[], steps_to_town_tick=0)
opp = OpponentState(observed_cash=1000.0)
state_weed = EconomicState(step=100, day=0, hour=10, player=0, phase="MID", remaining_horizon=619,
                           terminal_distance=619, workers=WorkerState(workers=workers), farm=farm,
                           market=market, opponent=opp, crop_feasibility={})

route_analyzer = RouteOpportunityAnalyzer()
opps_weed = route_analyzer.analyze(state_weed, [])
print(f"1. Opportunity Detected: {len(opps_weed)} -> {opps_weed}")

gen = PatchGenerator(config=config)
patches_weed = gen.generate_patches(opps_weed, state_weed, {"farmer": ["PASS"], "hands": [], "market": []}, config=config)
print(f"2. Patches Generated: {len(patches_weed)} -> {patches_weed}")

pruned_weed = prune_patches(patches_weed, state_weed)
print(f"3. Pruning Output: {len(pruned_weed)} -> {pruned_weed}")

sim = CounterfactualSimulator()
if pruned_weed:
    outcome_weed = sim.evaluate(pruned_weed[0], {"farmer": ["PASS"], "hands": [], "market": []}, state_weed, horizon=4)
    print(f"4. Simulation Outcome:")
    print(f"   delta_our_money: {outcome_weed.delta_our_money}")
    print(f"   delta_opp_money: {outcome_weed.delta_opponent_money}")
    print(f"   delta_terminal_margin: {outcome_weed.delta_terminal_margin}")
    
    checker = SafetyChecker()
    passed_safety, checks, reason = checker.verify(pruned_weed[0], outcome_weed, state_weed, {"farmer": ["PASS"]})
    print(f"5. Safety Verification: passed={passed_safety}, reason={reason}")
    
    wm = WinModel()
    eval_weed = wm.evaluate(pruned_weed[0], outcome_weed, state_weed)
    print(f"6. WinModel Evaluation: is_superior={eval_weed.is_superior}, rationale='{eval_weed.rationale}'")
    print(f"7. Commit Decision: {passed_safety and eval_weed.is_superior}")

# -------------------------------------------------------------
# 2. FRONTLOAD_ORDERS
# -------------------------------------------------------------
print("\n" + "="*60)
print("MECHANISM 2: FRONTLOAD_ORDERS")
print("="*60)

# Scenario A: Baseline has HIRE then BUY_LAND (no SELL)
market_analyzer = MarketOpportunityAnalyzer()
base_act_nosell = {"farmer": ["PASS"], "hands": [], "market": [["HIRE"], ["BUY_LAND", 2, 2]]}
opps_m1 = market_analyzer.analyze(state_weed, [], base_act_nosell)
print(f"Scenario A (No SELL orders):")
print(f"1. Opportunity Detected: {len(opps_m1)} -> {opps_m1}")
patches_m1 = gen.generate_patches(opps_m1, state_weed, base_act_nosell, config=config)
print(f"2. Patches Generated: {len(patches_m1)}")

# Scenario B: Baseline has HIRE then SELL
farm_strawberry = FarmState(tiles=tiles, cash=1000.0, shed_inventory={"STRAWBERRY": 5})
state_strawberry = EconomicState(step=121, day=1, hour=1, player=0, phase="MID", remaining_horizon=598,
                                terminal_distance=598, workers=WorkerState(workers=workers), farm=farm_strawberry,
                                market=MarketState(current_prices={"STRAWBERRY": 100}, market_inventory={}, unlocked_shops=[], steps_to_town_tick=0),
                                opponent=opp, crop_feasibility={})
base_act_sell = {"farmer": ["PASS"], "hands": [], "market": [["HIRE"], ["SELL", "STRAWBERRY", 2]]}
opps_m2 = market_analyzer.analyze(state_strawberry, [], base_act_sell)
print(f"\nScenario B (HIRE then SELL):")
print(f"1. Opportunity Detected: {len(opps_m2)} -> {opps_m2}")
patches_m2 = gen.generate_patches(opps_m2, state_strawberry, base_act_sell, config=config)
print(f"2. Patches Generated: {len(patches_m2)} -> {patches_m2}")
pruned_m2 = prune_patches(patches_m2, state_strawberry)
print(f"3. Pruning Output: {len(pruned_m2)} -> {pruned_m2}")
if pruned_m2:
    outcome_m2 = sim.evaluate(pruned_m2[0], base_act_sell, state_strawberry, horizon=4)
    print(f"4. Simulation Outcome:")
    print(f"   delta_our_money: {outcome_m2.delta_our_money}")
    print(f"   delta_opp_money: {outcome_m2.delta_opponent_money}")
    print(f"   delta_terminal_margin: {outcome_m2.delta_terminal_margin}")
    passed_safety, checks, reason = checker.verify(pruned_m2[0], outcome_m2, state_strawberry, base_act_sell)
    print(f"5. Safety Verification: passed={passed_safety}, reason={reason}")
    eval_m2 = wm.evaluate(pruned_m2[0], outcome_m2, state_strawberry)
    print(f"6. WinModel Evaluation: is_superior={eval_m2.is_superior}, rationale='{eval_m2.rationale}'")
    print(f"7. Commit Decision: {passed_safety and eval_m2.is_superior}")

# -------------------------------------------------------------
# 3. TERMINAL_LIQUIDATION
# -------------------------------------------------------------
print("\n" + "="*60)
print("MECHANISM 3: TERMINAL_LIQUIDATION")
print("="*60)

term_analyzer = TerminalOpportunityAnalyzer()
# Step 718 with shed_total = 0 (baseline already liquidated)
farm_empty_shed = FarmState(tiles=tiles, cash=50000.0, shed_inventory={})
state_718_empty = EconomicState(step=718, day=5, hour=23, player=0, phase="LATE", remaining_horizon=0,
                                terminal_distance=0, workers=WorkerState(workers=workers), farm=farm_empty_shed,
                                market=market, opponent=opp, crop_feasibility={"WHEAT": False, "CARROT": False, "STRAWBERRY": False, "MELON": False, "PUMPKIN": False})
opps_t_empty = term_analyzer.analyze(state_718_empty, [])
print(f"Step 718 with shed_total = 0:")
print(f"1. Opportunities Detected: {len(opps_t_empty)}")
for o in opps_t_empty:
    print(f"   {o.candidate_transformation_family}: {o.opportunity_id}")

# Step 718 with shed_total > 0
farm_full_shed = FarmState(tiles=tiles, cash=50000.0, shed_inventory={"STRAWBERRY": 10})
state_718_full = EconomicState(step=718, day=5, hour=23, player=0, phase="LATE", remaining_horizon=0,
                               terminal_distance=0, workers=WorkerState(workers=workers), farm=farm_full_shed,
                               market=MarketState(current_prices={"STRAWBERRY": 50}, market_inventory={}, unlocked_shops=[], steps_to_town_tick=0),
                               opponent=opp, crop_feasibility={"WHEAT": False, "CARROT": False, "STRAWBERRY": False, "MELON": False, "PUMPKIN": False})
opps_t_full = term_analyzer.analyze(state_718_full, [])
print(f"\nStep 718 with shed_total = 10:")
print(f"1. Opportunities Detected: {len(opps_t_full)}")
for o in opps_t_full:
    print(f"   {o.candidate_transformation_family}: {o.opportunity_id}")
patches_t_full = gen.generate_patches(opps_t_full, state_718_full, {"farmer": ["PASS"], "hands": [], "market": []}, config=config)
print(f"2. Patches Generated: {len(patches_t_full)}")
for p in patches_t_full:
    print(f"   {p.mechanism_family}: {p.patch_id}, mutations={p.market_mutations}")

# -------------------------------------------------------------
# 4. PHASE_SHUTDOWN
# -------------------------------------------------------------
print("\n" + "="*60)
print("MECHANISM 4: PHASE_SHUTDOWN")
print("="*60)

# Baseline doesn't buy dead crop seeds
state_shutdown = EconomicState(step=600, day=5, hour=0, player=0, phase="LATE", remaining_horizon=118,
                               terminal_distance=118, workers=WorkerState(workers=workers), farm=farm,
                               market=market, opponent=opp, crop_feasibility={"WHEAT": True, "CARROT": True, "STRAWBERRY": True, "MELON": False, "PUMPKIN": False})
opps_ps = term_analyzer.analyze(state_shutdown, [])
print(f"1. Opportunities Detected at step 600: {len(opps_ps)}")
for o in opps_ps:
    print(f"   {o.candidate_transformation_family}: {o.opportunity_id}")

base_act_normal = {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", "WHEAT", 2]]}
patches_ps_normal = gen.generate_patches(opps_ps, state_shutdown, base_act_normal, config=config)
print(f"2a. Patches Generated when baseline buys WHEAT (not dead MELON): {len(patches_ps_normal)}")

base_act_bad = {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", "MELON", 2]]}
patches_ps_bad = gen.generate_patches(opps_ps, state_shutdown, base_act_bad, config=config)
print(f"2b. Patches Generated when baseline buys MELON (dead crop): {len(patches_ps_bad)} -> {patches_ps_bad}")
