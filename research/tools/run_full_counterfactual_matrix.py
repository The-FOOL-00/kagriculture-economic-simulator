import sys, os
sys.path.insert(0, '.')
import copy
import json
import itertools
from collections import defaultdict

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

from research.v57.canonical_transform import verify_structural_invariants

# Define transformation factory
def build_transformation_suite():
    suite = {}
    
    # Baseline
    suite["Q0_baseline"] = {
        "description": "Exact V49 market action list",
        "fn": lambda step, m: m
    }
    
    # -------------------------------------------------------------
    # Step 697 Transformations
    # -------------------------------------------------------------
    # Q6: Permutations of sells at step 697
    def make_perm_fn(step_target, item_order):
        def fn(step, m):
            if step != step_target or not m:
                return m
            # Separate sells and non-sells
            sells = [x for x in m if x and x[0] == "SELL"]
            non_sells = [x for x in m if not (x and x[0] == "SELL")]
            # Sort sells by desired item_order if present
            item_rank = {item: i for i, item in enumerate(item_order)}
            sorted_sells = sorted(sells, key=lambda x: item_rank.get(x[1], 99))
            # Preserve original sell slot positions
            res = copy.deepcopy(m)
            sell_ptr = 0
            for i, x in enumerate(res):
                if x and x[0] == "SELL":
                    res[i] = sorted_sells[sell_ptr]
                    sell_ptr += 1
            return res
        return fn

    # Specific rotations at 697:
    for target_items, label in [
        (["WOOL", "CARROT", "EGG", "MILK"], "wool_first"),
        (["WOOL", "EGG", "MILK", "CARROT"], "wool_egg_milk_carrot"),
        (["MILK", "WOOL", "EGG", "CARROT"], "milk_wool_egg_carrot"),
        (["CARROT", "WOOL", "EGG", "MILK"], "carrot_wool_egg_milk"),
        (["EGG", "WOOL", "CARROT", "MILK"], "egg_wool_carrot_milk"),
    ]:
        suite[f"Q6_step697_{label}"] = {
            "description": f"Step 697: reorder sells to prioritize {label}",
            "fn": make_perm_fn(697, target_items)
        }
        
    # Q1: Leading empty-slot padding at Step 697 (where len < 10)
    def make_lead_pad_fn(step_target, num_pads=1):
        def fn(step, m):
            if step != step_target or not m or len(m) + num_pads > 10:
                return m
            return [[] for _ in range(num_pads)] + copy.deepcopy(m)
        return fn
        
    suite["Q1_step697_lead_pad1"] = {
        "description": "Step 697: Prepend [] if len < 10",
        "fn": make_lead_pad_fn(697, 1)
    }
    
    # Q2: Internal empty-slot padding at Step 697 (before WOOL)
    def make_pad_before_wool_fn(step_target):
        def fn(step, m):
            if step != step_target or not m or len(m) >= 10:
                return m
            res = []
            inserted = False
            for x in m:
                if not inserted and x and x[0] == "SELL" and x[1] == "WOOL":
                    res.append([])
                    inserted = True
                res.append(x)
            return res
        return fn
        
    suite["Q2_step697_pad_before_wool"] = {
        "description": "Step 697: Insert [] immediately before WOOL sell",
        "fn": make_pad_before_wool_fn(697)
    }

    # Q3: Trailing padding at Step 697
    def make_trailing_pad_fn(step_target):
        def fn(step, m):
            if step != step_target or not m or len(m) >= 10:
                return m
            return copy.deepcopy(m) + [[]]
        return fn
        
    suite["Q3_step697_trailing_pad"] = {
        "description": "Step 697: Append [] if len < 10",
        "fn": make_trailing_pad_fn(697)
    }

    # Q4: Same-turn quantity split at Step 697 (Carrot split)
    def make_split_carrot_fn(step_target):
        def fn(step, m):
            if step != step_target or not m or len(m) >= 10:
                return m
            res = []
            for x in m:
                if x and x[0] == "SELL" and x[1] == "CARROT" and x[2] >= 2 and len(res) + len(m) - len(res) < 10:
                    a = x[2] // 2
                    b = x[2] - a
                    res.append(["SELL", "CARROT", a])
                    res.append(["SELL", "CARROT", b])
                else:
                    res.append(x)
            return res
        return fn
        
    suite["Q4_step697_split_carrot"] = {
        "description": "Step 697: Split CARROT sell into two halves if fits",
        "fn": make_split_carrot_fn(697)
    }

    # -------------------------------------------------------------
    # Step 694 Transformations (Immediately Adjacent Step)
    # -------------------------------------------------------------
    for target_items, label in [
        (["WOOL", "TOMATO", "WHEAT", "FERTILIZER", "EGG"], "wool_first"),
        (["WOOL", "EGG", "TOMATO", "WHEAT", "FERTILIZER"], "wool_egg_first"),
        (["EGG", "WOOL", "TOMATO", "WHEAT", "FERTILIZER"], "egg_wool_first"),
    ]:
        suite[f"Q6_step694_{label}"] = {
            "description": f"Step 694: reorder sells to prioritize {label}",
            "fn": make_perm_fn(694, target_items)
        }
        
    suite["Q1_step694_lead_pad1"] = {
        "description": "Step 694: Prepend 1 []",
        "fn": make_lead_pad_fn(694, 1)
    }
    suite["Q1_step694_lead_pad2"] = {
        "description": "Step 694: Prepend 2 []",
        "fn": make_lead_pad_fn(694, 2)
    }
    suite["Q2_step694_pad_before_wool"] = {
        "description": "Step 694: Insert [] before WOOL",
        "fn": make_pad_before_wool_fn(694)
    }

    # -------------------------------------------------------------
    # Step 693 Transformations
    # -------------------------------------------------------------
    for target_items, label in [
        (["MILK", "STRAWBERRY", "EGG", "WHEAT", "CARROT"], "milk_strawberry_first"),
        (["EGG", "MILK", "STRAWBERRY", "WHEAT", "CARROT"], "egg_milk_first"),
    ]:
        suite[f"Q6_step693_{label}"] = {
            "description": f"Step 693: reorder sells {label}",
            "fn": make_perm_fn(693, target_items)
        }
    suite["Q1_step693_lead_pad1"] = {
        "description": "Step 693: Prepend 1 []",
        "fn": make_lead_pad_fn(693, 1)
    }

    # -------------------------------------------------------------
    # Step 718 Transformations (Terminal Step)
    # -------------------------------------------------------------
    for target_items, label in [
        (["WOOL", "EGG", "WHEAT", "CARROT", "FERTILIZER"], "wool_egg_wheat"),
        (["WOOL", "CARROT", "WHEAT", "EGG", "FERTILIZER"], "wool_carrot_wheat"),
        (["EGG", "WOOL", "CARROT", "WHEAT", "FERTILIZER"], "egg_wool_carrot"),
    ]:
        suite[f"Q6_step718_{label}"] = {
            "description": f"Step 718: reorder terminal sells {label}",
            "fn": make_perm_fn(718, target_items)
        }
    suite["Q1_step718_lead_pad1"] = {
        "description": "Step 718: Prepend 1 []",
        "fn": make_lead_pad_fn(718, 1)
    }

    # -------------------------------------------------------------
    # Combined Step 694 + Step 697 Transformations
    # -------------------------------------------------------------
    def combined_fn(step, m):
        if step == 694:
            return make_perm_fn(694, ["WOOL", "TOMATO", "WHEAT", "FERTILIZER", "EGG"])(step, m)
        if step == 697:
            return make_perm_fn(697, ["WOOL", "CARROT", "EGG", "MILK"])(step, m)
        return m
        
    suite["Q6_combo_694_697_wool_first"] = {
        "description": "Steps 694 & 697: Prioritize WOOL in both steps",
        "fn": combined_fn
    }
    
    return suite

