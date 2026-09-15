with open('candidates/candidate_cl_fert_gated.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace ('MELON', 'WOOL', 'MILK', 'STRAWBERRY', 'FERTILIZER', 'EGG', 'WHEAT')
target1 = 'for item in ("MELON", "WOOL", "MILK", "STRAWBERRY", "FERTILIZER", "EGG", "WHEAT"):'
replacement1 = 'for item in ("MELON", "WOOL", "MILK", "STRAWBERRY", "EGG", "WHEAT"):'

target2 = 'for item in SELLABLE:\n            qty = int(shed.get(item, 0) or 0)'
replacement2 = 'for item in SELLABLE:\n            if item == "FERTILIZER": continue\n            qty = int(shed.get(item, 0) or 0)'

assert target1 in code, "Target 1 not found in code!"
assert target2 in code, "Target 2 not found in code!"

code_retain = code.replace(target1, replacement1).replace(target2, replacement2)

with open('candidates/candidate_cl_fert_gated_retain.py', 'w', encoding='utf-8') as f:
    f.write(code_retain)

print("Successfully created candidates/candidate_cl_fert_gated_retain.py")
