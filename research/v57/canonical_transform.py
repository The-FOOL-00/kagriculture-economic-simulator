import sys, os
sys.path.insert(0, '.')
import copy
import json
import itertools
from collections import defaultdict

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

# Canonical Representation:
# Each order in action['market'] is [OP, ITEM, QTY] or [ATOMIC] or []
# Economic orders are those with SELL / BUY

def parse_canonical(market_orders):
    """Returns list of canonical tuples: (index, op, item, qty) or None for empty."""
    canonical = []
    for idx, ord_entry in enumerate(market_orders):
        if not ord_entry:
            canonical.append({"index": idx, "type": "EMPTY", "item": None, "qty": 0, "raw": ord_entry})
        elif ord_entry[0] in ("HIRE", "BUY_LAND"):
            canonical.append({"index": idx, "type": ord_entry[0], "item": None, "qty": 0, "raw": ord_entry})
        else:
            op = ord_entry[0]
            item = ord_entry[1] if len(ord_entry) > 1 else None
            qty = int(ord_entry[2]) if len(ord_entry) > 2 else 0
            canonical.append({"index": idx, "type": op, "item": item, "qty": qty, "raw": ord_entry})
    return canonical

def reconstruct_orders(canonical):
    res = []
    for entry in canonical:
        if entry["type"] == "EMPTY":
            res.append([])
        elif entry["type"] in ("HIRE", "BUY_LAND"):
            res.append([entry["type"]])
        else:
            res.append([entry["type"], entry["item"], entry["qty"]])
    return res

def verify_structural_invariants(orig_market, transformed_market):
    """Verifies Class B guarantees:
    - aggregate quantities per commodity = V49
    - turn of actual sale = V49
    - no new economic order type/item
    - max 10 slots
    """
    if len(transformed_market) > 10:
        return False, "Exceeds max 10 slots"
        
    orig_canon = parse_canonical(orig_market)
    trans_canon = parse_canonical(transformed_market)
    
    orig_totals = defaultdict(int)
    for c in orig_canon:
        if c["type"] in ("SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL"):
            orig_totals[(c["type"], c["item"])] += c["qty"]
        elif c["type"] in ("HIRE", "BUY_LAND"):
            orig_totals[(c["type"], None)] += 1
            
    trans_totals = defaultdict(int)
    for c in trans_canon:
        if c["type"] in ("SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL"):
            trans_totals[(c["type"], c["item"])] += c["qty"]
        elif c["type"] in ("HIRE", "BUY_LAND"):
            trans_totals[(c["type"], None)] += 1
            
    if orig_totals != trans_totals:
        return False, f"Totals mismatch: orig={dict(orig_totals)} vs trans={dict(trans_totals)}"
        
    return True, "OK"

