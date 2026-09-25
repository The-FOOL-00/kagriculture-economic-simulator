import time
import copy
import sys
import os
sys.path.insert(0, '.')
sys.path.insert(0, './scripts')
import kaggle_environments.envs.kaggriculture.kaggriculture as kg
from scripts.v32_common import load_agent

class DummyConfig:
    def __init__(self, seed=249635):
        self.seed = seed
        self.episodeSteps = 720
        self.turnsPerDay = 24
        self.boardSize = 10
        self.shedCapacity = 100
        self.startingMoney = 100
        self.wheatStartingDemand = 20
        self.wheatSupplyWeight = 0.5
        self.randomStartingDemands = False
        self.maxMarketOrders = 10
        self.startingSeedCount = 4
        self.farmStartingWeeds = 2
        self.weedsPerDay = 1
        self.daysBetweenShops = 3

class DummyEnv:
    def __init__(self, seed=249635):
        self.configuration = DummyConfig(seed)
        self.done = False

class DummyAgentState:
    def __init__(self, player, configuration):
        self.action = {}
        self.status = "ACTIVE"
        self.reward = 0.0
        class Obs:
            pass
        self.observation = Obs()
        self.observation.player = player
        self.observation.step = 0
        self.observation.day = 0
        self.observation.hour = 0

def create_direct_game(seed=249635):
    env = DummyEnv(seed)
    s0 = DummyAgentState(0, env.configuration)
    s1 = DummyAgentState(1, env.configuration)
    state = [s0, s1]
    kg._initialize(state, env)
    return env, state

def run_direct_game():
    env, state = create_direct_game(249635)
    a = load_agent('E2_A7')
    b = load_agent('E0_V3')
    
    t0 = time.perf_counter()
    
    for step in range(719):
        # Build observations for agents
        # In kaggriculture, obs0 has farms, market, town, day, hour, step
        obs0_dict = {
            "player": 0,
            "step": step,
            "day": step // 24,
            "hour": step % 24,
            "farms": state[0].observation.farms,
            "market": state[0].observation.market,
            "town": state[0].observation.town,
            "private": state[0].observation.private
        }
        obs1_dict = {
            "player": 1,
            "step": step,
            "day": step // 24,
            "hour": step % 24,
            "farms": state[0].observation.farms,
            "market": state[0].observation.market,
            "town": state[0].observation.town,
            "private": state[1].observation.private
        }
        
        act0 = a.act(obs0_dict)
        act1 = b.act(obs1_dict)
        
        state[0].action = act0
        state[1].action = act1
        state[0].observation.step = step
        state[1].observation.step = step
        
        kg.interpreter(state, env)
        if env.done or state[0].status == "DONE":
            break
            
    dur = time.perf_counter() - t0
    r0 = state[0].reward
    r1 = state[1].reward
    print(f"Direct engine completed in {dur:.3f}s (SPS: {720/dur:.1f}), r0={r0}, r1={r1}")

if __name__ == '__main__':
    run_direct_game()
