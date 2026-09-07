"""
Phase 10: Causal Ablation Experiments.
Evaluates 5 variants across 5 matched seeds:
Variant A: Frozen V2 Baseline
Variant B: Proposed Candidate (Full CL-Aethel Prime)
Variant C: Macro Improvement Removed (flat market orders, no dynamic strawberry/melon scaling)
Variant D: Micro Improvement Removed (no local-first execution, greedy remote routing)
Variant E: Economic Allocation Removed (no Day 0 Melon opening, naive opening)
"""

import sys, os, copy
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_cl_aethel_prime import agent as prime_agent, CLAethelPrime

pass_ag = lambda obs, cfg=None: {}

# Build Ablation C: Macro Improvement Removed
class AblationC(CLAethelPrime):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        # Reverse market orders or do not prioritize sells
        return [o for o in orders if o[0] != 'SELL'] + [o for o in orders if o[0] == 'SELL']

# Build Ablation D: Micro Improvement Removed (No Local-First Execution)
class AblationD(CLAethelPrime):
    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res):
        # Skip Step 1 (Local-First Execution) and go straight to Step 2 (Remote routing)
        actions = [None] * len(all_workers)
        claimed_tiles = set()
        ns = (4, 4)
        target_pasture_slots = scan_res.get("target_pasture_slots", set())
        
        # Directly do remote routing without clearing tile underneath worker
        n_workers = len(all_workers)
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            target = None
            if scan_res.get("hungry"):
                cands = [h for h in scan_res["hungry"] if h not in claimed_tiles]
                if cands: target = cands[0]
            elif scan_res.get("unwatered"):
                cands = [u for u in scan_res["unwatered"] if u not in claimed_tiles]
                if cands: target = cands[0]
            if target and target != pos:
                claimed_tiles.add(target)
                from candidates.candidate_cl_aethel_prime import _bfs
                actions[i] = [_bfs(pos, target, tiles)]
            else:
                actions[i] = ["PASS"]
        return actions

# Build Ablation E: Economic Allocation Removed (No Day 0 Melons)
class AblationE(CLAethelPrime):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        if step == 0:
            return [
                ["BUY_ANIMAL", "COW", 2],
                ["BUY_SEED", "WHEAT", 20],
                ["BUY_PRODUCT", "WHEAT", 10],
                ["HIRE"], ["HIRE"]
            ]
        return super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)

inst_c = AblationC()
inst_d = AblationD()
inst_e = AblationE()

def run_causal_experiments():
    print("=" * 80)
    print("PHASE 10: CAUSAL ABLATION EXPERIMENTS (MATCHED SEEDS)")
    print("=" * 80)
    
    seeds = [42, 100, 2026]
    variants = [
        ("A (Frozen V2 Baseline)", v2_agent),
        ("B (Proposed Candidate)", prime_agent),
        ("C (Macro Removed)", inst_c),
        ("D (Micro Removed)", inst_d),
        ("E (Day 0 Economy Removed)", inst_e),
    ]
    
    results = {name: [] for name, _ in variants}
    
    for s in seeds:
        print(f"\n--- Running Matched Seed {s} ---")
        for name, ag in variants:
            env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
            env.run([ag, pass_ag])
            r = env.state[0].reward
            results[name].append(r)
            print(f"  {name:28s}: ${r:,.1f}")
            
    print("\n" + "=" * 80)
    print("PHASE 10 SUMMARY: CAUSAL DRIVER ANALYSIS")
    print("=" * 80)
    print(f"{'Variant':28s} | {'Seed 42':10s} | {'Seed 100':10s} | {'Seed 2026':10s} | {'Mean Reward':12s}")
    print("-" * 80)
    for name, r_list in results.items():
        m = sum(r_list) / len(r_list)
        print(f"{name:28s} | ${r_list[0]:9,.1f} | ${r_list[1]:9,.1f} | ${r_list[2]:9,.1f} | ${m:11,.1f}")
        
    print("\nCausal Insights:")
    print(f"  1. Micro Scheduler Contribution (B vs D): ${sum(results['B (Proposed Candidate)'])/3 - sum(results['D (Micro Removed)'])/3:+,.1f}")
    print(f"  2. Day 0 Economic Pipeline (B vs E):      ${sum(results['B (Proposed Candidate)'])/3 - sum(results['E (Day 0 Economy Removed)'])/3:+,.1f}")
    print(f"  3. Macro Market Ordering (B vs C):        ${sum(results['B (Proposed Candidate)'])/3 - sum(results['C (Macro Removed)'])/3:+,.1f}")

if __name__ == "__main__":
    run_causal_experiments()
