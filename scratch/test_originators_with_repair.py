import os
import sys
import json
import copy

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import router_parent as mod_r

# Extract ORiginators tape
replay_path = "replays/live_tournament/episode_107543042.json"
with open(replay_path) as f:
    ep = json.load(f)

originators_tape = [s[1].get("action", {}) for s in ep["steps"]]

class OriginatorsRepairedPolicy:
    def __init__(self, tape):
        self.tape = tape
        self.players = {}

    def act(self, obs):
        step = int(obs["step"])
        player = int(obs["player"])
        state = self.players.get(player)
        if state is None or step <= state.last_step:
            state = self.players[player] = mod_r.DayState()
        state.last_step = step

        view = mod_r.FarmView(obs)
        if step < len(self.tape):
            action = copy.deepcopy(self.tape[step])
        else:
            action = {"farmer": ["PASS"], "hands": [], "market": []}

        # Apply Dmitrii's weed repair
        mod_r.repair_weeds(action, view, state, step)
        action["market"] = action.get("market", [])[:mod_r.MAX_ORDERS]
        
        if step == mod_r.LAST_STEP:
            return mod_r.liquidate(view)
        return action

def test():
    pizza_seeds = [50007, 50010, 50012, 50018, 50029]
    print("="*80)
    print("TESTING ORIGINATORS WITH WEED REPAIR vs DMITRII BASE")
    print("="*80)

    for s in pizza_seeds:
        p_orig = OriginatorsRepairedPolicy(originators_tape)
        p_dmi = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        g = kagsim.Game(s)
        while not g.done:
            g.step(p_orig.act(g.observe(0)), p_dmi.act(g.observe(1)))
        c_orig = g.reward(0)
        c_dmi = g.reward(1)
        print(f"Seed {s:5d}: Orig ${c_orig:,.0f} vs Dmi ${c_dmi:,.0f} (Margin: {c_orig - c_dmi:+,.0f})")

if __name__ == "__main__":
    test()
