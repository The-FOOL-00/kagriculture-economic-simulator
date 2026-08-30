import os, glob, re

root_dir = r"c:\Users\Sundareswaran\Kagriculture"
patterns = [
    r'obs\[["\']step["\']\]',
    r'obs\.get\(["\']step["\']',
    r'state\[["\']step["\']\]',
    r'state\.get\(["\']step["\']',
    r'\.step\b',
    r'step\s*=',
    r'obs\.step\b',
    r'observation\[["\']step["\']\]',
    r'observation\.get\(["\']step["\']',
]

results = {}

for root, dirs, files in os.walk(root_dir):
    if '.git' in root or '__pycache__' in root:
        continue
    for f in files:
        if f.endswith('.py') or f.endswith('.json') or f.endswith('.md'):
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, root_dir)
            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                    matches = []
                    for lno, line in enumerate(content.splitlines()):
                        for pat in patterns:
                            if re.search(pat, line):
                                matches.append((lno + 1, line.strip()))
                                break
                    if matches:
                        results[rel] = matches
            except Exception as e:
                pass

print(f"Found matches in {len(results)} files.\n")
for rel, matches in sorted(results.items()):
    if any(folder in rel for folder in ['agents', 'candidates', 'opponents', 'sweep_agents', 'ablation_agents', 'main.py', 'farm_state.py', 'worker_scheduler.py', 'economy.py']):
        print(f"=== {rel} ({len(matches)} matches) ===")
        for lno, line in matches[:10]:
            print(f"  L{lno:4d}: {line}")
        if len(matches) > 10:
            print(f"  ... and {len(matches) - 10} more")
