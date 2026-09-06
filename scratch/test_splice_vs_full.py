import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
import copy
from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2

with open("scratch/replays/V2_Loss_vs_GAYATHRI SALINI_104796498.json") as f:
    gayathri_steps = json.load(f)["steps"]

gayathri_trace = [s[0].get("action", {}) for s in gayathri_steps[1:]]
# ensure length 720
while len(gayathri_trace) < 720:
    gayathri_trace.append({"farmer": ["PASS"], "hands": [], "market": []})

# H1: Full Gayathri trace with V2 market controller overlay + terminal controller
def agent_H1(obs, config=None):
    step = int(obs.get("step", 0) or 0)
    if step >= 712:
        return v2._terminal_action(obs)
    # Use gayathri action
    action = copy.deepcopy(gayathri_trace[step])
    # Apply V2 market controller if appropriate, or return action
    return action

# H2: Spliced: Gayathri steps 0-264, then V2 steps 265-719
def agent_H2(obs, config=None):
    step = int(obs.get("step", 0) or 0)
    if step >= 712:
        return v2._terminal_action(obs)
    if step < 265:
        return copy.deepcopy(gayathri_trace[step])
    else:
        # V2 base agent
        return v2._base_agent(obs, config)

print("=== TESTING H1 vs H2 on Seeds 42, 100, 2026 ===")
for seed in [42, 100, 2026]:
    # H1 vs V2
    env1 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env1.run([agent_H1, v2.agent])
    h1_score = env1.steps[-1][0]["reward"]
    v2_score1 = env1.steps[-1][1]["reward"]
    
    # H2 vs V2
    env2 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env2.run([agent_H2, v2.agent])
    h2_score = env2.steps[-1][0]["reward"]
    v2_score2 = env2.steps[-1][1]["reward"]
    
    print(f"Seed {seed:4d} | H1={h1_score:,.0f} vs V2={v2_score1:,.0f} (Margin={h1_score-v2_score1:+,.0f}) | H2(Spliced)={h2_score:,.0f} vs V2={v2_score2:,.0f} (Margin={h2_score-v2_score2:+,.0f})")
