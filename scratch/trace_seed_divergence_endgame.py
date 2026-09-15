import json
import os, sys

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

for s in range(719):
    gb.step(pb.act(gb.observe(0)), v54.agent(gb.observe(1)))
    gc.step(pc.act(gc.observe(0)), v54.agent(gc.observe(1)))
    if s in [360, 432, 504, 576, 648, 718]:
        d = s // 24
        rb = gb.reward(0)
        rc = gc.reward(0)
        print(f"D{d:2d} (s{s:3d}): Base=${rb:6,.0f} | Cand=${rc:6,.0f} | Diff=${rc - rb:+6,.0f}")
