import hashlib
import os
import glob
import time

files = [
    'main.py',
    'compiler.py',
    'submit_slots.py',
    'stage_championship_candidates.py',
    'agents/hybrid_6c3s_10m.py',
    'agents/hybrid_dynamic_economic.py',
    'agents/hybrid_lookahead.py',
    'engine/livestock_engine.py',
    'engine/dynamic_allocator.py',
    'engine/market_executor.py',
    'engine/labor_scheduler.py',
    'engine/macro_planner.py',
    'engine/world_model.py',
    'engine/opponent_model.py',
    'submission.tar.gz'
] + glob.glob('candidates/*')

print(f"{'File':<40} | {'Size (B)':<10} | {'Modified':<20} | {'SHA256':<64}")
print("-" * 140)
for f in sorted(set(files)):
    if os.path.exists(f) and not os.path.isdir(f):
        data = open(f, 'rb').read()
        sha = hashlib.sha256(data).hexdigest()
        size = len(data)
        mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(f)))
        print(f"{f:<40} | {size:<10} | {mtime:<20} | {sha}")
