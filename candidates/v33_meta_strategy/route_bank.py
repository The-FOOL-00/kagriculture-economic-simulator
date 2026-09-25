# SPDX-License-Identifier: MIT
"""V33 Elite Route Bank.

Defines the core portfolio of 6 expert routes for V33 meta-strategy routing.
Each expert is an autonomous, closed-loop or coordinated policy that handles
low-level farming execution end-to-end.
"""

from __future__ import annotations
import copy
import os
import sys
import uuid
from typing import Any, Callable, Dict, List, Optional

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.v32_common import load_agent
from candidates.v32_rlx2.opponents import load_league_opponent


def load_p3090_agent() -> Callable[[Dict[str, Any], Optional[Dict[str, Any]]], Dict[str, Any]]:
    """Loads the public 3090 agent in an isolated namespace."""
    p3090_path = os.path.join(
        REPO_ROOT, "external_repos", "lixingtao123-Kaggriculture", "public_3090", "output", "main.py"
    )
    ns: Dict[str, Any] = {"__name__": f"p3090_{uuid.uuid4().hex[:8]}"}
    with open(p3090_path, "r", encoding="utf-8") as f:
        code = f.read()
    exec(compile(code, p3090_path, "exec"), ns)
    fn = ns["agent"]
    return lambda o, c=None: fn(o, c)


ROUTE_METADATA: Dict[str, Dict[str, Any]] = {
    "R0_A7": {
        "route_id": "R0_A7",
        "name": "A7 Protected Incumbent",
        "source": "candidates/v30_a7_standalone/main.py",
        "archetype": "High-Efficiency Choreography",
        "strategic_phases": ["HIRE4 Opening", "Single-Quad Crop Expansion", "Strict Cash Buffer", "Terminal Liquidation"],
        "phase_boundaries": [0, 48, 480, 680],
        "compatibility_assumptions": "Requires full control from t=0. Does not tolerate midgame capital siphoning.",
        "observed_strengths": "World-class execution efficiency (~$104k baseline mean), excellent weed immunity, high terminal cash.",
        "observed_weaknesses": "Inflexible land capex, cannot adapt to opponent market supply surges.",
        "benchmark_mean_cash": 104332.17,
        "provenance": "V30 championship submission, Slot B protected incumbent.",
        "status": "DEFAULT_EXPERT"
    },
    "R1_V22R1": {
        "route_id": "R1_V22R1",
        "name": "V22R1 Slot A Champion",
        "source": "submission_aec_v22r1.tar.gz",
        "archetype": "Adaptive Multi-Regime",
        "strategic_phases": ["Early Investment", "Dynamic Rebalancing", "Market Preemption", "Controlled Liquidation"],
        "phase_boundaries": [0, 72, 360, 650],
        "compatibility_assumptions": "Highly resilient to midgame perturbations, handles multi-quadrant farming.",
        "observed_strengths": "Superior win rate against mid-tier agro competitors, intelligent price impact preemption.",
        "observed_weaknesses": "Slightly lower peak cash than A7 in unshared markets.",
        "benchmark_mean_cash": 94315.00,
        "provenance": "Slot A frozen champion.",
        "status": "PORTFOLIO_EXPERT"
    },
    "R2_DMITRII": {
        "route_id": "R2_DMITRII",
        "name": "Dmitrii LB2800 Frontier",
        "source": "extracted_agents/dmitrii_lb2800/main.py",
        "archetype": "Pure Livestock Specialist",
        "strategic_phases": ["Rapid Coop/Pasture Build", "Animal Stocking", "Milk/Wool Continuous Sell", "Terminal Slump Avoidance"],
        "phase_boundaries": [0, 60, 240, 640],
        "compatibility_assumptions": "Focuses heavily on animals; does not use bakery wheat supply.",
        "observed_strengths": "Dominates when opponents saturate crop markets; zero vulnerability to bakery wheat price collapse.",
        "observed_weaknesses": "Vulnerable to high starting animal costs if cash flow is disrupted.",
        "benchmark_mean_cash": 85002.30,
        "provenance": "Decompiled 2800+ LB frontier benchmark.",
        "status": "PORTFOLIO_EXPERT"
    },
    "R3_P3090": {
        "route_id": "R3_P3090",
        "name": "Public 3090 Top Replay Fit",
        "source": "external_repos/lixingtao123-Kaggriculture/public_3090/output/main.py",
        "archetype": "Fit-Optimized Fast Tape",
        "strategic_phases": ["HIRE4 Opening", "Weed Repair Loop", "Town-Demand Sell Ranking", "Clean Liquidation"],
        "phase_boundaries": [0, 48, 300, 670],
        "compatibility_assumptions": "Dual-regime action tape adapted to town center sell interval.",
        "observed_strengths": "Very high raw score on historical replays ($75k-$96k), low latency, deterministic.",
        "observed_weaknesses": "Lacks dynamic closed-loop replanning if opponent steals public orders.",
        "benchmark_mean_cash": 73170.00,
        "provenance": "Public 3090 notebook.",
        "status": "PORTFOLIO_EXPERT"
    },
    "R4_V54": {
        "route_id": "R4_V54",
        "name": "Variant V54 Faithful",
        "source": "candidates/cms5_v54_faithful.py",
        "archetype": "Commercial Crop Flood",
        "strategic_phases": ["Multi-Land Expansion", "High-Volume Crop Sowing", "Harvest Coordination", "Bulk Sell Dumps"],
        "phase_boundaries": [0, 96, 384, 660],
        "compatibility_assumptions": "Requires unlocking 3+ quadrants; demands high seed inventory buffer.",
        "observed_strengths": "Extremely high yield volume, overwhelms passive or slow-expanding competitors.",
        "observed_weaknesses": "Suffers severe revenue contraction if opponent also dumps wheat/carrots.",
        "benchmark_mean_cash": 98854.70,
        "provenance": "Declarative multi-quadrant farming research.",
        "status": "PORTFOLIO_EXPERT"
    },
    "R5_V25P3": {
        "route_id": "R5_V25P3",
        "name": "V25 Unified Macro Backbone",
        "source": "candidates/v25_p3_unified.py",
        "archetype": "Fixed Balanced Zoning",
        "strategic_phases": ["Zoning Initialization", "Labor Scaling", "Mixed Production", "Terminal Harvest"],
        "phase_boundaries": [0, 48, 360, 680],
        "compatibility_assumptions": "Enforces strict quadrant zoning (crops vs pastures).",
        "observed_strengths": "Balanced risk profile, stable midgame cash buffer.",
        "observed_weaknesses": "Lower terminal ceiling than specialized monocultures.",
        "benchmark_mean_cash": 88000.00,
        "provenance": "V25 unified macro backbone.",
        "status": "PORTFOLIO_EXPERT"
    }
}


