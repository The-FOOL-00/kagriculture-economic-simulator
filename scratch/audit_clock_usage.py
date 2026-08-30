import os, glob

modules_to_check = []
for root, dirs, files in os.walk('.'):
    # skip .git, __pycache__, env_backup
    if any(x in root for x in ['.git', '__pycache__', 'env_backup']):
        continue
    for f in files:
        if f.endswith('.py'):
            modules_to_check.append(os.path.normpath(os.path.join(root, f)))

results = []

for mod_path in sorted(modules_to_check):
    with open(mod_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    uses_step_raw = 'obs["step"]' in content or "obs['step']" in content or 'state["step"]' in content
    uses_step_get = 'obs.get("step"' in content or "obs.get('step'" in content
    uses_day_hour = ('obs.get("day"' in content or 'obs["day"]' in content or "obs.get('day'" in content) and \
                    ('obs.get("hour"' in content or 'obs["hour"]' in content or "obs.get('hour'" in content)
    uses_canonical_clock = 'day * 24 + hour' in content or 'day*24 + hour' in content or 'day*24+hour' in content
    
    # Determine risk
    if uses_step_raw and not uses_canonical_clock:
        risk = "HIGH (Raw obs['step'] without canonical fallback)"
        p1_safe = "NO (Unsafe in manual step loops)"
    elif uses_step_get and not uses_canonical_clock:
        risk = "MEDIUM (obs.get('step') returns None for P1 in manual step loops)"
        p1_safe = "PARTIAL (Safe in env.run, unsafe in manual loops)"
    elif uses_canonical_clock:
        risk = "NONE (Uses canonical day*24+hour clock)"
        p1_safe = "YES (100% P1-Safe)"
    else:
        # Check if it has an agent or simulation logic
        if 'def agent(' in content or 'def my_agent(' in content or 'class ' in content:
            risk = "LOW (No direct step indexing or helper)"
            p1_safe = "YES"
        else:
            risk = "N/A (Script / Utility)"
            p1_safe = "N/A"
            
    results.append({
        "file": mod_path,
        "uses_step": "Yes" if (uses_step_raw or uses_step_get) else "No",
        "uses_day_hour": "Yes" if uses_day_hour else "No",
        "p1_safe": p1_safe,
        "risk": risk
    })

print(f"Audited {len(results)} python files.")
# Print markdown table for key agents/modules
print("\n| Module | Uses step? | Uses day/hour? | P1-safe? | Risk |")
print("| :--- | :---: | :---: | :---: | :--- |")
for r in results:
    if any(k in r["file"] for k in ['agents', 'candidates', 'opponents', 'main.py', 'bot.py', 'grandmaster', 'economy', 'worker_scheduler']):
        print(f"| `{r['file']}` | {r['uses_step']} | {r['uses_day_hour']} | {r['p1_safe']} | {r['risk']} |")
