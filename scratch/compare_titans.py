import difflib

f1 = r"c:\Users\Sundareswaran\Kagriculture\opponents\o1_titan.py"
f2 = r"c:\Users\Sundareswaran\Kagriculture\candidates\slot1_titan_control.py"

with open(f1, 'r', encoding='utf-8') as file1:
    l1 = file1.readlines()
with open(f2, 'r', encoding='utf-8') as file2:
    l2 = file2.readlines()

print(f"o1_titan.py lines: {len(l1)}")
print(f"slot1_titan_control.py lines: {len(l2)}")

# Let's inspect docstrings or top 50 lines of each
print("\n=== TOP 30 LINES OF o1_titan.py ===")
for line in l1[:30]:
    print(line.rstrip())

print("\n=== TOP 30 LINES OF slot1_titan_control.py ===")
for line in l2[:30]:
    print(line.rstrip())
