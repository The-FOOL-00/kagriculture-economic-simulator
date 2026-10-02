import sys, importlib.util, kaggle_environments as ke
from pathlib import Path

REPO = Path("C:/Users/Sundareswaran/Kagriculture")

def load_agent(path):
    spec = importlib.util.spec_from_file_location("agent_mod", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.agent

# --- Load V49 ---
v49 = load_agent(REPO / "candidates/v49_meta_fusion/main.py")
print("V49 loaded")

# --- Load Majkel1337 replay agent (inline, with correct path) ---
import json, gzip, random
from collections import defaultdict

REPLAY_DIR = REPO / "research/v60/data/sep_replays"
majkel_episodes = []
for f in sorted(REPLAY_DIR.glob("*.json.gz"), reverse=True):
    try:
        d = json.loads(gzip.open(f).read())
        teams = d.get("info", {}).get("TeamNames", [])
        if "Majkel1337" in teams:
            seat = teams.index("Majkel1337")
            actions = [step[seat].get("action") for step in d.get("steps", [])
                       if seat < len(step) and step[seat].get("action") is not None]
            if actions:
                majkel_episodes.append(actions)
    except Exception:
        pass

print(f"Loaded {len(majkel_episodes)} Majkel1337 episodes ({sum(len(e) for e in majkel_episodes)} total actions)")

if not majkel_episodes:
    print("ERROR: No Majkel1337 episodes found.")
    sys.exit(1)

ep_idx = [0]
step_idx = [0]

def majkel_agent(obs, config=None):
    ep = majkel_episodes[ep_idx[0] % len(majkel_episodes)]
    if step_idx[0] >= len(ep):
        ep_idx[0] = (ep_idx[0] + 1) % len(majkel_episodes)
        step_idx[0] = 0
        ep = majkel_episodes[ep_idx[0]]
    act = ep[step_idx[0]]
    step_idx[0] += 1
    return act

# --- Run benchmark ---
N_SEEDS = 32
wins = losses = 0
print(f"\nRunning V49 vs Majkel1337: {N_SEEDS} seeds x 2 seats = {N_SEEDS*2} legs")

for seed in range(N_SEEDS):
    for seat in range(2):
        # Reset replay position each game
        ep_idx[0] = seed % len(majkel_episodes)
        step_idx[0] = 0
        agents = [v49, majkel_agent] if seat == 0 else [majkel_agent, v49]
        try:
            env = ke.make("kaggriculture", debug=False)
            env.run(agents)
            final = env.steps[-1]
            r = [final[i]["reward"] for i in range(2)]
            v49_r = r[seat]
            opp_r = r[1 - seat]
            if v49_r > opp_r:
                wins += 1
            else:
                losses += 1
        except Exception as e:
            print(f"  [ERR] seed={seed} seat={seat}: {e}")
            losses += 1
    if (seed + 1) % 8 == 0:
        total = wins + losses
        print(f"  After {total} legs: {wins}W {losses}L = {100*wins/total:.1f}%")

total = wins + losses
print(f"\n=== V49 vs Majkel1337 (Sep 2026) ===")
print(f"Result: {wins}/{total} = {100*wins/total:.1f}% win rate")
if wins/total >= 0.95:
    print("VERDICT: V49 DOMINATES — no development needed")
elif wins/total >= 0.80:
    print("VERDICT: V49 LEADS but gap exists — investigate further")
else:
    print("VERDICT: REAL GAP FOUND — V50 development warranted")
