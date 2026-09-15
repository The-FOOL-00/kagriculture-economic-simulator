with open("candidates/candidate_cl_economic_v1.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip_next = False

for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
    if 'crop != "WHEAT" and fert_inv > 0 and t.get("fertilized_until_day", -1) < day' in line:
        indent = " " * 20
        new_lines.append(f"{indent}# STATE-DERIVED FERTILIZER GATING (P+7 <= day <= min(29, P+15))\n")
        new_lines.append(f"{indent}can_fert = False\n")
        new_lines.append(f'{indent}if crop == "STRAWBERRY":\n')
        new_lines.append(f'{indent}    p_day = int(t.get("planted_day", 0) or 0)\n')
        new_lines.append(f"{indent}    can_fert = (p_day + 7 <= day <= min(29, p_day + 15))\n")
        new_lines.append(f'{indent}elif crop != "WHEAT":\n')
        new_lines.append(f"{indent}    can_fert = True\n\n")
        new_lines.append(f'{indent}if can_fert and fert_inv > 0 and t.get("fertilized_until_day", -1) < day and pos not in claimed_action_tiles:\n')
        new_lines.append(f'{indent}    actions[i] = ["FERTILIZE"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue\n')
        skip_next = True
    else:
        new_lines.append(line)

with open("candidates/candidate_cl_fert_gated.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("candidates/candidate_cl_fert_gated.py generated successfully.")