class RouteBank:
    """Manages instantiation and access to the 6 elite expert routes."""
    def __init__(self):
        self._loaders: Dict[str, Callable] = {
            "R0_A7": lambda: load_league_opponent("E2_A7"),
            "R1_V22R1": lambda: load_league_opponent("E1_V22R1"),
            "R2_DMITRII": lambda: load_league_opponent("E8_DMITRII"),
            "R3_P3090": load_p3090_agent,
            "R4_V54": lambda: load_league_opponent("V54"),
            "R5_V25P3": lambda: load_league_opponent("E3_V25P3"),
        }

    def list_routes(self) -> List[str]:
        return list(self._loaders.keys())

    def get_metadata(self, route_id: str) -> Dict[str, Any]:
        return copy.deepcopy(ROUTE_METADATA.get(route_id, {}))

    def load_route(self, route_id: str) -> Callable[[Dict[str, Any], Optional[Dict[str, Any]]], Dict[str, Any]]:
        if route_id not in self._loaders:
            raise KeyError(f"Unknown route_id '{route_id}'. Available: {list(self._loaders.keys())}")
        return self._loaders[route_id]()


if __name__ == "__main__":
    bank = RouteBank()
    print("Testing RouteBank initialization...")
    for rid in bank.list_routes():
        agent_fn = bank.load_route(rid)
        meta = bank.get_metadata(rid)
        print(f"Loaded {rid}: {meta['name']} ({meta['archetype']})")
    print("RouteBank verified successfully!")
