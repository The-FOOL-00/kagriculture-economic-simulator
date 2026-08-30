import difflib, os

def diff_files(p1, p2, n1, n2):
    with open(p1, 'r', encoding='utf-8') as f1, open(p2, 'r', encoding='utf-8') as f2:
        l1 = f1.readlines()
        l2 = f2.readlines()
    d = list(difflib.unified_diff(l1, l2, fromfile=n1, tofile=n2))
    print(f"=== DIFF: {n1} vs {n2} (total diff lines: {len(d)}) ===")
    for line in d[:30]:
        print(line.rstrip())
    if len(d) > 30:
        print(f"... and {len(d)-30} more lines")

ctrl = r"c:\Users\Sundareswaran\Kagriculture\agents\slot4_control_frozen_v2.py"
b14_1 = r"c:\Users\Sundareswaran\Kagriculture\agents\ablation_batch_14.py"
b14_2 = r"c:\Users\Sundareswaran\Kagriculture\generated_agents_1_32_7\ablation_batch_14.py"
b14_3 = r"c:\Users\Sundareswaran\Kagriculture\generated_agents_1_32_7\sweep_batch_14.py"

diff_files(ctrl, b14_1, "Control_v2", "agents/ablation_batch_14.py")
print()
diff_files(ctrl, b14_2, "Control_v2", "generated_agents_1_32_7/ablation_batch_14.py")
print()
diff_files(ctrl, b14_3, "Control_v2", "generated_agents_1_32_7/sweep_batch_14.py")
