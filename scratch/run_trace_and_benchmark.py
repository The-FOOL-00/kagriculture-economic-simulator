import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import time
import statistics
from typing import Any, Dict, List

from aec.counterfactual.simulator import CounterfactualSimulator
from aec.ir.economic_state import build_economic_state
from aec.patches.patch import CoupledPatch


def make_synthetic_obs(step: int = 0, shed: Dict[str, int] = None, cash: float = 3000.0) -> Dict[str, Any]:
    return {
        "step": step, "day": step // 24, "hour": step % 24, "player": 0,
        "farms": [
            {
                "money": cash, "farmer": [4, 4], "hands": [[3, 4]],
                "tiles": [[None]*10 for _ in range(10)],
                "unlocked_quadrants": ["NW"], "hires_today": 0
            },
            {
                "money": 3000.0, "farmer": [4, 4], "hands": [[3, 4]],
                "tiles": [[None]*10 for _ in range(10)],
                "unlocked_quadrants": ["NW"], "hires_today": 0
            }
        ],
        "private": {
            "shed": shed or {"STRAWBERRY": 50, "WHEAT": 20},
            "seeds": {"STRAWBERRY": 10},
            "inventories": [{}, {}]
        },
        "market": {
            "prices": {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100},
            "inventory": {"WHEAT": 10000, "CARROT": 10000, "TOMATO": 10000, "STRAWBERRY": 10000, "MELON": 10000, "EGG": 10000, "MILK": 10000, "WOOL": 10000, "FERTILIZER": 10000}
        },
        "town": {"unlocked_shops": ["YARN_STORE", "BAKERY"]}
    }


def print_trace_summary(title: str, trace: List[Dict[str, Any]]) -> None:
    print(f"\n=======================================================")
    print(f"TRACE: {title} (H={len(trace)})")
    print(f"=======================================================")
    for t in trace:
        offset = t["offset"]
        step = t["step"]
        farmer_pos = t["worker_positions"][0]
        hand_pos = t["worker_positions"][1] if len(t["worker_positions"]) > 1 else "None"
        farmer_act = t["worker_actions"][0]
        hand_act = t["worker_actions"][1] if len(t["worker_actions"]) > 1 else "None"
        cash = t["cash"]
        shed = {k: v for k, v in t["shed"].items() if v > 0}
        straw_price = t["market_prices"].get("STRAWBERRY", 0)
        straw_inv = t["market_inventory"].get("STRAWBERRY", 0)
        straw_pressure = t["opponent_pressure"].get("STRAWBERRY", 0.0)
        print(f"t{offset} (step={step}):")
        print(f"  farmer={farmer_pos} act={farmer_act} | hand={hand_pos} act={hand_act}")
        print(f"  cash={cash:.1f} | shed={shed}")
        print(f"  market[STRAWBERRY]: price={straw_price} inv={straw_inv} opp_pressure={straw_pressure:.2f}")


