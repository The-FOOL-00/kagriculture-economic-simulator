# SPDX-License-Identifier: MIT
"""Kagriculture V32 RL-X2 Opponent League Loader & Sampler.

Loads frozen opponents without cross-match state contamination and provides
league sampling distributions for self-play / league training.
"""

from __future__ import annotations
import os
import sys
import uuid
from typing import Any, Callable, Dict, List, Optional
import numpy as np

try:
    from rlx2_config import REPO_ROOT
except ImportError:
    from candidates.v32_rlx2.rlx2_config import REPO_ROOT

sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from scripts.v32_common import load_agent, PassiveAgent


def _synthetic_aggressive(obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Hostile market dumper that sells inventory rapidly to suppress prices."""
    private = obs.get("private", {}) or {}
    shed = private.get("shed", {}) or {}
    orders = []
    for prod in ["MILK", "WOOL", "MELON", "STRAWBERRY", "WHEAT"]:
        qty = shed.get(prod, 0)
        if qty > 0:
            orders.append(["SELL", prod, min(qty, 30)])
    orders = orders[:10]
    farms = obs.get("farms", [])
    player = obs.get("player", 0)
    farm = farms[player] if farms and player < len(farms) else {}
    hands_n = len(farm.get("hands", []) or [])
    return {
        "market": orders,
        "farmer": ["PASS"],
        "hands": [["PASS"] for _ in range(hands_n)]
    }


def load_league_opponent(opponent_id: str) -> Callable[[Dict[str, Any], Optional[Dict[str, Any]]], Dict[str, Any]]:
    """Loads an opponent callable by ID."""
    if opponent_id == "SYN_AGG":
        return _synthetic_aggressive
    elif opponent_id == "V54":
        v54_path = os.path.join(REPO_ROOT, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4", "main.py")
        if not os.path.exists(v54_path):
            v54_path = os.path.join(REPO_ROOT, "candidates", "cms5_v54_faithful.py")
        with open(v54_path, "r", encoding="utf-8") as f:
            code = f.read()
        ns = {"__name__": f"v54_iso_{uuid.uuid4().hex[:8]}"}
        exec(compile(code, v54_path, "exec"), ns)
        fn = ns.get("agent")
        return lambda o, c=None: fn(o, c) if callable(fn) else {"farmer": ["PASS"], "hands": [], "market": []}
    elif opponent_id in ("E2_A7", "A7"):
        a7 = load_agent("E9_AST")
        return lambda o, c=None: a7.act(o, c)
    elif opponent_id == "PASSIVE":
        pas = PassiveAgent()
        return lambda o, c=None: pas.act(o, c)
    else:
        opp = load_agent(opponent_id)
        return lambda o, c=None: opp.act(o, c)


LEAGUE_OPPONENTS: List[str] = [
    "E2_A7",       # Incumbent benchmark
    "E1_V22R1",    # Slot A portfolio champion
    "E0_V3",       # Frozen base
    "E8_DMITRII",  # Frontier competitor (2800+ LB)
    "V54",         # Declarative reference
    "SYN_AGG",     # Hostile market stressor
]


class OpponentSampler:
    """Manages opponent sampling distributions during training."""
    def __init__(self, mode: str = "uniform"):
        self.mode = mode
        self.opponents = list(LEAGUE_OPPONENTS)
        
    def sample(self) -> str:
        if self.mode == "uniform":
            return np.random.choice(self.opponents)
        elif self.mode == "hard_weighted":
            # 40% Dmitrii, 20% A7, 20% V22R1, 10% V54, 10% SYN_AGG
            weights = [0.20, 0.20, 0.05, 0.35, 0.10, 0.10]
            return np.random.choice(self.opponents, p=weights)
        elif self.mode == "a7_only":
            return "E2_A7"
        elif self.mode == "dmitrii_only":
            return "E8_DMITRII"
        return "E2_A7"
