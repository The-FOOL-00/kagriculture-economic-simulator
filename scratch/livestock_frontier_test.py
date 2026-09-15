"""
PHASE 13: FOCUSED LIVESTOCK MARGINAL VALUE BENCHMARK (MILK & WOOL FRONTIER)
Measures the economic upside of optimizing:
1. Milk sale batch size: [2, 4, 6, 8, 12, ALL]
2. Wool sale batch size: [2, 4, 6, 8, ALL]
3. Sale timing for livestock goods: step % 4 == 1 vs immediate vs base
4. Feed efficiency / reserve threshold
Compares maximum plausible livestock gain against crop portfolio upside.
"""
import os, sys, json
from typing import Dict, List, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2

class LivestockTunedAgent(ClosedLoopAgentV2):
    def __init__(
        self,
        milk_batch: int = 6,
        wool_batch: int = 4,
        timing_mod: int = 1, # step % 4 == 1
        feed_per_animal: int = 3
    ):
        super().__init__(jit_headroom_threshold=96)
        self.milk_batch = milk_batch
        self.wool_batch = wool_batch
        self.timing_mod = timing_mod
        self.feed_per_animal = feed_per_animal

    def act(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        step = int(obs["step"])
        action = super().act(obs)
        
        # Intercept and tune milk and wool market sales
        if self.timing_mod is not None:
            # Active pulsed selling of milk and wool on step % 4 == timing_mod
            if step % 4 == self.timing_mod:
                shed = obs["private"]["shed"]
                cur_orders = action.get("market", [])
                
                # Check milk
                milk = shed.get("MILK", 0)
                if milk > 0 and len(cur_orders) < 10:
                    batch = milk if self.milk_batch == -1 else min(milk, self.milk_batch)
                    cur_orders.append(["SELL", "MILK", batch])
                    
                # Check wool
                wool = shed.get("WOOL", 0)
                if wool > 0 and len(cur_orders) < 10:
                    batch = wool if self.wool_batch == -1 else min(wool, self.wool_batch)
                    cur_orders.append(["SELL", "WOOL", batch])
                    
                action["market"] = cur_orders[:10]
        return action

def evaluate_livestock_config(name: str, milk_b: int, wool_b: int, t_mod: int, seeds: List[int]) -> Dict[str, Any]:
    deltas_vs_v2 = []
    scores = []
    
    for s in seeds:
        for seat in [0, 1]:
            # Agent game
            g_test = kagsim.Game(s)
            p_test = LivestockTunedAgent(milk_batch=milk_b, wool_batch=wool_b, timing_mod=t_mod)
            p_dmi1 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
            if seat == 0:
                while not g_test.done: g_test.step(p_test.act(g_test.observe(0)), p_dmi1.act(g_test.observe(1)))
                r_test = g_test.reward(0)
            else:
                while not g_test.done: g_test.step(p_dmi1.act(g_test.observe(0)), p_test.act(g_test.observe(1)))
                r_test = g_test.reward(1)
                
            # V2 baseline game
            g_v2 = kagsim.Game(s)
            p_v2 = ClosedLoopAgentV2()
            p_dmi2 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
            if seat == 0:
                while not g_v2.done: g_v2.step(p_v2.act(g_v2.observe(0)), p_dmi2.act(g_v2.observe(1)))
                r_v2 = g_v2.reward(0)
            else:
                while not g_v2.done: g_v2.step(p_dmi2.act(g_v2.observe(0)), p_v2.act(g_v2.observe(1)))
                r_v2 = g_v2.reward(1)
                
            deltas_vs_v2.append(r_test - r_v2)
            scores.append(r_test)
            
    mean_delta = sum(deltas_vs_v2) / len(deltas_vs_v2)
    mean_score = sum(scores) / len(scores)
    return {
        "config": name,
        "milk_batch": milk_b,
        "wool_batch": wool_b,
        "timing_mod": t_mod,
        "mean_score": round(mean_score, 2),
        "mean_delta_vs_v2": round(mean_delta, 2),
        "worst_delta": round(min(deltas_vs_v2), 2),
        "best_delta": round(max(deltas_vs_v2), 2)
    }

def run_livestock_benchmark():
    # Evaluate across 20 representative discovery seeds (40 games)
    seeds = list(range(50000, 50020))
    print(f"Running Livestock Frontier Benchmark across {len(seeds)} seeds (40 games per config)...")
    
    configs = [
        ("V2 Baseline (Unmodified)", 6, 4, None),
        ("Milk Batch 2 / Wool 2 (Small)", 2, 2, 1),
        ("Milk Batch 4 / Wool 4 (Balanced)", 4, 4, 1),
        ("Milk Batch 6 / Wool 4 (Pulsed %4==1)", 6, 4, 1),
        ("Milk Batch 8 / Wool 6 (Medium)", 8, 6, 1),
        ("Milk Batch 12 / Wool 8 (Large)", 12, 8, 1),
        ("Milk ALL / Wool ALL (Bulk Dump)", -1, -1, 1),
        ("Timing %4==0 (Immediate on consumption)", 6, 4, 0),
        ("Timing %4==2 (Late phase)", 6, 4, 2),
    ]
    
    results = []
    for name, mb, wb, tm in configs:
        res = evaluate_livestock_config(name, mb, wb, tm, seeds)
        results.append(res)
        print(f"{name:<38} | Delta vs V2: {res['mean_delta_vs_v2']:+,.2f} | Worst: {res['worst_delta']:+,.0f} | Best: {res['best_delta']:+,.0f}")
        
    out_path = os.path.join(BASE_DIR, "scratch", "livestock_frontier_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved livestock results to {out_path}")

if __name__ == "__main__":
    run_livestock_benchmark()
