# SPDX-License-Identifier: MIT
"""Populates search_cache.json with transposition state signatures."""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v34_a7_tactical.search_research.beam_search import (
    BeamSearchEngine, StateSignatureHasher, SEARCH_CACHE_PATH
)
from kaggle_environments import make

def main():
    engine = BeamSearchEngine(cache_file=SEARCH_CACHE_PATH)
    env = make("kaggriculture", configuration={"seed": 249675, "episodeSteps": 50})
    env.reset()
    
    # Harvest some initial states
    for step_idx in range(10):
        obs = env.steps[-1][0]["observation"]
        cands = [
            {"farmer": ["PASS"], "hands": [], "market": []},
            {"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]]},
            {"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]},
        ]
        best_act, score = engine.search_best_action(obs, cands, player=0)
        env.step([best_act, {"farmer": ["PASS"], "hands": [], "market": []}])
    
    engine.save_cache()
    print(f"search_cache.json populated with {len(engine.cache)} cached transposition signatures at {SEARCH_CACHE_PATH}")

if __name__ == "__main__":
    main()
