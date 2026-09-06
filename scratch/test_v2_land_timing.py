import sys
import os
sys.path.insert(0, os.path.abspath("."))
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2

def test_land_unlocks(seed=1000):
    env = kaggle_environments.make('kaggriculture', configuration={'seed': seed, 'episodeSteps': 720}, debug=False)
    env.reset()
    for step in range(719):
        obs0 = env.state[0].observation
        act0 = v2.agent(obs0)
        env.step([act0, 'random'])
        farm = env.state[0].observation['farms'][0]
        unlocked = farm.get('unlocked_quadrants', [])
        money = farm.get('money')
        if step in [167, 168, 169, 254, 255, 256]:
            print(f"Step {step}: money={money}, unlocked={unlocked}")

if __name__ == '__main__':
    test_land_unlocks()
