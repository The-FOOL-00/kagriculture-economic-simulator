import os

def create_ablations():
    with open("candidates/candidate_cl_fert_gated.py") as f:
        base_code = f.read()

    # -------------------------------------------------------------
    # 1. Candidate CL M1 + Sheep Timing (Accelerated sheep on Days 5-8)
    # -------------------------------------------------------------
    target_sheep_block = """                # BUY COW FIRST
                if cows_needed > 0 and money >= 650 and len(orders) < 8:
                    can_buy_c = min(cows_needed, min(2, int((money - 250) // 400)))
                    if can_buy_c > 0:
                        orders.append(["BUY_ANIMAL", "COW", can_buy_c])
                        money -= can_buy_c * 400
                        cows_tot += can_buy_c
                if sheep_needed > 0 and money >= 750 and len(orders) < 8:
                    can_buy_s = min(sheep_needed, min(3, int((money - 250) // 500)))
                    if can_buy_s > 0:
                        orders.append(["BUY_ANIMAL", "SHEEP", can_buy_s])
                        money -= can_buy_s * 500
                        sheep_tot += can_buy_s"""

    repl_sheep_block = """                # ABLATION 1: ACCELERATED SHEEP ACQUISITION (DAYS 5-8)
                # Prioritize completing 6 sheep by Day 8 before expanding cows to 8
                if day <= 8 and sheep_needed > 0 and money >= 650 and len(orders) < 8:
                    can_buy_s = min(sheep_needed, min(2, int((money - 150) // 500)))
                    if can_buy_s > 0:
                        orders.append(["BUY_ANIMAL", "SHEEP", can_buy_s])
                        money -= can_buy_s * 500
                        sheep_tot += can_buy_s
                        sheep_needed -= can_buy_s

                if cows_needed > 0 and money >= 650 and len(orders) < 8:
                    can_buy_c = min(cows_needed, min(2, int((money - 250) // 400)))
                    if can_buy_c > 0:
                        orders.append(["BUY_ANIMAL", "COW", can_buy_c])
                        money -= can_buy_c * 400
                        cows_tot += can_buy_c
                if sheep_needed > 0 and money >= 750 and len(orders) < 8:
                    can_buy_s = min(sheep_needed, min(3, int((money - 250) // 500)))
                    if can_buy_s > 0:
                        orders.append(["BUY_ANIMAL", "SHEEP", can_buy_s])
                        money -= can_buy_s * 500
                        sheep_tot += can_buy_s"""

    assert target_sheep_block in base_code, "Target sheep block not found!"
    code_sheep = base_code.replace(target_sheep_block, repl_sheep_block)
    with open("candidates/candidate_cl_m1_sheep_timing.py", "w") as f:
        f.write(code_sheep)
    print("Created candidates/candidate_cl_m1_sheep_timing.py")

    # -------------------------------------------------------------
    # 2. Candidate CL M1 + Pocket Batching (Threshold >= 4 units)
    # -------------------------------------------------------------
    target_drop_step3 = """            # Shed drop: ONLY drop produce
            if pos in SHED_ACCESS and produce_load > 0 and (cow_inv + sheep_inv) == 0 and (w_inv == 0 or not scan_res["hungry"]):
                actions[i] = ["DROP"]
                claimed_action_tiles.add(pos)
                self._worker_targets.pop(i, None)
                continue"""

    repl_drop_step3 = """            # ABLATION 2: POCKET BATCHING (Only drop if batch >= 4 units or late day)
            if pos in SHED_ACCESS and (produce_load >= 4 or (hour >= 20 and produce_load > 0)) and (cow_inv + sheep_inv) == 0 and (w_inv == 0 or not scan_res["hungry"]):
                actions[i] = ["DROP"]
                claimed_action_tiles.add(pos)
                self._worker_targets.pop(i, None)
                continue"""

    target_drop_step5 = """                if produce_load > 0 and (hour >= 20 or produce_load >= 5 or _dist(pos, ns) <= 2):
                    actions[w] = [_bfs_step(pos, ns, tiles)]
                    self._worker_targets[w] = (ns, "DROP", 1)
                else:
                    actions[w] = ["PASS"]"""

    repl_drop_step5 = """                # ABLATION 2: ELIMINATE EMPTY DEADHEAD TRIPS (Only walk to shed if pocket >= 4 or late day)
                if produce_load >= 4 or (hour >= 21 and produce_load > 0):
                    actions[w] = [_bfs_step(pos, ns, tiles)]
                    self._worker_targets[w] = (ns, "DROP", 1)
                else:
                    actions[w] = ["PASS"]"""

    assert target_drop_step3 in base_code, "Target drop step3 not found!"
    assert target_drop_step5 in base_code, "Target drop step5 not found!"
    code_batch = base_code.replace(target_drop_step3, repl_drop_step3).replace(target_drop_step5, repl_drop_step5)
    with open("candidates/candidate_cl_m1_pocket_batching.py", "w") as f:
        f.write(code_batch)
    print("Created candidates/candidate_cl_m1_pocket_batching.py")

    # -------------------------------------------------------------
    # 3. Candidate CL M1 + Wheat Expansion (Quota 60+ plots)
    # -------------------------------------------------------------
    target_wheat_buy = """        if hour == 0 and 2 <= day <= 24 and len(orders) < 8:
            wheat_s = int(seeds.get("WHEAT", 0) or 0)
            if wheat_s < 10 and money >= 200:
                can_buy_w = min(10 - wheat_s, min(10, int((money - 150) // 10)))
                if can_buy_w > 0:
                    orders.append(["BUY_SEED", "WHEAT", can_buy_w])
                    money -= can_buy_w * 10"""

    repl_wheat_buy = """        # ABLATION 3: WHEAT SEED EXPANSION (Support 60+ wheat plots across season)
        if hour == 0 and 2 <= day <= 24 and len(orders) < 8:
            wheat_s = int(seeds.get("WHEAT", 0) or 0)
            target_w_seeds = 25 if day <= 18 else 12
            if wheat_s < target_w_seeds and money >= 180:
                can_buy_w = min(target_w_seeds - wheat_s, min(15, int((money - 120) // 10)))
                if can_buy_w > 0:
                    orders.append(["BUY_SEED", "WHEAT", can_buy_w])
                    money -= can_buy_w * 10"""

    assert target_wheat_buy in base_code, "Target wheat buy not found!"
    code_wheat = base_code.replace(target_wheat_buy, repl_wheat_buy)
    with open("candidates/candidate_cl_m1_wheat_expansion.py", "w") as f:
        f.write(code_wheat)
    print("Created candidates/candidate_cl_m1_wheat_expansion.py")

if __name__ == "__main__":
    create_ablations()
