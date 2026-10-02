#!/usr/bin/env python3
"""Build candidates/v47_elite_transfer/main.py from validated elite backbone + V44 safeguards."""

import os
import hashlib

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

source_path = os.path.join(REPO_ROOT, "research", "v47", "elite_corpus", "agents", "thomastschinkel_2945", "main.py")
with open(source_path, "r", encoding="utf-8") as f:
    code = f.read()

wrapper = """

# ---------------------------------------------------------------------------
# V47 ELITE TRANSFER: V44 Safeguard Overlay (Step >= 520 CapEx Cutoff)
# ---------------------------------------------------------------------------
_V47_BASE_AGENT = agent
del agent

def agent(observation, configuration=None):
    act = _V47_BASE_AGENT(observation, configuration)
    try:
        step = int(observation.get("step", 0) or 0)
        if not isinstance(act, dict):
            return act
        mkt = list(act.get("market") or [])
        if step >= 520:
            mkt = [o for o in mkt if not (len(o) > 0 and o[0] in ("BUY_ANIMAL", "BUY_LAND"))]
        act["market"] = mkt[:10]
    except Exception:
        pass
    return act
"""

out_dir = os.path.join(REPO_ROOT, "candidates", "v47_elite_transfer")
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, "main.py")

with open(out_file, "w", encoding="utf-8") as f:
    f.write(code + wrapper)

sha = hashlib.sha256(open(out_file, "rb").read()).hexdigest().upper()
print(f"Successfully built {out_file}")
print(f"SHA256: {sha}")
