"""
TEST ORIGINATORS ACTION TAPE GENERALIZATION
Extracts the exact 720-step action tape from ORiginators (episode 107543042)
and evaluates its performance vs Dmitrii Base across Pizza seeds.
"""
import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import router_parent as mod_r

# Extract ORiginators tape
replay_path = "replays/live_tournament/episode_107543042.json"
with open(replay_path) as f:
    ep = json.load(f)

# ORiginators was Seat 1
originators_tape = []
for s in ep["steps"]:
    act = s[1].get("action", {})
    originators_tape.append(act)

print(f"Extracted ORiginators tape: {len(originators_tape)} steps")

class OriginatorsReplayPolicy:
    def __init__(self, tape):
        self.tape = tape
        self.players = {}

    def act(self, obs):
        step = int(obs["step"])
        if step < len(self.tape):
            return self.tape[step]
        return {"farmer": ["PASS"], "hands": [], "market": []}

def test_pizza_seeds():
    # Pizza qualification seeds
    pizza_seeds = [50007, 50010, 50012, 50018, 50029, 50030, 50032, 50035, 50037, 50049]
    print("="*85)
    print("TESTING ORIGINATORS TAPE vs DMITRII BASE ACROSS PIZZA SEEDS")
    print("="*85)

    wins = 0
    losses = 0
    margins = []
    orig_cashes = []
    dmi_cashes = []

    for s in pizza_seeds:
        # Seat 0: Originators vs Dmitrii
        p_orig = OriginatorsReplayPolicy(originators_tape)
        p_dmi = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        g0 = kagsim.Game(s)
        while not g0.done:
            g0.step(p_orig.act(g0.observe(0)), p_dmi.act(g0.observe(1)))
        c_orig = g0.reward(0)
        c_dmi = g0.reward(1)
        m0 = c_orig - c_dmi
        margins.append(m0)
        orig_cashes.append(c_orig)
        dmi_cashes.append(c_dmi)
        if m0 > 0: wins += 1
        elif m0 < 0: losses += 1

        # Seat 1: Dmitrii vs Originators
        p_dmi0 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        p_orig1 = OriginatorsReplayPolicy(originators_tape)
        g1 = kagsim.Game(s)
        while not g1.done:
            g1.step(p_dmi0.act(g1.observe(0)), p_orig1.act(g1.observe(1)))
        c_dmi0 = g1.reward(0)
        c_orig1 = g1.reward(1)
        m1 = c_orig1 - c_dmi0
        margins.append(m1)
        orig_cashes.append(c_orig1)
        dmi_cashes.append(c_dmi0)
        if m1 > 0: wins += 1
        elif m1 < 0: losses += 1

        print(f"Seed {s:5d}: S0 Orig ${c_orig:,.0f} vs Dmi ${c_dmi:,.0f} (M: {m0:+,.0f}) | S1 Orig ${c_orig1:,.0f} vs Dmi ${c_dmi0:,.0f} (M: {m1:+,.0f})")

    mean_m = sum(margins) / len(margins)
    mean_orig = sum(orig_cashes) / len(orig_cashes)
    mean_dmi = sum(dmi_cashes) / len(dmi_cashes)
    print("-" * 85)
    print(f"Total Matches: {len(margins)} | Wins: {wins} | Losses: {losses} | Win Rate: {wins/len(margins)*100:.1f}%")
    print(f"Mean Cash: Originators ${mean_orig:,.0f} vs Dmitrii ${mean_dmi:,.0f} | Mean Margin: ${mean_m:+,.2f}")

if __name__ == "__main__":
    test_pizza_seeds()
