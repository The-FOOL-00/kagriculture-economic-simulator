import sys, os
sys.path.insert(0, os.path.abspath("."))
import json

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

for s in (250621, 250617):
    sim = FastKagricultureSim(seed=s)
    obs = sim.reset(seed=s)
    
    blocked_events = []
    
    for step in range(719):
        farm0 = obs[0]["farms"][0]
        tiles0 = farm0["tiles"]
        priv0 = sim.state[0].observation.private
        
        a0 = v49_mod.agent(obs[0])
        a1 = v44_mod.agent(obs[1])
        
        if step >= 600:
            # Check farmer
            fx, fy = farm0["farmer"]
            t = tiles0[fy][fx]
            f_act = a0.get("farmer", ["PASS"])
            if f_act and f_act[0] in ("PLANT", "WATER", "HARVEST", "DIG", "FERTILIZE", "FEED", "CARE"):
                # Check legality
                if f_act[0] == "PLANT":
                    if t is not None:
                        blocked_events.append((step, "farmer", f_act, f"tile occupied by {t.get('crop') if isinstance(t, dict) else t}"))
                elif f_act[0] == "HARVEST":
                    if not isinstance(t, dict) or t.get("yield_units", 0) <= 0:
                        blocked_events.append((step, "farmer", f_act, "no yield"))
                elif f_act[0] == "WATER":
                    if not (isinstance(t, dict) and t.get("kind") == "PLANT") or t.get("watered_today"):
                        blocked_events.append((step, "farmer", f_act, "already watered or not plant"))
                        
            # Check hands
            for i, h_act in enumerate(a0.get("hands", [])):
                if not h_act or i >= len(farm0["hands"]): continue
                hx, hy = farm0["hands"][i]
                ht = tiles0[hy][hx]
                if h_act[0] == "PLANT":
                    if ht is not None:
                        blocked_events.append((step, f"hand_{i}", h_act, f"tile occupied by {ht.get('crop') if isinstance(ht, dict) else ht}"))
                elif h_act[0] == "HARVEST":
                    if not isinstance(ht, dict) or ht.get("yield_units", 0) <= 0:
                        blocked_events.append((step, f"hand_{i}", h_act, "no yield"))
                        
        obs, _, done, _ = sim.step([a0, a1])
        
    print(f"Seed {s}: Total blocked events between Step 600 and 718: {len(blocked_events)}")
    for b in blocked_events[:10]:
        print(f"  Step {b[0]}: Unit {b[1]} attempted {b[2]} -> {b[3]}")
