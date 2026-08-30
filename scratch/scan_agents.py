import os, hashlib, glob

def get_hash(fp):
    h = hashlib.sha256()
    with open(fp, 'rb') as f:
        while c := f.read(8192):
            h.update(c)
    return h.hexdigest()

root = r"c:\Users\Sundareswaran\Kagriculture"

print("=== ALL TITAN IMPLEMENTATIONS ===")
titan_files = []
for r, d, files in os.walk(root):
    if '.git' in r or '__pycache__' in r: continue
    for f in files:
        if 'titan' in f.lower() and f.endswith('.py'):
            fp = os.path.join(r, f)
            rel = os.path.relpath(fp, root)
            h = get_hash(fp)
            size = os.path.getsize(fp)
            titan_files.append((rel, h, size))
            print(f"  {rel:45s} | size: {size:6d} | sha256: {h}")

print("\n=== ALL CONTROL IMPLEMENTATIONS ===")
control_files = []
for r, d, files in os.walk(root):
    if '.git' in r or '__pycache__' in r: continue
    for f in files:
        if ('control' in f.lower() or 'golden' in f.lower()) and f.endswith('.py'):
            fp = os.path.join(r, f)
            rel = os.path.relpath(fp, root)
            h = get_hash(fp)
            size = os.path.getsize(fp)
            control_files.append((rel, h, size))
            print(f"  {rel:45s} | size: {size:6d} | sha256: {h}")

print("\n=== ALL BATCH 14 IMPLEMENTATIONS ===")
batch14_files = []
for r, d, files in os.walk(root):
    if '.git' in r or '__pycache__' in r: continue
    for f in files:
        if 'batch' in f.lower() and '14' in f.lower() and f.endswith('.py'):
            fp = os.path.join(r, f)
            rel = os.path.relpath(fp, root)
            h = get_hash(fp)
            size = os.path.getsize(fp)
            batch14_files.append((rel, h, size))
            print(f"  {rel:45s} | size: {size:6d} | sha256: {h}")

print("\n=== ALL APEX IMPLEMENTATIONS ===")
apex_files = []
for r, d, files in os.walk(root):
    if '.git' in r or '__pycache__' in r: continue
    for f in files:
        if ('apex' in f.lower() or 'slot5' in f.lower() or 'challenger' in f.lower() or 'main.py' == f.lower()) and f.endswith('.py'):
            fp = os.path.join(r, f)
            rel = os.path.relpath(fp, root)
            h = get_hash(fp)
            size = os.path.getsize(fp)
            apex_files.append((rel, h, size))
            print(f"  {rel:45s} | size: {size:6d} | sha256: {h}")
