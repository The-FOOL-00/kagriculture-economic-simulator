# SPDX-License-Identifier: MIT
"""HMEH Main Agent Entrypoint.

Orchestrates the 5-layer Hierarchical Macro-Economic Hybrid pipeline:
Observation -> Economic State -> Macro Planner -> Chore Executor -> Legality Filter -> Simulator
"""

from __future__ import annotations
import copy
from typing import Any, Dict, List, Optional

try:
    from config import HMEHConfig, PRODUCTS
    from economic_state import EconomicState, extract_economic_state
    from executor import ChoreExecutor
    from fallback import FallbackManager, load_fresh_a7
    from legality import LegalityFilter
    from macro_planner import MacroPlanner
    from strategies import StrategicIntent
except ImportError:
    from candidates.v32_hmeh.config import HMEHConfig, PRODUCTS
    from candidates.v32_hmeh.economic_state import EconomicState, extract_economic_state
    from candidates.v32_hmeh.executor import ChoreExecutor
    from candidates.v32_hmeh.fallback import FallbackManager, load_fresh_a7
    from candidates.v32_hmeh.legality import LegalityFilter
    from candidates.v32_hmeh.macro_planner import MacroPlanner
    from candidates.v32_hmeh.strategies import StrategicIntent


class HMEHAgent:
    def __init__(self, stage: str = "HMEH-0", config: Optional[HMEHConfig] = None):
        self.stage = stage
        self.config = config or HMEHConfig()
        
        # Configure pipeline based on ablation stage
        if stage == "HMEH-0":
            self.config.labor_mode = "static"
            self.config.production_mode = "static"
            self.config.market_mode = "static"
            self.config.terminal_mode = "static"
        elif stage == "HMEH-1":
            self.config.labor_mode = "adaptive"
            self.config.production_mode = "static"
            self.config.market_mode = "static"
            self.config.terminal_mode = "static"
        elif stage == "HMEH-2":
            self.config.labor_mode = "adaptive"
            self.config.production_mode = "shop_conditioned"
            self.config.market_mode = "static"
            self.config.terminal_mode = "static"
        elif stage == "HMEH-3":
            self.config.labor_mode = "adaptive"
            self.config.production_mode = "shop_conditioned"
            self.config.market_mode = "adaptive"
            self.config.terminal_mode = "static"
        elif stage == "HMEH-4":
            self.config.labor_mode = "adaptive"
            self.config.production_mode = "shop_conditioned"
            self.config.market_mode = "adaptive"
            self.config.terminal_mode = "search"
            
        self.planner = MacroPlanner(self.config, stage=self.stage)
        self.executor = ChoreExecutor()
        self.filter = LegalityFilter(board_size=self.config.board_size)
        self.fallback = FallbackManager()
        
        # Base A7 engine instance for core proven mechanisms
        self._a7_fn = load_fresh_a7()
        
        self.prev_state: Optional[EconomicState] = None
        self.traces: List[Dict[str, Any]] = []
        self.diagnostics: Dict[str, Any] = {
            "total_steps": 0,
            "rejections": 0,
            "fallbacks": 0,
            "crashes": 0,
        }

    def __call__(self, observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            self.diagnostics["total_steps"] += 1
            player = int(observation.get("player", 0) or 0)
            step = int(observation.get("step", 0) or 0)
            
            # 1. State Extraction
            econ_state = extract_economic_state(
                observation=observation,
                player=player,
                prev_state=self.prev_state,
                consecutive_stalls=self.fallback.consecutive_stalls
            )
            
            # 2. Base A7 Action
            base_action = self._a7_fn(observation, configuration) if self._a7_fn else {"farmer": ["PASS"], "hands": [], "market": []}
            raw_action = copy.deepcopy(base_action)
            
            # 3. Macro Replanning & Adaptive Overrides
            intent = self.planner.plan(econ_state)
            
            # STAGE 0 (HMEH-0): Preserves A7 opening & baseline execution bit-for-bit
            if self.stage == "HMEH-0":
                self.prev_state = econ_state
                return raw_action
                
            # STAGE 1 (HMEH-1): Adaptive Labor Controller
            # Modulates worker hiring: throttles hires when chore backlog is low or cash runway is tight
            elif self.stage in ("HMEH-1", "HMEH-2", "HMEH-3", "HMEH-4") and self.config.labor_mode == "adaptive":
                # If base plans to HIRE but chore backlog is low and runway is stressed, throttle HIRE
                market_orders = list(raw_action.get("market") or [])
                if any(o[0] == "HIRE" for o in market_orders if o):
                    # Keep HIRE only if chore backlog justifies it or cash runway > 3.0 days
                    if econ_state.wage_runway_days < 2.5 and econ_state.pending_chore_count < econ_state.active_workers * 2:
                        raw_action["market"] = [o for o in market_orders if o and o[0] != "HIRE"]
                        
            # STAGE 2 (HMEH-2): Shop-Conditioned Production
            if self.stage in ("HMEH-2", "HMEH-3", "HMEH-4") and self.config.production_mode == "shop_conditioned":
                # If Bakery revealed on Day 3/6, prioritize Wheat/Carrot over Melons
                if step >= 72 and "BAKERY" in econ_state.unlocked_shops:
                    # Replace melon purchases with wheat/carrot if low on wheat
                    m_orders = []
                    for o in raw_action.get("market") or []:
                        if o and o[0] == "BUY_SEED" and len(o) > 1 and o[1] == "MELON" and econ_state.shed_inventory.get("WHEAT", 0) < 10:
                            m_orders.append(["BUY_SEED", "WHEAT", min(4, o[2] if len(o) > 2 else 1)])
                        else:
                            m_orders.append(o)
                    raw_action["market"] = m_orders

            # STAGE 3 (HMEH-3): Market-Aware Selling
            if self.stage in ("HMEH-3", "HMEH-4") and self.config.market_mode == "adaptive":
                # Batch sales into 18-24 lots to minimize price impact and avoid slippage
                m_orders = []
                for o in raw_action.get("market") or []:
                    if o and o[0] == "SELL" and len(o) >= 3:
                        prod = o[1]
                        qty = int(o[2])
                        # If price dropped below threshold, hold sale unless terminal
                        spot_px = econ_state.spot_prices.get(prod, 0.0)
                        if spot_px < 5.0 and step < 670:
                            continue  # Hold stock for price recovery
                        # Clamp batch to 24
                        m_orders.append(["SELL", prod, min(qty, 24)])
                    else:
                        m_orders.append(o)
                raw_action["market"] = m_orders

            # STAGE 4 (HMEH-4): Terminal Liquidation (Steps 712-718)
            if self.stage == "HMEH-4" and self.config.terminal_mode == "search":
                if step >= 712:
                    # 7-turn physical liquidation search: dump all shed inventory into market
                    m_orders = list(raw_action.get("market") or [])
                    existing_sells = {o[1] for o in m_orders if o and o[0] == "SELL" and len(o) > 1}
                    for prod in PRODUCTS:
                        qty = econ_state.shed_inventory.get(prod, 0)
                        if qty > 0 and prod not in existing_sells and len(m_orders) < 10:
                            m_orders.append(["SELL", prod, min(qty, 30)])
                    raw_action["market"] = m_orders[:10]

            # 4. Legality & Safety Filtering
            filter_res = self.filter.filter(raw_action, observation)
            safe_action = filter_res.action
            
            if filter_res.rejections:
                self.diagnostics["rejections"] += len(filter_res.rejections)
                
            self.prev_state = econ_state
            return safe_action
            
        except Exception as e:
            self.diagnostics["crashes"] += 1
            self.diagnostics["fallbacks"] += 1
            return self.fallback.emergency_a7_fallback(observation, configuration)


_default_agent = HMEHAgent(stage="HMEH-0")


def agent(observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Default Kaggle submission entrypoint for HMEH."""
    return _default_agent(observation, configuration)


def make_hmeh_agent(stage: str = "HMEH-0", config: Optional[HMEHConfig] = None):
    """Factory creating an isolated HMEH agent instance."""
    inst = HMEHAgent(stage=stage, config=config)
    def _act(obs, cfg=None):
        return inst(obs, cfg)
    return _act, inst
