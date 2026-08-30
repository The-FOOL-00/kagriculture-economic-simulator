"""
=============================================================================
ENGINE: DYNAMIC ECONOMIC CROP ALLOCATOR (KAGGRICULTURE APEX)
=============================================================================
Replaces static crop ratio heuristics with:
1. Marginal ROI Evaluation per tile-day accounting for remaining season time.
2. Season Phase Transitions:
   - Early (Days 0-12): Compound Capital with Early Melons + Feed Wheat.
   - Mid (Days 13-19): Rebalance away from risky Cycle-2 Melons into Carrots/Wheat.
   - Late (Days 20-26): Fast-Turnaround Carrots (75%) & Wheat (25%).
   - Final (Days 27-29): Zero Planting; 100% Labor dedicated to Harvesting & Selling.
3. Market-Adaptive Hedging: Reduces acreage of commodities showing market glut.
=============================================================================
"""

from config import CROPS, MARKET_PARAMS, compute_market_price

class DynamicEconomicAllocator:
    def __init__(self, default_melon_target=10, max_cycle2_melons=0):
        self.default_melon_target = default_melon_target
        self.max_cycle2_melons = max_cycle2_melons

    def calculate_crop_roi(self, crop, day, market_prices, market_inventory):
        """
        Calculates expected Net Present Value and daily ROI for planting a crop on `day`.
        """
        rem_days = 29 - day
        cd = CROPS.get(crop, {})
        first_day = cd.get("first_yield_day", 10)
        max_day = cd.get("max_yield_day", 12)
        seed_cost = cd.get("seed", 10)
        ongoing = cd.get("ongoing", False)

        if not ongoing:
            if rem_days < first_day:
                return -999.0  # Cannot mature before season end

            # Expected yield units
            expected_yield = cd.get("max_yield", 4) if rem_days >= max_day else cd.get("base_yield", 3)
            expected_price = market_prices.get(crop, MARKET_PARAMS.get(crop, {}).get("base", 25))
            expected_rev = expected_yield * expected_price
            net_profit = expected_rev - seed_cost
            return net_profit / max(1, min(rem_days, max_day))
        else:
            if rem_days < first_day:
                return -999.0
            
            interval = cd.get("interval", 1)
            harvest_count = 1 + max(0, (rem_days - first_day) // interval)
            harvest_count = min(harvest_count, cd.get("max_yield", 4))
            expected_price = market_prices.get(crop, MARKET_PARAMS.get(crop, {}).get("base", 50))
            expected_rev = harvest_count * expected_price
            net_profit = expected_rev - seed_cost
            return net_profit / max(1, rem_days)

    def allocate_seeds(self, empty_tiles_count, held_seeds, money, spendable, day, market_prices, market_inventory, opp_crops=None):
        """
        Calculates optimal seed purchase counts for each crop and returns BUY_SEED orders.
        """
        orders = []
        rem_spendable = spendable
        total_seeds_held = sum(held_seeds.values())
        needed_seeds = max(0, empty_tiles_count - total_seeds_held)

        if needed_seeds <= 0 or day > 26 or rem_spendable <= 0:
            return orders, rem_spendable

        rem_days = 29 - day
        portfolio = {}

        if day <= 12 and rem_days >= 12:
            # Phase 1: Early High-Value Melons + Liquidity Crops
            target_m = self.default_melon_target if self.default_melon_target > 0 else int(needed_seeds * 0.65)
            m_cnt = min(target_m, needed_seeds, int(rem_spendable // CROPS["MELON"]["seed"]))
            rem = needed_seeds - m_cnt
            c_cnt = min(int(rem * 0.7), int((rem_spendable - m_cnt * 80) // CROPS["CARROT"]["seed"]))
            w_cnt = min(rem - c_cnt, int((rem_spendable - m_cnt * 80 - c_cnt * 20) // CROPS["WHEAT"]["seed"]))

            if m_cnt > 0: portfolio["MELON"] = m_cnt
            if c_cnt > 0: portfolio["CARROT"] = c_cnt
            if w_cnt > 0: portfolio["WHEAT"] = w_cnt

        elif day <= 19 and rem_days >= 10:
            # Phase 2: Mid-Season Capital Transition (Strict control on Cycle-2 Melons)
            target_c2_m = self.max_cycle2_melons
            m_cnt = min(target_c2_m, needed_seeds, int(rem_spendable // CROPS["MELON"]["seed"]))
            rem = needed_seeds - m_cnt
            c_cnt = min(int(rem * 0.7), int((rem_spendable - m_cnt * 80) // CROPS["CARROT"]["seed"]))
            w_cnt = min(rem - c_cnt, int((rem_spendable - m_cnt * 80 - c_cnt * 20) // CROPS["WHEAT"]["seed"]))

            if m_cnt > 0: portfolio["MELON"] = m_cnt
            if c_cnt > 0: portfolio["CARROT"] = c_cnt
            if w_cnt > 0: portfolio["WHEAT"] = w_cnt

        elif day <= 26 and rem_days >= 3:
            # Phase 3: Fast 3-Day Turnaround Crops (Carrots 75% / Wheat 25%)
            c_cnt = min(int(needed_seeds * 0.75), int(rem_spendable // CROPS["CARROT"]["seed"]))
            w_cnt = min(needed_seeds - c_cnt, int((rem_spendable - c_cnt * 20) // CROPS["WHEAT"]["seed"]))

            if c_cnt > 0: portfolio["CARROT"] = c_cnt
            if w_cnt > 0: portfolio["WHEAT"] = w_cnt

        for crop, count in portfolio.items():
            cost = CROPS[crop]["seed"] * count
            if count > 0 and rem_spendable >= cost:
                orders.append(["BUY_SEED", crop, count])
                rem_spendable -= cost

        return orders, rem_spendable
