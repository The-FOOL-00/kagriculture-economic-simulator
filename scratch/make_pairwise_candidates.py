with open("candidates/candidate_cl_economic_v1.py", "r", encoding="utf-8") as f:
    orig = f.read()

# M1 replacement: state-derived fertilizer gating
m1_target = '''                    # STRICT GUARD: DO NOT FERTILIZE WHEAT! Reserve $100 fertilizer for Strawberry or sale!
                    if crop != "WHEAT" and fert_inv > 0 and t.get("fertilized_until_day", -1) < day and pos not in claimed_action_tiles:
                        actions[i] = ["FERTILIZE"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue'''

m1_replacement = '''                    # STRICT GUARD: DO NOT FERTILIZE WHEAT!
                    # STATE-DERIVED FERTILIZER GATING (P+7 <= day <= min(29, P+15))
                    can_fert = False
                    if crop == "STRAWBERRY":
                        p_day = int(t.get("planted_day", 0) or 0)
                        can_fert = (p_day + 7 <= day <= min(29, p_day + 15))
                    elif crop != "WHEAT":
                        can_fert = True

                    if can_fert and fert_inv > 0 and t.get("fertilized_until_day", -1) < day and pos not in claimed_action_tiles:
                        actions[i] = ["FERTILIZE"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue'''

# M3 replacement: immediate harvesting yu >= 1
m3_target = '''                                # STRAWBERRY BATCH HARVEST: require >= 2 units (or terminal season)
                                if yu >= 2 or day >= 27:
                                    ripe_crops.append(pos)'''

m3_replacement = '''                                # HARVEST IMMEDIATE: harvest any ripe strawberry (yu >= 1) to prevent weed decay
                                if yu >= 1:
                                    ripe_crops.append(pos)'''

# M4 replacement: day <= 14 planting cutoff
m4_target = '''                        elif int(seeds.get("STRAWBERRY", 0) or 0) > 0 and day <= 20:
                            plant_s.append(pos)'''

m4_replacement = '''                        elif int(seeds.get("STRAWBERRY", 0) or 0) > 0 and day <= 14:  # ENGINE HORIZON CUTOFF: 4 cycles
                            plant_s.append(pos)'''

assert m1_target in orig
assert m3_target in orig
assert m4_target in orig

# 1. M1 + M3
c_m1_m3 = orig.replace(m1_target, m1_replacement).replace(m3_target, m3_replacement)
with open("candidates/candidate_cl_pair_m1_m3.py", "w", encoding="utf-8") as f:
    f.write(c_m1_m3)

# 2. M1 + M4
c_m1_m4 = orig.replace(m1_target, m1_replacement).replace(m4_target, m4_replacement)
with open("candidates/candidate_cl_pair_m1_m4.py", "w", encoding="utf-8") as f:
    f.write(c_m1_m4)

# 3. M3 + M4
c_m3_m4 = orig.replace(m3_target, m3_replacement).replace(m4_target, m4_replacement)
with open("candidates/candidate_cl_pair_m3_m4.py", "w", encoding="utf-8") as f:
    f.write(c_m3_m4)

# 4. M1 + M3 + M4
c_trio = orig.replace(m1_target, m1_replacement).replace(m3_target, m3_replacement).replace(m4_target, m4_replacement)
with open("candidates/candidate_cl_trio_m1_m3_m4.py", "w", encoding="utf-8") as f:
    f.write(c_trio)

print("Generated pairwise and trio candidate files successfully.")
