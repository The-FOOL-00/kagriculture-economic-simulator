import os, sys

with open('research/final_synthesis/teammates/v24/decoded_inner.py', 'r', encoding='utf-8') as f:
    src = f.read()

# Verify print('HP_TELEMETRY',_HP_STATS) exists and replace it
target_str = "print('HP_TELEMETRY',_HP_STATS)"
assert target_str in src, f"Target '{target_str}' not found in decoded inner source!"
clean_src = src.replace(target_str, "pass")

# Outer safety wrapper
outer_wrapper = """

# ---------------------------------------------------------------------------
# Final Production Safety & Sanitation Layer
# ---------------------------------------------------------------------------
import copy as _copy

_FINAL_PARENT = agent
_FINAL_SAFE = {"farmer": ["PASS"], "hands": [], "market": []}

def final_safety_agent(observation, configuration=None):
    try:
        action = _FINAL_PARENT(observation, configuration)
    except Exception:
        return dict(_FINAL_SAFE)
    if not isinstance(action, dict):
        return dict(_FINAL_SAFE)
    action = _copy.deepcopy(action)
    action.setdefault("farmer", ["PASS"])
    action.setdefault("hands", [])
    action.setdefault("market", [])
    if not isinstance(action["hands"], list):
        action["hands"] = []
    if not isinstance(action["market"], list):
        action["market"] = []
    action["market"] = action["market"][:10]
    return action

agent = final_safety_agent
kaggle_submission_agent = final_safety_agent
"""

full_code = clean_src + outer_wrapper

out_path = 'research/final_synthesis/final_candidate/main.py'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(full_code)

compile(full_code, out_path, 'exec')
print(f'Successfully built and compiled {out_path}! Length: {len(full_code)} chars, {full_code.count(chr(10))} lines.')
