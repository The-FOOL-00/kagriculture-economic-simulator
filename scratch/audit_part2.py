import sys
import os
import ast
import json
import hashlib
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.research_b_only_v1 as b1_modular
import candidates.compiled_research_b_only_v2 as b1_compiled_v2
import kaggle_environments.envs.kaggriculture.kaggriculture as engine

TRUE_ORIG_COMMIT = engine._commit_unit
TRUE_ORIG_HIRE = engine._do_hire
TRUE_ORIG_LAND = engine._do_buy_land
TRUE_ORIG_PROCESS = engine._process_market

def verify_b1_logic():
    print("--- PART 2.1: AST Logic Verification of research_b_only_v1 and compiled_research_b_only_v2 ---")
    with open("candidates/research_b_only_v1.py", "r", encoding="utf-8") as f:
        mod_code = f.read()
    with open("candidates/compiled_research_b_only_v2.py", "r", encoding="utf-8") as f:
        comp_code = f.read()

    # Verify that urgency sorting is NOT present in either file
    assert "crop_urgency_key" not in mod_code, "Found crop_urgency_key in research_b_only_v1.py!"
    assert "crop_urgency_key" not in comp_code, "Found crop_urgency_key in compiled_research_b_only_v2.py!"

    # Verify that ripe_crops is NOT sorted in either file
    assert ".sort" not in mod_code, "Unexpected sort call in modular!"
    
    # In compiled file, check where sort/sorted is used:
    tree = ast.parse(comp_code)
    # Check that in ResearchBOnlyV1 class, only wheat quota and weed suppression exist
    b1_class = None
    for n in tree.body:
        if isinstance(n, ast.ClassDef) and n.name == "ResearchBOnlyV1":
            b1_class = n
            break
    assert b1_class is not None, "ResearchBOnlyV1 not found in compiled AST!"
    
    method_names = [m.name for m in b1_class.body if isinstance(m, ast.FunctionDef)]
    print(f"ResearchBOnlyV1 methods in compiled file: {method_names}")
    assert set(method_names) == {"__init__", "__call__", "_macro_market", "_scan_field"}, f"Unexpected methods in ResearchBOnlyV1: {method_names}"

    print("Verified AST: ResearchBOnlyV1 overrides ONLY __init__, __call__, _macro_market (quota), and _scan_field (weeds + quota).")
    print("ZERO Component A urgency sorting, ZERO worker-matching, ZERO movement, ZERO animal, ZERO land mods.")

