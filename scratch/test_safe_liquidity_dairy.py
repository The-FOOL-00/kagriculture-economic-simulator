import json
import os, sys
from collections import defaultdict
import copy

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import router_parent as mod_r
import compiled_v54_plus_residual as v54

def compile_safe_liquidity_dairy():
    tapes = json.load(open("extracted_agents/dmitrii_lb2800/actions.json"))
    tape0 = tapes[0]
    new_tape = copy.deepcopy(tape0)
    
    modified_count = 0
    for step in range(144, 712):
        act = new_tape[step]
        orig_market = act.get("market", [])
        
        # Count critical orders that must NEVER be dropped
        hires = [o for o in orig_market if o and o[0] == "HIRE"]
        buys = [o for o in orig_market if o and o[0] in ("BUY_LAND", "BUY_ANIMAL", "BUY_PRODUCT", "BUY_SEED")]
        orig_sells = [o for o in orig_market if o and o[0] == "SELL"]
        
        # Sells must precede buys if cash is needed, but HIRE must never be displaced!
        # Dedicated budget: 10 max slots
        # If step has hires, hires take priority slots
        available_slots = 10 - len(hires) - len(buys)
        
        new_sells = []
        # On pulse turns where no hires exist (or plenty of slots exist):
        if step % 4 == 0 and available_slots >= 3:
            new_sells.append(["SELL", "MILK", 2])
            new_sells.append(["SELL", "STRAWBERRY", 2])
            new_sells.append(["SELL", "WHEAT", 1])
            
        # Append original sells
        for s in orig_sells:
            if s not in new_sells and len(new_sells) < available_slots:
                new_sells.append(s)
                
        # Final assembly:
        # 1. Essential Sells first (to generate cash)
        # 2. Hires & Buys
        # 3. Remaining sells
        final_market = new_sells + hires + buys
        act["market"] = final_market[:10]
        modified_count += 1
        
    out_path = "scratch/safe_liquidity_dairy_tape.json"
    with open(out_path, "w") as f:
        json.dump(new_tape, f)
    print(f"Compiled Safe Liquidity Dairy Tape ({modified_count} steps modified).")
    return new_tape

class SafeDairyPolicy(mod_r.Policy):
    def __init__(self, f, safe_tape=None):
        super().__init__(f)
        if safe_tape is None:
            safe_tape = json.load(open("scratch/safe_liquidity_dairy_tape.json"))
        self.tapes.append(safe_tape)
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
        
        # Runtime shed headroom: if shed > 75, sell excess wool/fert
        stock = mod_r.projected_shed(a, v)
        if sum(stock.values()) > 75 and len(a["market"]) < 10:
            for it in ["WOOL", "FERTILIZER"]:
                if stock.get(it, 0) > 0 and len(a["market"]) < 10:
                    a["market"].append(["SELL", it, min(6, stock[it])])
                    
        a["market"] = a["market"][:10]
        return mod_r.liquidate(v) if s == 718 else a

def test_safe_liquidity_dairy(seed=50007):
    safe_tape = compile_safe_liquidity_dairy()

    pb = mod_r.Policy("extracted_agents/dmitrii_lb2800")
    psafe = SafeDairyPolicy("extracted_agents/dmitrii_lb2800")
    
    gb = kagsim.Game(seed)
    gsafe = kagsim.Game(seed)
    
    while not gb.done: gb.step(pb.act(gb.observe(0)), v54.agent(gb.observe(1)))
    while not gsafe.done: gsafe.step(psafe.act(gsafe.observe(0)), v54.agent(gsafe.observe(1)))
    
    rb = gb.reward(0)
    rsafe = gsafe.reward(0)
    print(f"Seed {seed}: Base=${rb:,.0f} | SafeDairy=${rsafe:,.0f} | Delta=${rsafe - rb:+,.0f}")

if __name__ == "__main__":
    test_safe_liquidity_dairy(50007)
    test_safe_liquidity_dairy(50266)
    test_safe_liquidity_dairy(50274)
