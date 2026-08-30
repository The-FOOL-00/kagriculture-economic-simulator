import difflib

with open(r"C:\Users\Sundareswaran\.gemini\antigravity-ide\brain\1a3b82a1-c6f0-4548-874b-0e3add7eb4e8\scratch\strategies_lab.py", "r") as f1:
    l1 = f1.readlines()

with open("agents/hybrid_6c3s_10m.py", "r") as f2:
    l2 = f2.readlines()

print(f"strategies_lab.py: {len(l1)} lines")
print(f"hybrid_6c3s_10m.py: {len(l2)} lines")

# Let's inspect differences in logic
for line in difflib.unified_diff(l1[25:395], l2[100:330], fromfile="scratch_lab", tofile="hybrid_6c3s"):
    print(line, end="")
