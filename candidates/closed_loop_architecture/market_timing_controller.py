"""
MARKET TIMING CONTROLLER
Optimizes market sales by exploiting:
1. Deterministic shop pull cycles (steps t == 1 mod 4 execute immediately after town shop drain).
2. Real-time market price multipliers (P_current / P_base).
3. Micro-batching of nonlinear commodities (Strawberry, Milk, Wool) to minimize price slippage.
4. Holding safe inventory of shop-demanded commodities during price troughs.
"""
from typing import Dict, List, Any, Set, Tuple

PRODUCTS = (
    "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
    "EGG", "MILK", "WOOL", "FERTILIZER",
)

BASE_PRICES = {
    "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120,
    "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100
}

SHOP_ITEMS = {
    "BAKERY": {"EGG", "WHEAT"},
    "BRUNCH_SPOT": {"EGG", "WHEAT", "STRAWBERRY"},
    "FARMERS_MARKET": {"WHEAT", "CARROT", "TOMATO", "STRAWBERRY"},
    "ICE_CREAM_SHOP": {"STRAWBERRY", "MILK", "WHEAT"},
    "PET_CAFE": {"CARROT"},
    "PIZZA_SHOP": {"MILK", "TOMATO", "WHEAT"},
    "SMOOTHIE_SHOP": {"STRAWBERRY", "MILK"},
    "YARN_STORE": {"WOOL"},
}

# Max batch size per sell order to prevent nonlinear price collapse
MAX_BATCH_SIZES = {
    "STRAWBERRY": 6,
    "MILK": 6,
    "WOOL": 5,
    "MELON": 8,
    "TOMATO": 10,
    "CARROT": 12,
    "EGG": 12,
    "WHEAT": 15,
    "FERTILIZER": 15
}

class MarketTimingController:
    def __init__(self, enable_timing: bool = True, enable_microbatch: bool = True):
        self.enable_timing = enable_timing
        self.enable_microbatch = enable_microbatch
        self.pending_sales: Dict[str, int] = {}
        self.diagnostics = {
            "sales_timed_post_pull": 0,
            "batches_split": 0,
            "sales_held_for_recovery": 0,
            "units_liquidated_at_peak": 0
        }

    def get_shop_demands(self, unlocked_shops: List[str]) -> Set[str]:
        demands = set()
        for s in unlocked_shops:
            if s in SHOP_ITEMS:
                demands.update(SHOP_ITEMS[s])
        return demands

    def optimize_sales(
        self,
        raw_market_orders: List[List[Any]],
        obs: Dict[str, Any],
        projected_stock: Dict[str, int],
        feed_reserve: int,
        is_jit_overflow: bool
    ) -> List[List[Any]]:
        """
        Refines market orders:
        - Non-sell orders (HIRE, BUY_SEED, etc.) are passed through unchanged.
        - Sell orders are evaluated against shop demand, current price, and step % 4.
        """
        if not self.enable_timing:
            return raw_market_orders

        step = int(obs.get("step", 0))
        hour = step % 24
        day = step // 24
        unlocked_shops = obs.get("town", {}).get("unlocked_shops", [])
        shop_demands = self.get_shop_demands(unlocked_shops)
        prices = obs.get("market", {}).get("prices", {})
        
        non_sells = []
        planned_sells: Dict[str, int] = {}
        
        for ord_item in raw_market_orders:
            if not ord_item:
                continue
            op = str(ord_item[0]).upper()
            if op == "SELL" and len(ord_item) >= 3:
                item = ord_item[1]
                qty = max(0, int(ord_item[2]))
                planned_sells[item] = planned_sells.get(item, 0) + qty
            else:
                non_sells.append(ord_item)

        # Merge in previously deferred pending sales
        for item, p_qty in list(self.pending_sales.items()):
            if p_qty > 0:
                planned_sells[item] = planned_sells.get(item, 0) + p_qty
        self.pending_sales.clear()

        # If last day or JIT overflow, execute all sells immediately
        if step >= 716 or is_jit_overflow:
            immediate_sells = []
            for item, qty in planned_sells.items():
                if qty > 0:
                    avail = projected_stock.get(item, 0)
                    if item == "WHEAT":
                        avail = max(0, avail - feed_reserve)
                    actual_sell = min(qty, avail)
                    if actual_sell > 0:
                        immediate_sells.append(["SELL", item, actual_sell])
            return non_sells + immediate_sells

        # Market Timing & Micro-Batching Logic:
        # Step % 4 == 1 is the golden step (immediately after town shop drain)
        is_post_drain_step = (step % 4 == 1)
        optimized_sells = []

        for item, qty in planned_sells.items():
            if qty <= 0:
                continue
                
            avail = projected_stock.get(item, 0)
            if item == "WHEAT":
                avail = max(0, avail - feed_reserve)
            qty = min(qty, avail)
            if qty <= 0:
                continue

            base_p = BASE_PRICES.get(item, 100)
            curr_p = prices.get(item, base_p)
            has_shop = (item in shop_demands)
            
            # Rule 1: If item has shop demand and current price is depressed (< 0.9 * base)
            # and it is NOT a post-drain step, defer sale until step % 4 == 1
            if has_shop and curr_p < 0.9 * base_p and not is_post_drain_step:
                # Defer to next cycle
                self.pending_sales[item] = qty
                self.diagnostics["sales_held_for_recovery"] += qty
                continue

            # Rule 2: If it IS post-drain step OR price is high (>= base_p) OR no shop demand
            if self.enable_microbatch:
                max_batch = MAX_BATCH_SIZES.get(item, 10)
                # On post-drain step, allow up to 1.5x max_batch
                if is_post_drain_step:
                    max_batch = int(max_batch * 1.5)
                    self.diagnostics["sales_timed_post_pull"] += 1
                
                sell_now = min(qty, max_batch)
                defer_later = qty - sell_now
                
                if sell_now > 0:
                    optimized_sells.append(["SELL", item, sell_now])
                    self.diagnostics["units_liquidated_at_peak"] += sell_now
                if defer_later > 0:
                    self.pending_sales[item] = defer_later
                    self.diagnostics["batches_split"] += 1
            else:
                optimized_sells.append(["SELL", item, qty])

        return non_sells + optimized_sells
