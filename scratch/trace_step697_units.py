import sys, os
sys.path.insert(0, '.')
import copy

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod
import kaggle_environments.envs.kaggriculture.kaggriculture as kg

def trace_step_detailed(seed, target_step=697):
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    
    for step in range(target_step):
        a0 = v49_mod.agent(obs[0])
        a1 = v44_mod.agent(obs[1])
        obs, _, done, _ = sim.step([a0, a1])
        if done: return
        
    print(f"\n=======================================================")
    print(f"DETAILED STEP {target_step} TRACE FOR SEED {seed}")
    print(f"=======================================================")
    
    a0 = v49_mod.agent(obs[0])
    a1 = v44_mod.agent(obs[1])
    
    print(f"Pre-step cash: V49=${obs[0]['farms'][0]['money']}, V44=${obs[0]['farms'][1]['money']}, Marg={obs[0]['farms'][0]['money'] - obs[0]['farms'][1]['money']}")
    print(f"Pre-step shed V49: {sim.state[0].observation.private['shed']}")
    print(f"Pre-step shed V44: {sim.state[1].observation.private['shed']}")
    print(f"V49 market action: {a0.get('market', [])}")
    print(f"V44 market action: {a1.get('market', [])}")
    
    # We can inspect _process_market step by step by monkey-patching or instrumenting _commit_unit
    orig_commit = kg._commit_unit
    
    commits = []
    def instrumented_commit(op, item, price, farm, private, market, shed_capacity=100):
        # find player
        player_id = 0 if farm == sim.state[0].observation.farms[0] else 1
        pname = "V49" if player_id == 0 else "V44"
        res = orig_commit(op, item, price, farm, private, market, shed_capacity)
        commits.append({
            "player": pname,
            "op": op,
            "item": item,
            "price": price,
            "ok": res,
            "post_cash": farm["money"],
            "post_inv": market["inventory"].get(item)
        })
        print(f"  COMMIT: {pname} {op} {item} @ ${price} (ok={res}) -> Cash=${farm['money']}, Inv[{item}]={market['inventory'].get(item)}")
        return res
        
    kg._commit_unit = instrumented_commit
    try:
        obs, _, _, _ = sim.step([a0, a1])
    finally:
        kg._commit_unit = orig_commit
        
    print(f"Post-step cash: V49=${obs[0]['farms'][0]['money']}, V44=${obs[0]['farms'][1]['money']}, Marg={obs[0]['farms'][0]['money'] - obs[0]['farms'][1]['money']}")
    print(f"Post-step shed V49: {sim.state[0].observation.private['shed']}")
    print(f"Post-step shed V44: {sim.state[1].observation.private['shed']}")

trace_step_detailed(250621, 697)
trace_step_detailed(250617, 697)
trace_step_detailed(250617, 718)