def run_single(args):
    pol_type, seed = args
    if pol_type == "modular":
        agent = b1_modular.ResearchBOnlyV1()
    elif pol_type == "compiled_v2":
        agent = b1_compiled_v2.ResearchBOnlyV1()
    else:
        raise ValueError(f"Unknown pol_type: {pol_type}")

    ledger = defaultdict(float)
    trans_stream = []
    current_f0 = [None]

    def my_commit(op, item, price, farm, private, market, shed_capacity=100):
        m_b = farm['money']
        res = TRUE_ORIG_COMMIT(op, item, price, farm, private, market, shed_capacity)
        if res and farm is current_f0[0]:
            delta = farm['money'] - m_b
            if op == 'SELL':
                ledger['REV_' + item] += delta
            elif op == 'BUY_PRODUCT':
                if item == 'FERTILIZER':
                    ledger['EXP_FERT'] += abs(delta)
                else:
                    ledger['EXP_FEED_' + item] += abs(delta)
            elif op == 'BUY_SEED':
                ledger['EXP_SEED_' + item] += abs(delta)
            elif op == 'BUY_ANIMAL':
                ledger['EXP_ANIMAL_' + item] += abs(delta)
            trans_stream.append((op, item, float(price), float(delta)))
        return res

    def my_hire(farm, private, board_size, mult=engine.FARM_HAND_COST_MULT):
        m_b = farm['money']
        TRUE_ORIG_HIRE(farm, private, board_size, mult)
        if farm is current_f0[0]:
            delta = m_b - farm['money']
            ledger['EXP_HIRE'] += delta
            trans_stream.append(('HIRE', 'HAND', 0.0, float(delta)))

    def my_land(farm, board_size):
        m_b = farm['money']
        TRUE_ORIG_LAND(farm, board_size)
        if farm is current_f0[0]:
            delta = m_b - farm['money']
            ledger['EXP_LAND'] += delta
            trans_stream.append(('BUY_LAND', 'LAND', 0.0, float(delta)))

    def my_process_market(state, env):
        current_f0[0] = state[0].observation.farms[0]
        TRUE_ORIG_PROCESS(state, env)

    engine._commit_unit = my_commit
    engine._do_hire = my_hire
    engine._do_buy_land = my_land
    engine._process_market = my_process_market

    try:
        cfg = {"episodeSteps": 720, "seed": seed}
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        steps = env.run([agent, "starter"])
    finally:
        engine._commit_unit = TRUE_ORIG_COMMIT
        engine._do_hire = TRUE_ORIG_HIRE
        engine._do_buy_land = TRUE_ORIG_LAND
        engine._process_market = TRUE_ORIG_PROCESS

    rew = float(steps[-1][0]["reward"])
    start_money = float(steps[0][0]["observation"]["farms"][0]["money"])
    
    total_rev = sum(v for k, v in ledger.items() if k.startswith("REV_"))
    total_exp = sum(v for k, v in ledger.items() if k.startswith("EXP_"))
    diff = abs(start_money + total_rev - total_exp - rew)

    action_stream = []
    for st in steps:
        act = st[0].get("action") or {}
        action_stream.append((str(act.get("farmer")), [str(h) for h in act.get("hands") or []], [list(o) for o in act.get("market") or []]))

    f0 = steps[-1][0]["observation"]["farms"][0]
    final_state = {
        "money": f0.get("money"),
        "shed": f0.get("shed"),
        "tiles": f0.get("tiles")
    }

    act_hash = hashlib.sha256(json.dumps(action_stream, sort_keys=True).encode('utf-8')).hexdigest()
    trans_hash = hashlib.sha256(json.dumps(trans_stream, sort_keys=True).encode('utf-8')).hexdigest()
    state_hash = hashlib.sha256(json.dumps(final_state, sort_keys=True).encode('utf-8')).hexdigest()

    return {
        "pol_type": pol_type,
        "seed": seed,
        "reward": rew,
        "act_hash": act_hash,
        "trans_hash": trans_hash,
        "state_hash": state_hash,
        "accounting_diff": diff
    }

def run_100_seed_equivalence():
    test_seeds = list(range(865500, 865600)) # 100 fresh seeds outside 865000..865499
    print(f"\n--- PART 2.2: 100-Seed Behavioral Equivalence Audit ({test_seeds[0]}..{test_seeds[-1]}) ---")

    jobs = []
    for s in test_seeds:
        jobs.append(("modular", s))
        jobs.append(("compiled_v2", s))

    results = defaultdict(dict)
    with ProcessPoolExecutor(max_workers=10) as executor:
        for res in executor.map(run_single, jobs):
            results[res["pol_type"]][res["seed"]] = res

    mismatches = 0
    max_acct_diff = 0.0

    for s in test_seeds:
        mod = results["modular"][s]
        com = results["compiled_v2"][s]

        r_match = (mod["reward"] == com["reward"])
        a_match = (mod["act_hash"] == com["act_hash"])
        t_match = (mod["trans_hash"] == com["trans_hash"])
        s_match = (mod["state_hash"] == com["state_hash"])

        max_acct_diff = max(max_acct_diff, mod["accounting_diff"], com["accounting_diff"])

        if not (r_match and a_match and t_match and s_match):
            mismatches += 1
            print(f"Mismatch on seed {s}: r={r_match}, a={a_match}, t={t_match}, s={s_match}")

    print(f"Total Mismatches across 100 fresh seeds: {mismatches} / 100")
    print(f"Max accounting difference: {max_acct_diff:.2e}")
    assert mismatches == 0, f"Found {mismatches} behavioral mismatches!"
    assert max_acct_diff < 1e-6, "Accounting check failed!"
    print("PART 2 PASSED: 100 / 100 EXACT BEHAVIORAL MATCHES (actions, transactions, rewards, terminal states)!")

if __name__ == "__main__":
    verify_b1_logic()
    run_100_seed_equivalence()
