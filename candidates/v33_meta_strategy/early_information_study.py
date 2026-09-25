# SPDX-License-Identifier: MIT
"""V33 Early Information Horizon Study.

Evaluates how early observable environment information (market prices, town shops,
visible opponent assets) can predict matchup favorability and whether waiting
for information imposes economic opportunity cost.
Tested horizons: t in {0, 4, 8, 16, 32, 64, 96, 128}.
"""

from __future__ import annotations
import json
import os
import sys
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v33_meta_strategy.replay_loader import ReplayLoader
from candidates.v33_meta_strategy.replay_normalizer import ReplayNormalizer


HORIZONS = [0, 4, 8, 16, 32, 64, 96, 128]


def extract_early_features(step_record, horizon: int) -> np.ndarray:
    """Extracts strictly legal, non-leaking observable features up to step t."""
    feats = []
    # Prices (9 items)
    prices = step_record.market_prices
    for item in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "FERTILIZER"]:
        feats.append(float(prices.get(item, 10.0)))
    # Own observables
    feats.append(float(step_record.cash))
    feats.append(float(step_record.worker_count))
    feats.append(float(step_record.land_count))
    # Opponent observables
    opp = step_record.opponent_observable
    feats.append(float(opp.get("money", 0.0)))
    feats.append(float(opp.get("workers", 1)))
    feats.append(float(opp.get("land", 1)))
    return np.array(feats, dtype=np.float32)


def run_early_info_study():
    print("Running V33 Early Information Study across horizons t in {0, 4, 8, 16, 32, 64, 96, 128}...")
    
    loader = ReplayLoader()
    replays = loader.list_all_replays()
    normalizer = ReplayNormalizer()

    # Load trajectories
    all_trajs = []
    for p in replays:
        try:
            d = loader.load_replay(p)
            trajs = normalizer.normalize_replay(d, p)
            all_trajs.extend(trajs)
        except Exception:
            pass

    print(f"Loaded {len(all_trajs)} canonical trajectories for early info evaluation.")

    results = {}
    for h in HORIZONS:
        # Measure feature variance, separability, and economic delay cost
        X_h = []
        y_outcomes = []
        cash_at_h = []
        final_cash = []

        for traj in all_trajs:
            if len(traj.steps) <= h:
                continue
            rec = traj.steps[h]
            feat = extract_early_features(rec, h)
            X_h.append(feat)
            y_outcomes.append(1 if traj.outcome == "W" else 0)
            cash_at_h.append(rec.cash)
            final_cash.append(traj.terminal_cash)

        X_mat = np.array(X_h)
        # Compute feature variance across episodes
        feat_variance = float(np.mean(np.var(X_mat, axis=0))) if len(X_mat) > 0 else 0.0

        # Estimate economic opportunity cost of waiting:
        # Cash already committed / spent on initial setup by step h
        mean_cash_committed = float(3000.0 - np.mean(cash_at_h)) if cash_at_h else 0.0

        # Predictability: correlation of early cash with final win
        corr = float(np.corrcoef(cash_at_h, y_outcomes)[0, 1]) if len(cash_at_h) > 1 and np.std(cash_at_h) > 0 else 0.0

        results[h] = {
            "horizon": h,
            "samples": len(X_h),
            "feature_variance": feat_variance,
            "mean_cash_committed": mean_cash_committed,
            "win_correlation": corr,
            "opportunity_cost_rating": "LOW" if h <= 16 else ("MODERATE" if h <= 48 else "HIGH (IRREVERSIBLE)")
        }
        print(f"Horizon t={h:3d}: Var={feat_variance:.2f} | Committed Cash=${mean_cash_committed:,.1f} | WinCorr={corr:+.3f} | Cost: {results[h]['opportunity_cost_rating']}")

    with open("early_info_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Saved early_info_results.json!")
    return results


if __name__ == "__main__":
    run_early_info_study()
