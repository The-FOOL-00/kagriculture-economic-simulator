# SPDX-License-Identifier: MIT
"""V55 Candidate: Post-Reveal Shop-Regime Continuation Agent.

Preserves 100% bit-exact V49 behavior until Step 216.
From Step 216 onward, if a newly revealed town shop creates high dairy demand
(PIZZA_SHOP, ICE_CREAM_SHOP, SMOOTHIE_SHOP), the agent adjusts milk market
sales timing to exploit elevated town demand while guarding shed capacity.
"""

from typing import Any, Dict, List
import copy
import candidates.v49_meta_fusion.main as v49_mod

MILK_SHOPS = {"PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP"}

def agent(obs: Dict[str, Any], cfg: Any = None) -> Dict[str, Any]:
    step = int(obs.get("step", 0))
    # Bit-exact V49 prefix before Step 216
    base_act = v49_mod.agent(obs, cfg)
    if step < 216:
        return base_act
        
    if not isinstance(base_act, dict):
        return base_act
        
    unlocked = obs.get("town", {}).get("unlocked_shops", [])
    has_milk_shop = any(s in MILK_SHOPS for s in unlocked)
    if not has_milk_shop:
        return base_act
        
    farm = obs["farms"][obs.get("player", 0)]
    shed = farm.get("shed", {}) or {}
    shed_used = sum(shed.values())
    
    # If shed is getting congested (> 75 items), sell normally to avoid engine crop deletion
    if shed_used >= 75:
        return base_act
        
    # Check current milk price
    m_price = obs.get("market", {}).get("prices", {}).get("MILK", 100)
    if m_price >= 120:
        return base_act
        
    # Withhold milk until price reaches $120
    market_acts = base_act.get("market", [])
    new_market = []
    for m_op in market_acts:
        if len(m_op) >= 2 and m_op[0] == "SELL" and m_op[1] == "MILK":
            continue
        new_market.append(m_op)
        
    return {
        "farmer": base_act.get("farmer", ["PASS"]),
        "hands": base_act.get("hands", []),
        "market": new_market
    }