def run_synthetic_traces() -> None:
    simulator = CounterfactualSimulator()

    # ----------------------------------------------------
    # TRACE A: Worker Route Continuation (H=6)
    # ----------------------------------------------------
    obs_a = make_synthetic_obs(step=48)
    state_a = build_economic_state(obs_a)
    init_act_a = {"farmer": ["SOUTH"], "hands": [["EAST"]], "market": []}
    continuation_a = [
        {"farmer": ["SOUTH"], "hands": [["EAST"]], "market": []},
        {"farmer": ["EAST"], "hands": [["NORTH"]], "market": []},
        {"farmer": ["EAST"], "hands": [["NORTH"]], "market": []},
        {"farmer": ["NORTH"], "hands": [["WEST"]], "market": []},
        {"farmer": ["NORTH"], "hands": [["WEST"]], "market": []},
    ]
    patch_a = CoupledPatch(
        patch_id="P_TRACE_A",
        source_opportunity_id="OPP_A",
        worker_mutations={0: ["SOUTH"]},
        expected_horizon=6
    )
    outcome_a = simulator.evaluate(patch_a, init_act_a, state_a, horizon=6, continuation_trajectory=continuation_a, trace=True)
    print_trace_summary("A. Worker Route Continuation", outcome_a.baseline_trace)

    # ----------------------------------------------------
    # TRACE B: Market Continuation (H=6)
    # ----------------------------------------------------
    obs_b = make_synthetic_obs(step=96, shed={"STRAWBERRY": 60, "WHEAT": 10})
    state_b = build_economic_state(obs_b)
    init_act_b = {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 10]]}
    continuation_b = [
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 10]]},
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 10]]},
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 10]]},
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 10]]},
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 10]]},
    ]
    patch_b = CoupledPatch(
        patch_id="P_TRACE_B",
        source_opportunity_id="OPP_B",
        market_mutations=[["SELL", "STRAWBERRY", 10]],
        expected_horizon=6
    )
    outcome_b = simulator.evaluate(patch_b, init_act_b, state_b, horizon=6, continuation_trajectory=continuation_b, trace=True)
    print_trace_summary("B. Market Continuation", outcome_b.candidate_trace)

    # ----------------------------------------------------
    # TRACE C: Terminal-Near Continuation (H=6 requested at step 717)
    # ----------------------------------------------------
    obs_c = make_synthetic_obs(step=717, shed={"STRAWBERRY": 30}, cash=12000.0)
    state_c = build_economic_state(obs_c)
    init_act_c = {"farmer": ["SOUTH"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 10]]}
    continuation_c = [
        {"farmer": ["EAST"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 10]]},
        {"farmer": ["EAST"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 10]]},
        {"farmer": ["NORTH"], "hands": [["PASS"]], "market": []},
        {"farmer": ["NORTH"], "hands": [["PASS"]], "market": []},
        {"farmer": ["WEST"], "hands": [["PASS"]], "market": []},
    ]
    patch_c = CoupledPatch(
        patch_id="P_TRACE_C",
        source_opportunity_id="OPP_C",
        market_mutations=[["SELL", "STRAWBERRY", 10]],
        expected_horizon=6
    )
    outcome_c = simulator.evaluate(patch_c, init_act_c, state_c, horizon=6, continuation_trajectory=continuation_c, trace=True)
    print_trace_summary("C. Terminal-Near Boundary Clamping (Step 717)", outcome_c.candidate_trace)


def run_runtime_benchmarks() -> None:
    simulator = CounterfactualSimulator()
    obs = make_synthetic_obs(step=100)
    state = build_economic_state(obs)
    base_act = {"farmer": ["SOUTH"], "hands": [["EAST"]], "market": [["SELL", "STRAWBERRY", 5]]}
    patch = CoupledPatch(
        patch_id="P_BENCH",
        source_opportunity_id="OPP_BENCH",
        market_mutations=[["SELL", "STRAWBERRY", 5]],
        expected_horizon=36
    )

    print("\n=======================================================")
    print("RUNTIME BENCHMARK (Evaluations of baseline + candidate)")
    print("=======================================================")

    horizons = [1, 6, 18, 36]
    n_iters = 100

    for h in horizons:
        continuation = [
            {"farmer": ["SOUTH"], "hands": [["EAST"]], "market": [["SELL", "STRAWBERRY", 1]]}
            for _ in range(h - 1)
        ]
        
        # Warmup
        for _ in range(5):
            simulator.evaluate(patch, base_act, state, horizon=h, continuation_trajectory=continuation)

        times_ms = []
        for _ in range(n_iters):
            t0 = time.perf_counter()
            simulator.evaluate(patch, base_act, state, horizon=h, continuation_trajectory=continuation)
            t1 = time.perf_counter()
            times_ms.append((t1 - t0) * 1000.0)

        mean_ms = statistics.mean(times_ms)
        max_ms = max(times_ms)
        total_steps = h * 2  # Baseline rollout + Candidate rollout

        print(f"H={h:2d} | steps={total_steps:2d} | mean={mean_ms:.3f} ms | max={max_ms:.3f} ms | per-step={mean_ms/total_steps:.4f} ms")


if __name__ == "__main__":
    run_synthetic_traces()
    run_runtime_benchmarks()
