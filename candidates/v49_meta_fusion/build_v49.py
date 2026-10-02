#!/usr/bin/env python3
"""Build and assemble candidate V49 Meta Fusion."""

import os
import hashlib

CAND_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CAND_DIR, "..", ".."))

V48_PATH = os.path.join(REPO_ROOT, "candidates", "v48_challenger", "main.py")
V49_PATH = os.path.join(CAND_DIR, "main.py")

V49_OVERLAY = """

# ---------------------------------------------------------------------------
# V49 META FUSION: E402 Late Seed Cap Overlay (Step >= 624 Dead Stock Cap)
# ---------------------------------------------------------------------------
_V48_BASE_AGENT = agent
del agent

_V49_E402_CACHE = {}

def _v49_e402_remaining(native, step, chassis):
    route = native.get('route', 0)
    key = (route, step)
    if key in _V49_E402_CACHE:
        return _V49_E402_CACHE[key]
    need = 0
    for t in range(step + 1, 719):
        tape = chassis.routes[2 if t >= 648 else route]
        act = tape[t]
        need += sum(1 for c in [act.get('farmer') or ['PASS']] + list(act.get('hands') or [])
                    if len(c) > 1 and c[0] == 'PLANT' and c[1] in ('WHEAT', 'CARROT'))
    _V49_E402_CACHE[key] = need
    return need


def agent(observation, configuration=None):
    act = _V48_BASE_AGENT(observation, configuration)
    try:
        step = int(observation.get("step", 0) or 0)
        if step == 0:
            _V49_E402_CACHE.clear()
        if step < 624:
            return act
        if not isinstance(act, dict):
            return act
        mkt = list(act.get("market") or [])
        if not any(len(o) >= 3 and o[0] == 'BUY_SEED' and o[1] in ('WHEAT', 'CARROT') for o in mkt):
            return act
        seat = int(observation['player'])
        chassis = _IMPL.chassis
        native = chassis.players[seat]
        remaining = _v49_e402_remaining(native, step, chassis)
        remaining += sum(1 for queue in native.get('pending', {}).values() for pos, c in queue
                         if len(c) > 1 and c[0] == 'PLANT' and c[1] in ('WHEAT', 'CARROT'))
        units = [act.get('farmer') or ['PASS']] + list(act.get('hands') or [])
        seeds = observation.get('private', {}).get('seeds', {}) or {}
        available = {p: max(0, int(seeds.get(p, 0)) - sum(c[:2] == ['PLANT', p] for c in units)) for p in ('WHEAT', 'CARROT')}
        out = []
        changed = False
        for o in mkt:
            if len(o) >= 3 and o[0] == 'BUY_SEED' and o[1] in available:
                p = o[1]
                qty = max(0, int(o[2]))
                keep = min(qty, max(0, remaining - available[p]))
                available[p] += keep
                if keep < qty:
                    changed = True
                    o = [o[0], p, keep] if keep else []
            out.append(o)
        if changed:
            act["market"] = [o for o in out if o][:10]
    except Exception:
        pass
    return act
"""

def main():
    with open(V48_PATH, 'r', encoding='utf-8') as f:
        v48_code = f.read()

    v49_code = v48_code + V49_OVERLAY

    with open(V49_PATH, 'w', encoding='utf-8') as f:
        f.write(v49_code)

    # Validate compilation
    compile(v49_code, V49_PATH, 'exec')
    h = hashlib.sha256(v49_code.encode('utf-8')).hexdigest().upper()
    print(f"Successfully compiled {V49_PATH}")
    print(f"V49 SHA256: {h}")

if __name__ == '__main__':
    main()
