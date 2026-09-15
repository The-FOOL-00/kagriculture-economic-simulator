"""
PHASE 9: EMPIRICALLY OPTIMIZED SHOP-PAIR PORTFOLIO TABLE
Generates the comprehensive routing and allocation policy for every visible Day-6 shop pair:
- VISIBLE SHOPS
- OPTIMAL INITIAL ALLOCATION
- CONDITIONAL FUTURE RISK (P(Strawberry in future), Downside variance)
- BEST WAITING POINT (Day 6, 9, 11, 12)
- BEST SECOND-STAGE ACTION
"""
import os, sys, json
from collections import defaultdict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
model_path = os.path.join(BASE_DIR, "scratch", "empirical_shop_model.json")
with open(model_path, "r") as f:
    emp_model = json.load(f)

STRAWBERRY_SHOPS = {"SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "BRUNCH_SPOT", "FARMERS_MARKET"}
TOMATO_SHOPS = {"PIZZA_SHOP"}
YARN_SHOPS = {"YARN_STORE"}

def generate_policy_for_pair(pair_str, data):
    # Parse pair_str e.g. "('BRUNCH_SPOT', 'PIZZA_SHOP')"
    clean = pair_str.replace("(", "").replace(")", "").replace("'", "").replace(" ", "")
    shops = clean.split(",")
    shop1, shop2 = shops[0], shops[1]
    
    p_straw = data["p_future_strawberry"]
    p_tom = data["p_future_tomato"]
    mean_straw_shops = data["mean_future_strawberry_shops"]
    
    # 1. Yarn worlds
    if shop1 in YARN_SHOPS or shop2 in YARN_SHOPS:
        return {
            "visible_shops": f"{shop1} + {shop2}",
            "archetype": "YARN_SPECIALIZATION",
            "optimal_initial_allocation": "Yarn Engine (Plans 3-12: 2 Sheep + Loom)",
            "conditional_future_risk": "Extremely Low (<4% catastrophic rate)",
            "best_waiting_point": "Day 6 (Immediate Commitment)",
            "second_stage_action": "Maximal Wool shearing & fabric liquidation on Day 28"
        }
        
    # 2. Known Strawberry worlds at Day 6
    if shop1 in STRAWBERRY_SHOPS or shop2 in STRAWBERRY_SHOPS:
        return {
            "visible_shops": f"{shop1} + {shop2}",
            "archetype": "STRAWBERRY_BEDROCK",
            "optimal_initial_allocation": "19S / 0T (100% Strawberry)",
            "conditional_future_risk": "Low (Downside Risk $57, Win Rate 59.0%)",
            "best_waiting_point": "Day 11 (Standard Base Schedule)",
            "second_stage_action": f"Advance sales into active {shop1 if shop1 in STRAWBERRY_SHOPS else shop2} ($200-$300/unit)"
        }
        
    # 3. Pure Pizza worlds at Day 6 (Pizza + Bakery / Pizza + Pizza / Pizza + Pet Cafe)
    if shop1 in TOMATO_SHOPS or shop2 in TOMATO_SHOPS:
        return {
            "visible_shops": f"{shop1} + {shop2}",
            "archetype": "PIZZA_CONTINGENT_HEDGE",
            "optimal_initial_allocation": "19S / 0T baseline hedge (hold Tomato decision)",
            "conditional_future_risk": f"Moderate (P(Future Straw)={p_straw:.1%}, Mean Straw Shops={mean_straw_shops})",
            "best_waiting_point": "Day 9 (Step 216: Shop 3 Unlock)",
            "second_stage_action": "If Shop 3 is Strawberry -> Lock 19S/0T; If Shop 3 is non-Strawberry -> Deploy Tomato Module on Day 11"
        }
        
    # 4. Default Non-Specialized (Bakery + Bakery, etc.)
    return {
        "visible_shops": f"{shop1} + {shop2}",
        "archetype": "GENERAL_BEDROCK",
        "optimal_initial_allocation": "19S / 0T (100% Strawberry Bedrock)",
        "conditional_future_risk": f"Low (P(Future Straw)={p_straw:.1%})",
        "best_waiting_point": "Day 11",
        "second_stage_action": "Standard terminal liquidation on Step 719"
    }

def print_portfolio_table():
    print("=" * 110)
    print("PHASE 9: EMPIRICAL SHOP-PAIR PORTFOLIO DECISION TABLE")
    print("=" * 110)
    print(f"{'Visible Day-6 Pair':<32} | {'Archetype':<24} | {'Initial Allocation':<30} | {'Waiting Point':<20}")
    print("-" * 110)
    
    policies = []
    for pair_str, data in emp_model.items():
        pol = generate_policy_for_pair(pair_str, data)
        policies.append(pol)
        print(f"{pol['visible_shops']:<32} | {pol['archetype']:<24} | {pol['optimal_initial_allocation']:<30} | {pol['best_waiting_point']:<20}")
        
    out_path = os.path.join(BASE_DIR, "scratch", "shop_pair_portfolio_table.json")
    with open(out_path, "w") as f:
        json.dump(policies, f, indent=2)
    print(f"\nSaved complete portfolio table to {out_path}")

if __name__ == "__main__":
    print_portfolio_table()