# Execution engine
def run_all_counterfactuals():
    suite = build_transformation_suite()
    print(f"Total transformations in suite: {len(suite)}")
    
    all_results = {}
    
    # First get baseline
    baseline_res = {}
    for seed in [250621, 250617]:
        for seat in [0, 1]:
            opp_seat = 1 - seat
            leg_key = f"seed_{seed}_seat_{seat}"
            sim = FastKagricultureSim(seed=seed)
            obs = sim.reset(seed=seed)
            for step in range(719):
                a49 = v49_mod.agent(obs[seat])
                a44 = v44_mod.agent(obs[opp_seat])
                obs, _, done, _ = sim.step([a49, a44] if seat == 0 else [a44, a49])
                if done: break
            c49 = float(obs[seat]["farms"][seat]["money"])
            c44 = float(obs[opp_seat]["farms"][opp_seat]["money"])
            baseline_res[leg_key] = {"c49": c49, "c44": c44, "marg": c49 - c44}
            
    print("Baselines:")
    for k, v in baseline_res.items():
        print(f"  {k}: Marg={v['marg']:+.1f} (V49={v['c49']}, V44={v['c44']})")
        
    for trans_name, t_info in suite.items():
        fn = t_info["fn"]
        trans_results = {}
        rescues = 0
        regressions = 0
        total_delta = 0.0
        
        for seed in [250621, 250617]:
            for seat in [0, 1]:
                opp_seat = 1 - seat
                leg_key = f"seed_{seed}_seat_{seat}"
                sim = FastKagricultureSim(seed=seed)
                obs = sim.reset(seed=seed)
                
                diverged_step = None
                diverged_info = None
                
                for step in range(719):
                    a49 = v49_mod.agent(obs[seat])
                    a44 = v44_mod.agent(obs[opp_seat])
                    
                    if isinstance(a49, dict) and "market" in a49:
                        orig_m = a49["market"]
                        new_m = fn(step, orig_m)
                        if new_m is not None and new_m != orig_m:
                            # Verify invariants
                            ok, reason = verify_structural_invariants(orig_m, new_m)
                            if not ok:
                                raise ValueError(f"Invariant violation in {trans_name} at step {step}: {reason}")
                            a49 = copy.deepcopy(a49)
                            a49["market"] = new_m
                            
                    obs, _, done, _ = sim.step([a49, a44] if seat == 0 else [a44, a49])
                    
                    # Track first divergence
                    if diverged_step is None:
                        curr_c49 = float(obs[seat]["farms"][seat]["money"])
                        curr_c44 = float(obs[opp_seat]["farms"][opp_seat]["money"])
                        # Compare to pre-recorded baseline if needed
                    if done: break
                    
                c49 = float(obs[seat]["farms"][seat]["money"])
                c44 = float(obs[opp_seat]["farms"][opp_seat]["money"])
                marg = c49 - c44
                base_marg = baseline_res[leg_key]["marg"]
                delta = marg - base_marg
                total_delta += delta
                outcome = "WIN" if marg > 0 else ("LOSS" if marg < 0 else "DRAW")
                
                if base_marg < 0 and marg > 0:
                    rescues += 1
                elif base_marg > 0 and marg < 0:
                    regressions += 1
                    
                trans_results[leg_key] = {
                    "v49_cash": c49,
                    "v44_cash": c44,
                    "margin": marg,
                    "delta_vs_baseline": delta,
                    "outcome": outcome
                }
                
        all_results[trans_name] = {
            "description": t_info["description"],
            "rescues": rescues,
            "regressions": regressions,
            "mean_delta": total_delta / 4.0,
            "legs": trans_results
        }
        
        status_sym = "RESCUE!" if rescues > 0 else ("REGRESSION" if regressions > 0 else ("NEUTRAL" if total_delta == 0 else f"Delta {total_delta/4.0:+.1f}"))
        print(f"[{trans_name:32s}] Rescues={rescues}/4 | MeanDelta={total_delta/4.0:>+8.1f} | Status={status_sym}")
        
    os.makedirs("research/v57/counterfactuals", exist_ok=True)
    with open("research/v57/counterfactuals/QUEUE_ALIGNMENT_MATRIX.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("Saved research/v57/counterfactuals/QUEUE_ALIGNMENT_MATRIX.json")

if __name__ == "__main__":
    run_all_counterfactuals()
