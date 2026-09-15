import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import router_parent as mod_r
import compiled_v54_plus_residual as v54
import copy

def trace_divergence(seed=50007):
    dairy_tape = json.load(open("scratch/dairy_specialized_tape.json"))
    
    class CandidateDairyPolicy(mod_r.Policy):
        def __init__(self, folder):
            super().__init__(folder)
            self.tapes.append(dairy_tape)
        def act(self, observation):
            step = int(observation["step"])
            player = int(observation["player"])
            state = self.players.get(player)
            if state is None or step <= state.last_step:
                state = self.players[player] = mod_r.DayState()
            state.last_step = step
            if step == mod_r.ROUTE_STEP:
                state.plan = 13
            if step == mod_r.FINAL_PLAN_STEP:
                state.plan = 2
            view = mod_r.FarmView(observation)
            tape = self.tapes[state.plan]
            action = copy.deepcopy(tape[step])
            mod_r.repair_weeds(action, view, state, step)
            mod_r.subtract_advanced_sales(action, state, step)
            mod_r.advance_sales(action, view, state, tape, step)
            action["market"] = action["market"][:mod_r.MAX_ORDERS]
            return mod_r.liquidate(view) if step == mod_r.LAST_STEP else action

    pb0 = mod_r.Policy("extracted_agents/dmitrii_lb2800")
    pc0 = CandidateDairyPolicy("extracted_agents/dmitrii_lb2800")
    
    g_base = kagsim.Game(seed)
    g_cand = kagsim.Game(seed)
    
    print(f"=== TRACING SEED {seed} DIVERGENCE ===")
    
    for s in range(719):
        obs_b = g_base.observe(0)
        obs_c = g_cand.observe(0)
        
        act_b = pb0.act(obs_b)
        act_c = pc0.act(obs_c)
        
        act_opp_b = v54.agent(g_base.observe(1))
        act_opp_c = v54.agent(g_cand.observe(1))
        
        g_base.step(act_b, act_opp_b)
        g_cand.step(act_c, act_opp_c)
        
        c_base = g_base.reward(0)
        c_cand = g_cand.reward(0)
        
        # Check around steps 144 to 300
        if 144 <= s <= 300 and (s % 24 in (0, 1, 2) or abs(c_base - c_cand) > 500 or c_cand < 1000):
            d = s // 24
            h = s % 24
            m_b = act_b.get("market", [])
            m_c = act_c.get("market", [])
            print(f"Step {s:3d} (D{d:02d} h{h:02d}): Base Cash=${c_base:6,.0f} | Cand Cash=${c_cand:6,.0f} | Diff=${c_cand - c_base:+6,.0f}")
            if m_b != m_c:
                print(f"    Base Mkt: {m_b}")
                print(f"    Cand Mkt: {m_c}")

if __name__ == "__main__":
    trace_divergence(50007)
