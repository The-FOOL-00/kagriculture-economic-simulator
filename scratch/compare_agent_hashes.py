import os, hashlib

def hash_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while c := f.read(8192):
            h.update(c)
    return h.hexdigest(), os.path.getsize(p)

titan_candidates = [
    r'opponents/o1_titan.py',
    r'candidates/slot1_titan_control.py',
    r'agents/titan_agent.py',
    r'opponents/o12_top_meta.py'
]

control_candidates = [
    r'agents/ground_truth_control_current_engine.py',
    r'agents/slot4_control_frozen_v2.py',
    r'candidates/slot4_control_frozen_v2.py',
    r'agents/control_frozen.py'
]

apex_candidates = [
    r'main.py',
    r'candidates/slot5_apex_synthesis_v2.py',
    r'candidates/apex_champion_v3.py',
    r'clean_ablations/apex_no_2day_feed.py'
]

print("=== TITAN IMPLEMENTATIONS ===")
for p in titan_candidates:
    if os.path.exists(p):
        digest, sz = hash_file(p)
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            lc = len(f.readlines())
        print(f"{p}: {digest} ({sz} bytes, {lc} lines)")
    else:
        print(f"{p}: NOT FOUND")

print("\n=== CONTROL IMPLEMENTATIONS ===")
for p in control_candidates:
    if os.path.exists(p):
        digest, sz = hash_file(p)
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            lc = len(f.readlines())
        print(f"{p}: {digest} ({sz} bytes, {lc} lines)")
    else:
        print(f"{p}: NOT FOUND")

print("\n=== APEX IMPLEMENTATIONS ===")
for p in apex_candidates:
    if os.path.exists(p):
        digest, sz = hash_file(p)
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            lc = len(f.readlines())
        print(f"{p}: {digest} ({sz} bytes, {lc} lines)")
    else:
        print(f"{p}: NOT FOUND")
