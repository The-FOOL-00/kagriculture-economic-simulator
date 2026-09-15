with open("candidates/candidate_cl_economic_v1.py", "r", encoding="utf-8") as f:
    text = f.read()

target = '''                                # STRAWBERRY BATCH HARVEST: require >= 2 units (or terminal season)
                                if yu >= 2 or day >= 27:
                                    ripe_crops.append(pos)'''

replacement = '''                                # HARVEST IMMEDIATE: harvest any ripe strawberry (yu >= 1) to prevent weed decay
                                if yu >= 1:
                                    ripe_crops.append(pos)'''

assert target in text, "Target block not found!"
new_text = text.replace(target, replacement)

with open("candidates/candidate_cl_harvest_priority.py", "w", encoding="utf-8") as f:
    f.write(new_text)

print("candidates/candidate_cl_harvest_priority.py generated successfully.")
