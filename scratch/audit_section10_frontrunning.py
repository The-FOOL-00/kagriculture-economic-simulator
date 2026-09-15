"""
Audit Section 10: Preemptive Front-Running Decomposition (CF1 - CF7)
Decomposes the market interaction benefit into:
A. Earlier selling (Liquidity)
B. Smaller batches
C. Lower inventory threshold
D. Prediction/lookahead (Price-defense)
E. Converting inventory to cash earlier

Evaluates across 10 identical seeds (2000-2009) against V54:
CF1: Same selling times, no lookahead (preempt_horizon=0)
CF2: Same threshold (3.0), no lookahead (preempt_enabled=False)
CF3: Same lookahead (horizon=3), threshold disabled (front_supply_threshold=999)
CF4: Same quantity but randomized selling order
CF5: Delayed selling by 1 turn
CF6: Delayed selling by 3 turns
CF7: Delayed selling by 6 turns
Baseline: Full V54 policy
"""
import sys, os, json, importlib.util, copy, random
from kaggle_environments import make

def run_counterfactual_suite():
    v54_path = "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py"
    d = os.path.dirname(os.path.abspath(v54_path))
    if d not in sys.path: sys.path.insert(0, d)
    spec = importlib.util.spec_from_file_location("v54_mod", v54_path)
    v54_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v54_mod)
    raw_v54 = getattr(v54_mod, "agent", None)
    
    build_policy = v54_mod._v51_build_policy
    route = v54_mod._V54_ROUTE
    base_cfg = v54_mod._V54_CONFIG
    ResidualConfig = v54_mod._V51ResidualConfig
    
    seeds = list(range(2000, 2010))
    
    # 1. Baseline Full V54 Policy
    baseline_policy = build_policy(route, base_cfg)
    
    # 2. CF1: No lookahead (preempt_horizon = 0)
    cfg_cf1 = copy.deepcopy(base_cfg.__dict__)
    cfg_cf1["preempt_horizon"] = 0
    policy_cf1 = build_policy(route, ResidualConfig(**cfg_cf1))
    
    # 3. CF2: Preempt completely disabled (preempt_enabled = False)
    cfg_cf2 = copy.deepcopy(base_cfg.__dict__)
    cfg_cf2["preempt_enabled"] = False
    policy_cf2 = build_policy(route, ResidualConfig(**cfg_cf2))
    
    # 4. CF3: Lookahead enabled, but front_supply_threshold disabled (threshold = 99999)
    cfg_cf3 = copy.deepcopy(base_cfg.__dict__)
    cfg_cf3["front_supply_threshold"] = 99999.0
    policy_cf3 = build_policy(route, ResidualConfig(**cfg_cf3))
    
    # 5. CF4: Randomized sell order wrapper around baseline
    def policy_cf4(obs, cfg=None):
        act = baseline_policy(obs, cfg)
        if isinstance(act, dict) and "market" in act:
            sells = [o for o in act["market"] if o and o[0] == "SELL"]
            others = [o for o in act["market"] if not (o and o[0] == "SELL")]
            random.Random(42 + obs.step).shuffle(sells)
            act["market"] = (others + sells)[:10]
        return act
        
    # Helper for delayed selling
    def make_delayed_policy(delay_turns):
        queue = [] # (step_due, sell_orders)
        def delayed_policy(obs, cfg=None):
            act = baseline_policy(obs, cfg)
            step = obs.get("step", obs.get("day", 0)*24 + obs.get("hour", 0))
            if not isinstance(act, dict): return act
            market = act.get("market", [])
            curr_sells = [o for o in market if o and o[0] == "SELL"]
            others = [o for o in market if not (o and o[0] == "SELL")]
            
            if curr_sells:
                queue.append((step + delay_turns, curr_sells))
                
            ready_sells = []
            rem_queue = []
            for due, orders in queue:
                if step >= due:
                    ready_sells.extend(orders)
                else:
                    rem_queue.append((due, orders))
            queue[:] = rem_queue
            
            act["market"] = (others + ready_sells)[:10]
            return act
        return delayed_policy

    policy_cf5 = make_delayed_policy(1)
    policy_cf6 = make_delayed_policy(3)
    policy_cf7 = make_delayed_policy(6)
    
    arms = {
        "BASELINE": baseline_policy,
        "CF1_NO_LOOKAHEAD_HORIZON_0": policy_cf1,
        "CF2_PREEMPT_DISABLED": policy_cf2,
        "CF3_THRESHOLD_DISABLED_999": policy_cf3,
        "CF4_RANDOMIZED_ORDER": policy_cf4,
        "CF5_DELAY_1_TURN": policy_cf5,
        "CF6_DELAY_3_TURNS": policy_cf6,
        "CF7_DELAY_6_TURNS": policy_cf7,
    }
    
    print("Evaluating Counterfactuals CF1 - CF7 vs V54 across 10 seeds...")
    results = {}
    
    for arm_name, arm_fn in arms.items():
        rewards = []
        opp_rewards = []
        for seed in seeds:
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            env.run([arm_fn, raw_v54])
            r0 = float(env.steps[-1][0].reward or 0.0)
            r1 = float(env.steps[-1][1].reward or 0.0)
            rewards.append(r0)
            opp_rewards.append(r1)
            
        m0 = sum(rewards) / len(rewards)
        m1 = sum(opp_rewards) / len(opp_rewards)
        margin = m0 - m1
        win_rate = sum(1 for r0, r1 in zip(rewards, opp_rewards) if r0 > r1) / len(rewards)
        
        results[arm_name] = {
            "reward_mean": m0,
            "opp_reward_mean": m1,
            "margin_mean": margin,
            "win_rate": win_rate,
            "delta_vs_baseline": m0 - (results["BASELINE"]["reward_mean"] if "BASELINE" in results else m0)
        }
        print(f"{arm_name:28s} | Reward: {m0:7.0f} | Opp: {m1:7.0f} | Margin: {margin:+7.0f} | Win%: {win_rate:.0%} | DeltaBase: {results[arm_name]['delta_vs_baseline']:+7.0f}")
        
    with open("scratch/frontrunning_audit_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved front-running audit to scratch/frontrunning_audit_results.json")

if __name__ == "__main__":
    run_counterfactual_suite()
