import os
import sys

os.makedirs("candidates/counterstrategy_ablation", exist_ok=True)

# Read base V2 code
v2_path = "candidates/slot2_aethel_refined_v2.py"
with open(v2_path, "r", encoding="utf-8") as f:
    v2_base_code = f.read()

# Candidate A: Exact V2 baseline
with open("candidates/counterstrategy_ablation/candidate_A.py", "w", encoding="utf-8") as f:
    f.write(v2_base_code)
print("Created Candidate A (Exact V2 baseline)")

# Candidate configurations: (has_cap12, has_early_ramp, has_preemption, desc)
configs = {
    "B": (True, False, False, "V2 + 12-worker cap only"),
    "C": (False, True, False, "V2 + early-capital-ramp only"),
    "D": (False, False, True, "V2 + market-preemption only"),
    "E": (True, True, False, "V2 + 12-worker cap + early ramp"),
    "F": (True, False, True, "V2 + 12-worker cap + market preemption"),
    "G": (False, True, True, "V2 + early ramp + market preemption"),
    "H": (True, True, True, "V2 + all three changes (cap12 + early ramp + preemption)")
}

for name, (cap12, early_ramp, preemption, desc) in configs.items():
    code = v2_base_code
    
    # Inject feature flags at the top of the file
    flags = f"""
# ===========================================================================
# CANDIDATE {name}: {desc}
# ===========================================================================
_ENABLE_CAP_12 = {cap12}
_ENABLE_EARLY_RAMP = {early_ramp}
_ENABLE_PREEMPTION = {preemption}
"""
    # Insert after imports
    insert_pos = code.find("def _public_signature")
    code_mod = code[:insert_pos] + flags + "\n" + code[insert_pos:]
    
    # Modify agent() function to apply the features cleanly
    agent_target = "def agent(obs, config=None):"
    
    mod_agent_logic = """def agent(obs, config=None):
    \"\"\"Controlled candidate with explicit factor ablations.\"\"\"
    if not _MARKET_CONTROLLER_ENABLED:
        return _base_agent(obs, config)
    action = _base_agent(obs, config)
    try:
        step = int(obs.get("step", 0) or 0)
        day = step // 24
        hour = step % 24
        player = int(obs.get("player", 0) or 0)
        farms = obs.get("farms") or []
        farm = farms[player] if len(farms) > player else {}
        hands = farm.get("hands", []) or []
        
        # Factor 1: 12-Worker Cap (Cap hands at 11, total units 12)
        if _ENABLE_CAP_12 and len(hands) >= 11:
            market = action.get("market", []) or []
            action["market"] = [o for o in market if not (isinstance(o, list) and o and o[0] == "HIRE")]
            
        if step >= _TERMINAL_START_STEP:
            return action
            
        orders = list(action.get("market") or [])
        keep = [
            order for order in orders
            if not (
                isinstance(order, list) and len(order) >= 2
                and order[0] == "SELL" and order[1] in _RESERVE
            )
        ]
        
        # Factor 1 continued: enforce hire cap in keep queue
        if _ENABLE_CAP_12 and len(hands) >= 11:
            keep = [o for o in keep if not (isinstance(o, list) and o and o[0] == "HIRE")]
            
        money = float(farm.get("money", 0) or 0)
        short = max(0.0, _cash_needed(keep, obs) - money)
        
        # Factor 2: Early Capital Ramp
        effective_short = short
        if _ENABLE_EARLY_RAMP and 2 <= day <= 10:
            effective_short = max(short, 500.0)
            
        sells = _plan_sells(obs, step, 10 - len(keep), effective_short)
        
        # Factor 3: Market Preemption (Safe slot-filling without displacing buys)
        if _ENABLE_PREEMPTION:
            private = obs.get("private") or {}
            shed = private.get("shed") or {}
            for item in _SELLABLE:
                avail = int(shed.get(item, 0) or 0)
                if avail > 0 and not any(isinstance(s, list) and len(s) >= 2 and s[0] == "SELL" and s[1] == item for s in sells):
                    sells.append(["SELL", item, avail])
                    
        if not _SORT_SELLS:
            action["market"] = (keep + sells)[:10]
            return action

        def is_sell(o):
            return isinstance(o, list) and o and o[0] == "SELL"

        opp_money = None
        if _PROMOTE_IF_OPP_MONEY:
            if len(farms) > 1:
                opp_money = float(farms[1 - player].get("money", 0) or 0)

        def promotable(o):
            if not is_sell(o):
                return False
            item = o[1]
            if item in _PROMOTE_IF_OPP_MONEY:
                if opp_money is None:
                    return False
                return opp_money >= _PROMOTE_IF_OPP_MONEY[item]
            if item in _PROMOTE_AFTER:
                return step >= _PROMOTE_AFTER[item]
            return not _PROMOTE or item in _PROMOTE

        merged = [o for o in sells if promotable(o)] + [o for o in keep if promotable(o)]
        merged.sort(key=lambda o: -_sell_priority(o, obs, step))
        
        # Keep the tape's slot layout: sorted sells refill promotable sell slots,
        # non-promotable structural buys/hires remain untouched in place.
        out = []
        queue = list(merged)
        for order in keep:
            out.append(queue.pop(0) if (promotable(order) and queue) else order)
        out.extend(queue)
        action["market"] = out[:10]
        return action
    except Exception:
        return action
"""
    code_mod = code_mod.replace(agent_target, "# BASE_AGENT_DEF\n" + agent_target)
    start_agent = code_mod.find("def agent(obs, config=None):")
    code_final = code_mod[:start_agent] + mod_agent_logic
    
    out_file = f"candidates/counterstrategy_ablation/candidate_{name}.py"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(code_final)
    print(f"Created Candidate {name} ({desc})")

print("\nAll 8 controlled candidates successfully rebuilt.")
