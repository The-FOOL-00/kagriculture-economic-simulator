import json
import os, sys
from collections import defaultdict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim, copy
import router_parent as mod_r
import compiled_v54_plus_residual as v54

dairy_tape = json.load(open("scratch/dairy_specialized_tape.json"))

class Cand(mod_r.Policy):
    def __init__(self, f):
        super().__init__(f)
        self.tapes.append(dairy_tape)
    def act(self, obs):
        s = int(obs["step"])
        p = int(obs["player"])
        st = self.players.get(p)
        if st is None or s <= st.last_step: st = self.players[p] = mod_r.DayState()
        st.last_step = s
        if s == 144: st.plan = 13
        if s == 648: st.plan = 2
        v = mod_r.FarmView(obs)
        t = self.tapes[st.plan]
        a = copy.deepcopy(t[s])
        mod_r.repair_weeds(a, v, st, s)
        mod_r.subtract_advanced_sales(a, st, s)
        mod_r.advance_sales(a, v, st, t, s)
        a["market"] = a["market"][:10]
        return mod_r.liquidate(v) if s == 718 else a

pb = mod_r.Policy("extracted_agents/dmitrii_lb2800")
pc = Cand("extracted_agents/dmitrii_lb2800")
gb = kagsim.Game(50007)
gc = kagsim.Game(50007)

for s in range(505):
    gb.step(pb.act(gb.observe(0)), v54.agent(gb.observe(1)))
    gc.step(pc.act(gc.observe(0)), v54.agent(gc.observe(1)))
    if s in [288, 360, 504]:
        d = s // 24
        obs_b = gb.observe(0)
        obs_c = gc.observe(0)
        
        f_b = obs_b["farms"][0]
        f_c = obs_c["farms"][0]
        
        shed_b = obs_b["private"]["shed"]
        shed_c = obs_c["private"]["shed"]
        
        tot_b = sum(shed_b.values())
        tot_c = sum(shed_c.values())
        
        print(f"\n--- STEP {s} (Day {d}) ---")
        print(f"Base: Cash=${f_b['money']:,.0f} | ShedTotal={tot_b}/100 | Shed={shed_b}")
        print(f"Cand: Cash=${f_c['money']:,.0f} | ShedTotal={tot_c}/100 | Shed={shed_c}")
