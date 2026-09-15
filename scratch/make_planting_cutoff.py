with open("candidates/candidate_cl_economic_v1.py", "r", encoding="utf-8") as f:
    text = f.read()

# Replace day <= 20 with day <= 14 for strawberry planting
target = 'elif int(seeds.get("STRAWBERRY", 0) or 0) > 0 and day <= 20:\n                            plant_s.append(pos)'

replacement = 'elif int(seeds.get("STRAWBERRY", 0) or 0) > 0 and day <= 14:  # ENGINE HORIZON CUTOFF: 4 cycles\n                            plant_s.append(pos)'

assert target in text, "Target block not found!"
new_text = text.replace(target, replacement)

with open("candidates/candidate_cl_planting_cutoff.py", "w", encoding="utf-8") as f:
    f.write(new_text)

print("candidates/candidate_cl_planting_cutoff.py generated successfully.")
