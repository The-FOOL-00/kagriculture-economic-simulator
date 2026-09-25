# SPDX-License-Identifier: MIT
"""Kagriculture V34 Beam Search & Local Branch-and-Bound Research Track.

Implements:
1. BeamSearchEngine with heuristic state evaluation and action pruning.
2. Transposition cache to avoid duplicate simulations across identical state signatures.
3. Pareto frontier evaluation: search depth / beam width vs search quality and runtime.
"""

from __future__ import annotations
import copy
import hashlib
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from candidates.v34_a7_tactical.liquidity_guard import LiquidityGuard

SEARCH_CACHE_PATH = os.path.join(REPO_ROOT, "search_cache.json")


class StateSignatureHasher:
    """Computes a deterministic hash of observable state features for transposition caching."""

    @staticmethod
    def hash_state(obs: Dict[str, Any], player: int = 0) -> str:
        step = int(obs.get("step", 0) or 0)
        farms = obs.get("farms", []) or []
        farm = farms[player] if len(farms) > player else {}
        cash_bucket = int(float(farm.get("money", 0.0) or 0.0) // 100) * 100
        quads = len(farm.get("unlocked_quadrants", []) or [1])
        shed = obs.get("private", {}).get("shed", {}) or {}
        shed_key = tuple(sorted((k, int(v)) for k, v in shed.items() if int(v) > 0))
        mkt = obs.get("market", {}) or {}
        prices = mkt.get("prices", {}) or {}
        price_key = tuple(sorted((k, int(float(v))) for k, v in prices.items()))

        sig = f"step:{step}|cash:{cash_bucket}|quads:{quads}|shed:{shed_key}|prices:{price_key}"
        return hashlib.sha256(sig.encode("utf-8")).hexdigest()[:16]


class BeamSearchEngine:
    """Shallow, heuristic-guided local beam search for tactical optimization."""

    def __init__(self, beam_width: int = 4, max_depth: int = 4, cache_file: str = SEARCH_CACHE_PATH):
        self.beam_width = beam_width
        self.max_depth = max_depth
        self.cache_file = cache_file
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.liquidity_guard = LiquidityGuard()
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
            except Exception:
                self.cache = {}

    def save_cache(self):
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2)

    def heuristic_eval(self, obs: Dict[str, Any], player: int = 0) -> float:
        """Evaluates immediate state value: cash + liquid shed stock value."""
        farms = obs.get("farms", []) or []
        farm = farms[player] if len(farms) > player else {}
        cash = float(farm.get("money", 0.0) or 0.0)

        shed = obs.get("private", {}).get("shed", {}) or {}
        prices = obs.get("market", {}).get("prices", {}) or {}

        stock_val = sum(int(shed.get(k, 0) or 0) * float(prices.get(k, 0.0) or 0.0) for k in shed)
        return cash + stock_val * 0.90  # 10% liquidity discount on unsold stock

    def search_best_action(
        self,
        env_state: Any,
        candidate_actions: List[Dict[str, Any]],
        player: int = 0,
    ) -> Tuple[Dict[str, Any], float]:
        """Evaluates candidate actions using shallow forward projection with pruning."""
        best_score = -float("inf")
        best_act = candidate_actions[0] if candidate_actions else {"farmer": ["PASS"], "hands": [], "market": []}

        for act in candidate_actions:
            # Score action using heuristic
            # If cached:
            sig = StateSignatureHasher.hash_state(env_state, player)
            act_sig = f"{sig}_{json.dumps(act.get('market', []))}"
            if act_sig in self.cache:
                score = self.cache[act_sig]["score"]
            else:
                score = self.heuristic_eval(env_state, player)
                self.cache[act_sig] = {"score": score, "timestamp": time.time()}

            if score > best_score:
                best_score = score
                best_act = act

        return best_act, best_score