# Transformation generators:
def get_transformations_for_step(step, market_orders):
    transforms = {}
    
    # Q0: Baseline
    transforms["Q0_baseline"] = copy.deepcopy(market_orders)
    
    # Check if empty slots can fit
    curr_len = len(market_orders)
    
    # Q1: Leading empty slot padding
    if curr_len < 10:
        transforms["Q1_lead_pad1"] = [[]] + copy.deepcopy(market_orders)
    if curr_len < 9:
        transforms["Q1_lead_pad2"] = [[], []] + copy.deepcopy(market_orders)
        
    # Q2: Internal empty slot padding
    if curr_len < 10:
        for pos in range(1, curr_len):
            trans = copy.deepcopy(market_orders)
            trans.insert(pos, [])
            transforms[f"Q2_internal_pad_pos{pos}"] = trans
            
    # Q3: Trailing padding
    if curr_len < 10:
        transforms["Q3_trailing_pad1"] = copy.deepcopy(market_orders) + [[]]
    if curr_len < 9:
        transforms["Q3_trailing_pad2"] = copy.deepcopy(market_orders) + [[], []]
        
    # Q4: Same-turn quantity split
    # For any SELL with qty >= 2
    for idx, ord_entry in enumerate(market_orders):
        if ord_entry and ord_entry[0] == "SELL" and len(ord_entry) >= 3:
            qty = ord_entry[2]
            if qty >= 2 and curr_len < 10:
                # Try 50/50 split or 1 / (qty-1) split
                splits = [qty // 2, 1] if qty > 2 else [1]
                for a in splits:
                    b = qty - a
                    if a > 0 and b > 0:
                        trans = copy.deepcopy(market_orders)
                        trans[idx] = ["SELL", ord_entry[1], a]
                        trans.insert(idx + 1, ["SELL", ord_entry[1], b])
                        transforms[f"Q4_split_{ord_entry[1]}_{a}_{b}"] = trans
                        
                        # Q5: Split + empty
                        if curr_len < 9:
                            trans5 = copy.deepcopy(market_orders)
                            trans5[idx] = ["SELL", ord_entry[1], a]
                            trans5.insert(idx + 1, [])
                            trans5.insert(idx + 2, ["SELL", ord_entry[1], b])
                            transforms[f"Q5_split_empty_{ord_entry[1]}_{a}_{b}"] = trans5

    # Q6: Adjacent-order slot rotation / Permutations of sell orders
    # Find all SELL orders
    sell_indices = [i for i, o in enumerate(market_orders) if o and o[0] == "SELL"]
    if len(sell_indices) >= 2:
        # Swap adjacent sell orders
        for k in range(len(sell_indices) - 1):
            i1 = sell_indices[k]
            i2 = sell_indices[k + 1]
            trans = copy.deepcopy(market_orders)
            trans[i1], trans[i2] = trans[i2], trans[i1]
            transforms[f"Q6_swap_sells_{market_orders[i1][1]}_{market_orders[i2][1]}"] = trans
            
        # If 3 or 4 sell orders, try full permutations of sell orders
        if 2 <= len(sell_indices) <= 4:
            sells = [market_orders[i] for i in sell_indices]
            for p_idx, perm in enumerate(itertools.permutations(sells)):
                if list(perm) != sells:
                    trans = copy.deepcopy(market_orders)
                    for pos_idx, sell_pos in enumerate(sell_indices):
                        trans[sell_pos] = list(perm[pos_idx])
                    p_names = "_".join([s[1] for s in perm])
                    transforms[f"Q6_perm_{p_names}"] = trans
                    
    # Q7: Order-count preservation with different [] placements
    # If any transformation has length L, compare different positions
    if curr_len < 10:
        for pos in range(curr_len + 1):
            trans = copy.deepcopy(market_orders)
            trans.insert(pos, [])
            transforms[f"Q7_pad_at_{pos}"] = trans

    return transforms

def evaluate_transformation(trans_name, transform_fn, target_step=697):
    """Evaluates transformation across both loss seeds in both seat directions."""
    results = {}
    
    for seed in [250621, 250617]:
        for seat in [0, 1]:
            opp_seat = 1 - seat
            leg_key = f"seed_{seed}_seat_{seat}"
            sim = FastKagricultureSim(seed=seed)
            obs = sim.reset(seed=seed)
            
            for step in range(719):
                a_v49 = v49_mod.agent(obs[seat])
                a_v44 = v44_mod.agent(obs[opp_seat])
                
                # Apply transformation if at target step
                if transform_fn is not None and isinstance(a_v49, dict):
                    m = a_v49.get("market", [])
                    new_m = transform_fn(step, m)
                    if new_m is not None:
                        a_v49 = copy.deepcopy(a_v49)
                        a_v49["market"] = new_m
                        
                actions = [a_v49, a_v44] if seat == 0 else [a_v44, a_v49]
                obs, _, done, _ = sim.step(actions)
                if done: break
                
            c49 = float(obs[seat]["farms"][seat]["money"])
            c44 = float(obs[opp_seat]["farms"][opp_seat]["money"])
            marg = c49 - c44
            res = "WIN" if marg > 0 else ("LOSS" if marg < 0 else "DRAW")
            results[leg_key] = {
                "v49_cash": c49,
                "v44_cash": c44,
                "margin": marg,
                "outcome": res
            }
    return results

print("Transform module loaded successfully.")
