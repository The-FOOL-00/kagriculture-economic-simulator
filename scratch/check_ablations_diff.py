import difflib, os

root = r"c:\Users\Sundareswaran\Kagriculture"
abl_dir = os.path.join(root, "scratch", "clean_ablations")
main_py = os.path.join(root, "main.py")

with open(main_py, 'r', encoding='utf-8') as f:
    main_lines = f.readlines()

for fn in sorted(os.listdir(abl_dir)):
    fp = os.path.join(abl_dir, fn)
    with open(fp, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    d = list(difflib.unified_diff(main_lines, lines, fromfile="main.py", tofile=fn))
    print(f"=== DIFF: main.py vs {fn} ({len(d)} lines diff) ===")
    for l in d:
        if l.startswith(('+', '-')) and not l.startswith(('+++', '---')):
            print("  ", l.rstrip())
