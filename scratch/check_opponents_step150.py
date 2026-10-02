import sys, os
sys.path.insert(0, os.path.abspath("."))
import json

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod
from scratch.analyze_signals import extract_signals_at_step

def make_adversary(strategy: str):
    def _adv(obs, cfg=None):
        step = int(obs.get("step", 0))
        seat = int(obs.get("player", 0))
        farm = obs["farms"][seat]
        shed = (obs.get("private") or {}).get("shed", {}) or {}
        mkt = []
        if strategy == "DAIRY_FLOOD":
            milk = shed.get("MILK", 0)
            if milk > 0:
                mkt.append(["SELL", "MILK", milk])
            if step < 240 and farm.get("money", 0) >= 400:
                mkt.append(["BUY_ANIMAL", "COW", 1])
        elif strategy == "WOOL_FLOOD":
            wool = shed.get("WOOL", 0)
            if wool > 0:
                mkt.append(["SELL", "WOOL", wool])
            if step < 240 and farm.get("money", 0) >= 500:
                mkt.append(["BUY_ANIMAL", "SHEEP", 1])
        elif strategy == "TERMINAL_DUMPER":
            if step >= 716:
                for prod in ["MILK", "WOOL", "EGG", "STRAWBERRY", "MELON"]:
                    q = shed.get(prod, 0)
                    if q > 0:
                        mkt.append(["SELL", prod, q])
        return {"farmer": ["PASS"], "hands": [], "market": mkt}
    return _adv

opp_list = [
    ("V44", load_elite_agent("V44")),
    ("dmitrii_lb2800", load_elite_agent("dmitrii_lb2800")),
    ("tetsutani_pasture", load_elite_agent("tetsutani_pasture")),
    ("kaitofukami_v48_3009", load_elite_agent("kaitofukami_v48_3009")),
    ("indarkarhana_top10", load_elite_agent("indarkarhana_top10")),
    ("saiteja_mega_3000", load_elite_agent("saiteja_mega_3000")),
    ("DAIRY_FLOOD", make_adversary("DAIRY_FLOOD")),
    ("WOOL_FLOOD", make_adversary("WOOL_FLOOD")),
    ("TERMINAL_DUMPER", make_adversary("TERMINAL_DUMPER"))
]

print(f"{'Opponent':<22} {'Cows @ 150':<12} {'Pastures @ 150':<16} {'Hands @ 150':<13} {'Milk Price':<12} {'Score @ 150':<12}")
print("-" * 88)

for opp_name, opp_agent in opp_list:
    sim = FastKagricultureSim(seed=250600)
    obs = sim.reset()
    prev_obs = None
    for step in range(151):
        if step == 150:
            sig = extract_signals_at_step(obs[0], prev_obs[0] if prev_obs else None, 0)
            print(f"{opp_name:<22} {sig['O1_cows']:<12} {sig['O2_pastures']:<16} {sig['O4_hands']:<13} ${sig['O8_milk_price']:<11} {sig['O10_composite_score']:<12.2f}")
            break
        prev_obs = obs
        a0 = v49_mod.agent(obs[0], sim.configuration)
        a1 = opp_agent.act(obs[1]) if hasattr(opp_agent, "act") else opp_agent(obs[1])
        obs, rewards, done, info = sim.step([a0, a1])
        if done:
            break
