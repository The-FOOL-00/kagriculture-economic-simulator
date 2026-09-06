import sys
sys.path.insert(0, ".")
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2

env = kaggle_environments.make("kaggriculture", configuration={"seed": 215620170, "episodeSteps": 720})

# Hook to capture V2's observations turn by turn
history_p0 = []
history_p1 = []

def p0_wrapper(obs, cfg=None):
    res = v2.agent(obs, cfg)
    if obs["step"] % 24 == 0 or obs["step"] in (715, 719):
        history_p0.append((obs["step"], obs["farms"][0]["money"], len(obs["farms"][0]["hands"]), obs["private"]["shed"].copy(), obs["private"]["seeds"].copy(), res.get("market")))
    return res

def p1_wrapper(obs, cfg=None):
    return v2.agent(obs, cfg)

env.run([p0_wrapper, p1_wrapper])

print("=== V2 (PLAYER 0) TURN-BY-TURN MILESTONES ===")
for step, money, hands, shed, seeds, market in history_p0:
    print(f"Step {step:3d} (D{step//24:2d}): Money=${money:8.1f} | Hands={hands} | Shed={shed} | Seeds={seeds} | Market={market[:3] if market else []}")

print(f"\nFinal Reward: P0 = ${env.steps[-1][0]['reward']:,.1f} | P1 = ${env.steps[-1][1]['reward']:,.1f}")
