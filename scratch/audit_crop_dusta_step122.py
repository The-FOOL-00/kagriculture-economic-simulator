import json

with open("scratch/replays/Whyme_Labs_104824599.json", "r", encoding="utf-8") as f:
    rep = json.load(f)

print("="*80)
print("INSPECTING CROP DUSTA REPLAY (STEPS 120..126)")
print("="*80)
for s in range(120, 127):
    step_data = rep["steps"][s]
    # Crop Dusta was Player 1
    p1_act = step_data[1].get("action", {})
    p1_obs = step_data[1].get("observation", {})
    p1_farm = (p1_obs.get("farms") or [{}, {}])[1] if "farms" in p1_obs else {}
    p1_money = p1_farm.get("money", 0)
    p1_quads = p1_farm.get("unlocked_quadrants", [])
    print(f"Replay Step {s}: P1 Money={p1_money}, Quads={p1_quads}")
    print(f"  P1 Action: {p1_act}")
