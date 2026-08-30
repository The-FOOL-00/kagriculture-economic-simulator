import os, json
from kaggle_environments import make

def ground_truth_pass(obs, cfg):
    return {"farmer": ["PASS"], "hands": []}

env = make("kaggriculture", configuration={"episodeSteps": 20, "seed": 1000}, debug=True)

p0_trace = []
p1_trace = []

def logging_agent_p0(obs, cfg):
    f0 = obs["farms"][0]
    p0_trace.append({
        "turn": len(p0_trace),
        "seat": 0,
        "step": obs.get("step"),
        "day": obs.get("day"),
        "hour": obs.get("hour"),
        "cash": f0["money"],
        "position": list(f0["farmer"]),
        "land": f0.get("unlocked_quadrants", 1),
        "workers": len(f0.get("hands", [])),
        "crops": sum(1 for row in f0["tiles"] for cell in row if isinstance(cell, dict) and "crop" in cell),
        "animals": sum(1 for row in f0["tiles"] for cell in row if isinstance(cell, dict) and "animal" in cell),
        "market": {k: {"price": obs["market"]["prices"][k], "inventory": obs["market"]["inventory"][k]} for k in obs["market"]["prices"]},
        "town": list(obs["town"]["unlocked_shops"]),
        "inventory": dict(obs["private"]["shed"])
    })
    return ground_truth_pass(obs, cfg)

def logging_agent_p1(obs, cfg):
    f1 = obs["farms"][1]
    p1_trace.append({
        "turn": len(p1_trace),
        "seat": 1,
        "step": obs.get("step"),
        "day": obs.get("day"),
        "hour": obs.get("hour"),
        "cash": f1["money"],
        "position": list(f1["farmer"]),
        "land": f1.get("unlocked_quadrants", 1),
        "workers": len(f1.get("hands", [])),
        "crops": sum(1 for row in f1["tiles"] for cell in row if isinstance(cell, dict) and "crop" in cell),
        "animals": sum(1 for row in f1["tiles"] for cell in row if isinstance(cell, dict) and "animal" in cell),
        "market": {k: {"price": obs["market"]["prices"][k], "inventory": obs["market"]["inventory"][k]} for k in obs["market"]["prices"]},
        "town": list(obs["town"]["unlocked_shops"]),
        "inventory": dict(obs["private"]["shed"])
    })
    return ground_truth_pass(obs, cfg)

env.run([logging_agent_p0, logging_agent_p1])

trace_data = {
    "engine_version": "1.32.7",
    "seed": 1000,
    "p0_trace": p0_trace,
    "p1_trace": p1_trace
}

trace_path = r"c:\Users\Sundareswaran\Kagriculture\current_engine_trace.json"
with open(trace_path, "w") as f:
    json.dump(trace_data, f, indent=2)

print(f"Recorded {len(p0_trace)} turns for P0 and {len(p1_trace)} turns for P1.")
print(f"Trace saved to: {trace_path}")

# Verify observation symmetry and clock
print("\n=== CLOCK & OBSERVATION EQUIVALENCE CHECK ===")
clock_matches = True
obs_matches = True
for t in range(len(p0_trace)):
    t0 = p0_trace[t]
    t1 = p1_trace[t]
    
    # Check clock formula: day * 24 + hour
    calc_step_0 = t0["day"] * 24 + t0["hour"]
    calc_step_1 = t1["day"] * 24 + t1["hour"]
    
    if calc_step_0 != t0["step"] or calc_step_1 != t1["step"] or calc_step_0 != calc_step_1:
        clock_matches = False
        print(f"Clock mismatch at turn {t}: P0 step={t0['step']}, calc={calc_step_0} | P1 step={t1['step']}, calc={calc_step_1}")
        
    # Check market and town equivalence
    if t0["market"] != t1["market"] or t0["town"] != t1["town"]:
        obs_matches = False
        print(f"Public market/town mismatch at turn {t}")

print(f"Clock formula (day * 24 + hour == step) valid across all turns: {clock_matches}")
print(f"Market & Town state 100% identical between P0 & P1 across all turns: {obs_matches}")
