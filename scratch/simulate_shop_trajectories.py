"""
Simulate town shop inventory drain and market price trajectories across all shop archetypes.
"""
import sys
sys.path.insert(0, '.')
from scratch.market_dynamics_model import (
    ITEMS, ITEM_IDS, MARKET_PARAMS, MARKET_AMPS, market_price, SHOP_ITEMS
)

SHOP_ARCHETYPES = {
    'Pet Cafe (Carrot heavy)': ['PET_CAFE', 'PET_CAFE'],
    'Pizza + Pizza (Tomato + Milk heavy)': ['PIZZA_SHOP', 'PIZZA_SHOP'],
    'Yarn + Yarn (Wool heavy)': ['YARN_STORE', 'YARN_STORE'],
    'Bakery + Brunch (Egg + Wheat heavy)': ['BAKERY', 'BRUNCH_SPOT'],
    'Ice Cream + Smoothie (Strawberry + Milk heavy)': ['ICE_CREAM_SHOP', 'SMOOTHIE_SHOP'],
    'Farmers Market + Pet Cafe': ['FARMERS_MARKET', 'PET_CAFE'],
    'Non-Yarn Control (No shop demand for Strawberries/Milk)': ['BAKERY', 'PET_CAFE'],
}

def analyze_shop_archetype_impact():
    print("="*80)
    print("PHASE 3: SHOP CONSUMPTION DYNAMICS & PRICE TRAJECTORIES")
    print("="*80)
    
    # Analyze total consumption over 720 steps assuming 2 shops unlocked on Day 3 & Day 6
    for arch_name, shops in SHOP_ARCHETYPES.items():
        inv = {item: 10000 for item in ITEMS}
        
        # Track drain over 720 steps
        # Day 3 = step 72, Day 6 = step 144
        active_shops = []
        for step in range(720):
            if step == 72:
                active_shops.append(shops[0])
            elif step == 144:
                active_shops.append(shops[1])
                
            # Shop pull every 4 steps
            if step % 4 == 0 and active_shops:
                for s in active_shops:
                    items_dict = SHOP_ITEMS[s]
                    for it, mult in items_dict.items():
                        inv[it] -= mult
                        
            # Center pull every 24 steps
            if step % 24 == 0:
                for it in ITEMS:
                    if it != 'FERTILIZER':
                        inv[it] -= 1
                        
        print(f"\nArchetype: {arch_name} (Shops: {shops})")
        print(f"{'Item':<12} | {'Initial':<8} | {'Final Inv':<10} | {'Deficit':<8} | {'Base Price':<11} | {'Final Price':<12} | {'Multiplier':<10}")
        print("-" * 80)
        for it in ITEMS:
            it_idx = ITEM_IDS[it]
            base_p = MARKET_PARAMS[it_idx][0]
            fin_p = market_price(it_idx, inv[it])
            deficit = 10000 - inv[it]
            mult = fin_p / base_p
            if deficit > 30 or mult > 1.05:
                print(f"{it:<12} | {10000:<8} | {inv[it]:<10} | {deficit:<8} | ${base_p:<10.0f} | ${fin_p:<11.0f} | {mult:>8.2f}x")

if __name__ == '__main__':
    analyze_shop_archetype_impact()
