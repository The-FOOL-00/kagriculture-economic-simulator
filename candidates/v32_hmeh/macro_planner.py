# SPDX-License-Identifier: MIT
"""HMEH Macro-Economic Planner Layer.

Generates StrategicIntent from EconomicState using deterministic event-driven
replanning across the 5 ablation stages (HMEH-0 through HMEH-4).
"""

from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Tuple

try:
    from config import HMEHConfig, LAND_PRICES, PRODUCTS, SEED_PRICES, fib_hire_cost
    from economic_state import EconomicState
    from strategies import StrategicIntent
except ImportError:
    from candidates.v32_hmeh.config import HMEHConfig, LAND_PRICES, PRODUCTS, SEED_PRICES, fib_hire_cost
    from candidates.v32_hmeh.economic_state import EconomicState
    from candidates.v32_hmeh.strategies import StrategicIntent


class MacroPlanner:
    def __init__(self, config: Optional[HMEHConfig] = None, stage: str = "HMEH-0"):
        self.cfg = config or HMEHConfig()
        self.stage = stage
        self.land_1_done = False
        self.land_2_done = False
        self.melon_seeds_bought = 0
        self.straw_seeds_bought = 0
        self.last_replan_event = None
        
    def plan(self, state: EconomicState) -> StrategicIntent:
        """Evaluates economic state and produces StrategicIntent."""
        step = state.step
        day = state.day
        hour = state.hour
        cash = state.cash
        spendable = max(0.0, cash - self.cfg.min_cash_reserve)
        market_orders: List[List[Any]] = []
        fallback_mode = "NORMAL"
        event_trigger = None
        reason = "routine"
        
        # ---------------------------------------------------------------------
        # EVENT 1: STEP 0 OPENING WASH (A7 MECHANISM PRESERVATION)
        # ---------------------------------------------------------------------
        if step == 0:
            event_trigger = "EVENT_BOOTSTRAP_STEP0"
            reason = "A7 30-wash capital preservation mechanism"
            market_orders = [
                ["BUY_PRODUCT", "WHEAT", 30],
                ["SELL", "WHEAT", 30]
            ]
            return StrategicIntent(
                objective="A7 Step 0 Wash Preservation",
                target_worker_count=1,
                crop_targets={"MELON": 12, "WHEAT": 0, "STRAWBERRY": 0},
                cow_target=0,
                sheep_target=0,
                min_cash_reserve=30.0,
                land_expansion_target=0,
                market_orders=market_orders,
                fallback_mode="NORMAL",
                stage=self.stage,
                reason=reason,
                event_trigger=event_trigger,
                metadata={"wash_size": 30}
            )

        # ---------------------------------------------------------------------
        # EVENT 2: STEPS 1–8 OPENING LIVESTOCK BOOTSTRAP
        # ---------------------------------------------------------------------
        if step == 1:
            event_trigger = "EVENT_LIVESTOCK_INIT"
            reason = "Initial labor burst (5 hands) for pasture setup"
            # In A7 / V3, 5 workers are hired at step 1
            for _ in range(5):
                market_orders.append(["HIRE"])
            return StrategicIntent(
                objective="Opening Livestock Setup",
                target_worker_count=6,
                crop_targets={"MELON": 12, "WHEAT": 0, "STRAWBERRY": 0},
                cow_target=0,
                sheep_target=1,
                min_cash_reserve=30.0,
                land_expansion_target=0,
                market_orders=market_orders,
                fallback_mode="NORMAL",
                stage=self.stage,
                reason=reason,
                event_trigger=event_trigger,
                metadata={"hires": 5}
            )

        # ---------------------------------------------------------------------
        # EVENT 3: WAGE RUNWAY STRESS
        # ---------------------------------------------------------------------
        if state.wage_runway_days < self.cfg.wage_runway_stress_threshold:
            fallback_mode = "CAUTION"
            event_trigger = "EVENT_RUNWAY_STRESS"
            reason = f"Wage runway low ({state.wage_runway_days:.1f} days); throttle spending"

        # ---------------------------------------------------------------------
        # EVENT 4: TERMINAL LIQUIDATION WINDOW (STEPS 712–718)
        # ---------------------------------------------------------------------
        if state.is_terminal_window:
            fallback_mode = "LIQUIDATION"
            event_trigger = "EVENT_TERMINAL_WINDOW"
            reason = "Final turns: convert all shed inventory into cash"
            
            # Dump all shed items into market
            for prod in PRODUCTS:
                qty = state.shed_inventory.get(prod, 0)
                if qty > 0 and len(market_orders) < self.cfg.max_market_orders:
                    market_orders.append(["SELL", prod, min(qty, 30)])
                    
            return StrategicIntent(
                objective="Terminal Liquidation",
                target_worker_count=state.active_workers,
                crop_targets={},
                cow_target=state.cow_count,
                sheep_target=state.sheep_count,
                min_cash_reserve=0.0,
                land_expansion_target=state.unlocked_quadrants - 1,
                market_orders=market_orders,
                fallback_mode=fallback_mode,
                stage=self.stage,
                reason=reason,
                event_trigger=event_trigger,
                metadata={"terminal_step": step}
            )

        # ---------------------------------------------------------------------
        # MECHANISM 1: LABOR TARGET
        # ---------------------------------------------------------------------
        total_chores_est = state.pending_chore_count + len(state.vacant_arable_tiles)
        
        if self.stage in ("HMEH-1", "HMEH-2", "HMEH-3", "HMEH-4") and self.cfg.labor_mode == "adaptive":
            # Adaptive Labor Scaling: hire only when chore queue justifies Fibonacci wage burden
            # and cash runway exceeds 2.5 days
            if state.wage_runway_days >= 2.5:
                # Dynamic formula: scales with actual pending chores and arable capacity
                if state.unlocked_quadrants == 1:
                    target_workers = min(6, max(2, (total_chores_est + 4) // 6))
                elif state.unlocked_quadrants == 2:
                    target_workers = min(self.cfg.max_workers, max(3, (total_chores_est + 6) // 7))
                else:
                    target_workers = min(self.cfg.max_workers, max(4, (total_chores_est + 8) // 8))
            else:
                target_workers = state.active_workers  # Freeze hiring under runway stress
        else:
            # Baseline (HMEH-0): Standard declarative labor curve
            if state.unlocked_quadrants == 1:
                target_workers = min(self.cfg.hire_initial_burst, max(2, (total_chores_est + 6) // 8))
            elif state.unlocked_quadrants == 2:
                target_workers = min(self.cfg.max_workers, max(3, (total_chores_est + 8) // 9))
            else:
                target_workers = min(self.cfg.max_workers, max(4, (total_chores_est + 10) // 10))

        # Check hiring orders at hour 0
        if hour == 0 and target_workers > state.active_workers:
            needed_hires = target_workers - state.active_workers
            avail_money = cash
            for _ in range(needed_hires):
                cost = fib_hire_cost(state.hires_today + len([o for o in market_orders if o[0] == "HIRE"]))
                if avail_money >= cost + self.cfg.min_cash_reserve:
                    market_orders.append(["HIRE"])
                    avail_money -= cost

        # ---------------------------------------------------------------------
        # MECHANISM 2: LAND EXPANSION
        # ---------------------------------------------------------------------
        n_unlocked = state.unlocked_quadrants - 1
        land_target = n_unlocked
        if n_unlocked == 0 and step >= self.cfg.land_1_step and not self.land_1_done:
            cost = LAND_PRICES[0]
            if cash >= cost + self.cfg.min_cash_reserve and len(market_orders) < self.cfg.max_market_orders:
                market_orders.append(["BUY_LAND"])
                self.land_1_done = True
                land_target = 1
                event_trigger = "EVENT_LAND_1"
                reason = "Quadrant 2 expansion milestone unlocked"
        elif n_unlocked == 1 and step >= self.cfg.land_2_step and not self.land_2_done:
            cost = LAND_PRICES[1]
            if cash >= cost + self.cfg.min_cash_reserve and len(market_orders) < self.cfg.max_market_orders:
                market_orders.append(["BUY_LAND"])
                self.land_2_done = True
                land_target = 2
                event_trigger = "EVENT_LAND_2"
                reason = "Quadrant 3 expansion milestone unlocked"

        # ---------------------------------------------------------------------
        # MECHANISM 3: PRODUCTION & SHOP CONDITIONING
        # ---------------------------------------------------------------------
        cow_target = self.cfg.cow_target
        sheep_target = self.cfg.sheep_target
        melon_target = self.cfg.melon_seed_target
        straw_target = self.cfg.strawberry_seed_target
        
        if self.stage in ("HMEH-2", "HMEH-3", "HMEH-4") and self.cfg.production_mode == "shop_conditioned":
            # Condition production on revealed town shops
            shops = state.unlocked_shops
            if "YARN_STORE" in shops:
                sheep_target = 6
                cow_target = 6
            if "BAKERY" in shops:
                # High wheat & carrot demand
                melon_target = 10
            if "PET_CAFE" in shops:
                # High milk & egg demand
                cow_target = 10

        # Purchase animals if spendable exceeds threshold
        cows_in_system = state.cow_count + sum(inv.get("COW", 0) for inv in state.carried_inventory) + state.shed_inventory.get("COW", 0)
        sheep_in_system = state.sheep_count + sum(inv.get("SHEEP", 0) for inv in state.carried_inventory) + state.shed_inventory.get("SHEEP", 0)
        
        if day <= 14 and fallback_mode != "CAUTION":
            if cows_in_system < cow_target and spendable >= self.cfg.cow_buy_threshold and len(market_orders) < self.cfg.max_market_orders:
                market_orders.append(["BUY_ANIMAL", "COW", 1])
                spendable -= 600
            if sheep_in_system < sheep_target and spendable >= self.cfg.sheep_buy_threshold and len(market_orders) < self.cfg.max_market_orders:
                market_orders.append(["BUY_ANIMAL", "SHEEP", 1])
                spendable -= 500

        # Feed Reserve Management
        feed_target = (cows_in_system + sheep_in_system) * (self.cfg.feed_reserve_days if day < 26 else 0)
        wheat_in_shed = state.wheat_in_shed
        if wheat_in_shed < feed_target and spendable >= 25 and len(market_orders) < self.cfg.max_market_orders:
            wheat_price = state.spot_prices.get("WHEAT", 25.0)
            deficit = feed_target - wheat_in_shed
            can_buy = min(deficit, int(spendable // max(1.0, wheat_price)), 15)
            if can_buy > 0:
                market_orders.append(["BUY_PRODUCT", "WHEAT", can_buy])
                spendable -= can_buy * wheat_price

        # Seed Purchasing
        # Melons: early game
        melon_active = state.planted_crops.get("MELON", 0) + state.seed_inventory.get("MELON", 0)
        if day <= 2 and melon_active < melon_target and spendable >= 80 and len(market_orders) < self.cfg.max_market_orders:
            needed = melon_target - melon_active
            can_buy = min(needed, int(spendable // 80), 8)
            if can_buy > 0:
                market_orders.append(["BUY_SEED", "MELON", can_buy])
                spendable -= can_buy * 80

        # Carrots: revenue generation
        carrot_seeds = state.seed_inventory.get("CARROT", 0)
        if 2 <= day <= 26 and carrot_seeds < 8 and spendable >= 40 and len(market_orders) < self.cfg.max_market_orders:
            needed = 8 - carrot_seeds
            can_buy = min(needed, int(spendable // 20), 6)
            if can_buy > 0:
                market_orders.append(["BUY_SEED", "CARROT", can_buy])
                spendable -= can_buy * 20

        # Strawberries: mid-game compounder
        straw_day = self.cfg.strawberry_start_step // 24
        if straw_day <= day <= straw_day + 10 and self.straw_seeds_bought < straw_target and spendable >= 100 and len(market_orders) < self.cfg.max_market_orders:
            needed = straw_target - self.straw_seeds_bought
            can_buy = min(needed, int(spendable // 100), 4)
            if can_buy > 0:
                market_orders.append(["BUY_SEED", "STRAWBERRY", can_buy])
                spendable -= can_buy * 100
                self.straw_seeds_bought += can_buy

        # ---------------------------------------------------------------------
        # MECHANISM 4: MARKET SELLING POLICY
        # ---------------------------------------------------------------------
        is_sell_step = (step % 4 == 0)
        sell_crops = (step >= self.cfg.sell_crops_start_step)
        
        batch_size = self.cfg.sell_batch_size
        if self.stage in ("HMEH-3", "HMEH-4") and self.cfg.market_mode == "adaptive":
            # Adaptive selling: larger batches (24) on high-value products to preserve market price
            batch_size = 24
            
        if is_sell_step:
            for prod in ["MELON", "WOOL", "MILK", "CARROT", "STRAWBERRY", "FERTILIZER"]:
                if prod in ("MELON", "CARROT", "STRAWBERRY") and not sell_crops:
                    continue
                qty = state.shed_inventory.get(prod, 0)
                if qty > 0 and len(market_orders) < self.cfg.max_market_orders:
                    # Only sell if price >= min_sell_price
                    if state.spot_prices.get(prod, 0.0) >= self.cfg.min_sell_price:
                        order_qty = min(qty, batch_size)
                        market_orders.append(["SELL", prod, order_qty])

        return StrategicIntent(
            objective="Standard Macro Execution",
            target_worker_count=target_workers,
            crop_targets={"MELON": melon_target, "STRAWBERRY": straw_target},
            cow_target=cow_target,
            sheep_target=sheep_target,
            min_cash_reserve=self.cfg.min_cash_reserve,
            land_expansion_target=land_target,
            market_orders=market_orders[:self.cfg.max_market_orders],
            fallback_mode=fallback_mode,
            stage=self.stage,
            reason=reason,
            event_trigger=event_trigger,
            metadata={"step": step, "day": day}
        )
