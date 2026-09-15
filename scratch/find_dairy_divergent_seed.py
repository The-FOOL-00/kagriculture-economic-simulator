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

dairy_tape = json.load(open("scratch/dairy_specialized_tape.json"))
seeds_data = json.load(open("scratch/shop_world_seeds.json"))
dairy_seeds = seeds_data["SMOOTHIE_SHOP+ICE_CREAM_SHOP"] + seeds_data.get("ICE_CREAM_SHOP+SMOOTHIE_SHOP", [])
test_seeds = dairy_seeds[:50]

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

for idx, s in enumerate(test_seeds):
    # Just test Seat 0
    pb0 = mod_r.Policy("extracted_agents/dmitrii_lb2800")
    g0 = kagsim.Game(s)
    while not g0.done: g0.step(pb0.act(g0.observe(0)), v54.agent(g0.observe(1)))
    r_base0 = g0.reward(0)
    
    pc0 = CandidateDairyPolicy("extracted_agents/dmitrii_lb2800")
    g1 = kagsim.Game(s)
    while not g1.done: g1.step(pc0.act(g1.observe(0)), v54.agent(g1.observe(1)))
    r_cand0 = g1.reward(0)
    
    diff = r_cand0 - r_base0
    if diff != 0:
        print(f"DIFFERENCE AT SEED idx={idx}, seed={s}: Base={r_base0}, Cand={r_cand0}, Diff={diff}", flush=True)
    if idx % 10 == 0:
        print(f"Checked up to idx {idx} (seed {s})...", flush=True)
