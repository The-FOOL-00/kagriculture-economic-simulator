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

def compute_safe_cash_floor(step):
    day = step // 24
    hour = step % 24
    
    # Base operating buffer
    floor = 500
    
    # Night hours (hour 18 to 23): prepare for dawn expenditures
    if hour >= 18:
        # Morning hire cost for 11 hands = 232
        floor += 250
        # Feed for first 6 hours of next day
        floor += 450
        # If Day 5 night (Day 6 NE land): $1000
        if day == 5:
            floor += 1000
        # If Day 10 night (Day 11 SW land): $2000
        elif day == 10:
            floor += 2000
        # Replanting seeds on Day 11
        if day == 10:
            floor += 1600
    elif hour <= 4:
        # Early morning: hiring and morning feed
        floor += 250 + 300
    else:
        # Daytime operating buffer
        floor += 300
        
    return floor

def compile_liquidity_guaranteed_dairy():
    # Load original Tape 0
    tapes = json.load(open("extracted_agents/dmitrii_lb2800/actions.json"))
    tape0 = tapes[0]
    new_tape = copy.deepcopy(tape0)
    
    # Window 0 (0..143) is untouched
    # In Window 1 (144..711):
    # 1. Maintain ALL original wool, fertilizer, melon, wheat sales from Tape 0 as baseline!
    # 2. On pulse turns (step % 4 == 0), ADD targeted Dairy sales:
    #    ['SELL', 'MILK', 2], ['SELL', 'STRAWBERRY', 2], ['SELL', 'WHEAT', 1]
    # 3. Add Shed Headroom Guard: if wool or fertilizer exists, ensure it is sold periodically!
    
    modified_count = 0
    for step in range(144, 712):
        act = new_tape[step]
        orig_market = act.get("market", [])
        
        # Non-sell orders and sell orders:
        # CRITICAL ENGINE RULE: SELLS MUST PRECEDE BUYS TO FUND PURCHASES IN THE SAME STEP!
        buys = [o for o in orig_market if o and o[0] != "SELL"]
        orig_sells = [o for o in orig_market if o and o[0] == "SELL"]
        
        new_sells = []
        if step % 4 == 0:
            # Pulse turn: add shop targeted sales FIRST to get best town absorption
            new_sells.append(["SELL", "MILK", 2])
            new_sells.append(["SELL", "STRAWBERRY", 2])
            new_sells.append(["SELL", "WHEAT", 1])
            
        # ALWAYS KEEP original sales from tape 0 (including Wool and Fertilizer) so cash is preserved!
        for s in orig_sells:
            # Don't duplicate if already selling that item on pulse
            if step % 4 == 0 and s[1] in ("MILK", "STRAWBERRY", "WHEAT"):
                continue
            new_sells.append(s)
            
        new_market = new_sells + buys
        act["market"] = new_market[:10]
        modified_count += 1
        
    out_path = "scratch/dairy_liquidity_guaranteed_tape.json"
    with open(out_path, "w") as f:
        json.dump(new_tape, f)
    print(f"Compiled Liquidity-Guaranteed Dairy Tape ({modified_count} steps modified).")
    return new_tape

class GuaranteedPolicy(mod_r.Policy):
    def __init__(self, f, guaranteed_tape=None):
        super().__init__(f)
        if guaranteed_tape is None:
            guaranteed_tape = json.load(open("scratch/dairy_liquidity_guaranteed_tape.json"))
        self.tapes.append(guaranteed_tape)
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
        
        # LIQUIDITY INVARIANT AT RUNTIME:
        floor = compute_safe_cash_floor(s)
        cash = obs["farms"][p]["money"]
        if cash < floor and len(a["market"]) < 10:
            stock = mod_r.projected_shed(a, v)
            for item in ["WOOL", "MILK", "STRAWBERRY", "FERTILIZER"]:
                if stock.get(item, 0) > 0 and len(a["market"]) < 10:
                    a["market"].append(["SELL", item, min(4, stock[item])])
                    
        # SHED HEADROOM INVARIANT AT RUNTIME:
        stock = mod_r.projected_shed(a, v)
        if sum(stock.values()) > 65 and len(a["market"]) < 10:
            for item in ["WOOL", "FERTILIZER", "WHEAT"]:
                if stock.get(item, 0) > 0 and len(a["market"]) < 10:
                    a["market"].append(["SELL", item, min(8, stock[item])])
                    
        a["market"] = a["market"][:10]
        return mod_r.liquidate(v) if s == 718 else a

def test_guaranteed_vs_base(seed=50007):
    guaranteed_tape = compile_liquidity_guaranteed_dairy()
    failed_dairy_tape = json.load(open("scratch/dairy_specialized_tape.json"))

    class FailedDairyPolicy(mod_r.Policy):
        def __init__(self, f):
            super().__init__(f)
            self.tapes.append(failed_dairy_tape)
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
    pfail = FailedDairyPolicy("extracted_agents/dmitrii_lb2800")
    pguard = GuaranteedPolicy("extracted_agents/dmitrii_lb2800")
    
    gb = kagsim.Game(seed)
    gfail = kagsim.Game(seed)
    gguard = kagsim.Game(seed)
    
    for s in range(719):
        gb.step(pb.act(gb.observe(0)), v54.agent(gb.observe(1)))
        gfail.step(pfail.act(gfail.observe(0)), v54.agent(gfail.observe(1)))
        gguard.step(pguard.act(gguard.observe(0)), v54.agent(gguard.observe(1)))
        
    rb = gb.reward(0)
    rfail = gfail.reward(0)
    rguard = gguard.reward(0)
    
    print(f"\nRESULTS ON SEED {seed}:")
    print(f"  Dmitrii Base Cash:             ${rb:,.0f}")
    print(f"  Failed Dairy Candidate:        ${rfail:,.0f} (Deficit: ${rfail - rb:+,.0f})")
    print(f"  Liquidity-Guaranteed Dairy:    ${rguard:,.0f} (Delta:   ${rguard - rb:+,.0f})")

if __name__ == "__main__":
    test_guaranteed_vs_base(50007)
    test_guaranteed_vs_base(50266) # The worst seed (-$61,561)
