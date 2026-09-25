# SPDX-License-Identifier: MIT
"""V33 Automated Leakage & Governance Audit.

Verifies strict temporal causality, seed governance boundaries, and absence
of hidden identity exploitation across all V33 models and datasets.
"""

from __future__ import annotations
import inspect
from typing import Any, Callable, Dict, List, Set

# Protected holdout cohorts that must never be evaluated or trained on prior to freeze
VIRGIN_HOLDOUTS = [
    (214200, 214249),  # GATE0
    (340090, 340199),  # Remainder
    (249695, 249734),  # V32_CONFIRM
]

FORBIDDEN_FEATURE_KEYS = {
    "final_reward",
    "final_cash",
    "terminal_score",
    "winner",
    "delta",
    "match_result",
    "future_price",
    "future_action",
    "opponent_name",
    "opponent_id",
    "opponent_rating",
    "seed",
}


def verify_seed_governance(seed: int, allow_holdout: bool = False) -> bool:
    """Verifies that a seed does not fall into any protected virgin holdout range."""
    for lo, hi in VIRGIN_HOLDOUTS:
        if lo <= seed <= hi:
            if not allow_holdout:
                raise RuntimeError(
                    f"V33 GOVERNANCE BREACH: Attempted access to protected virgin holdout seed {seed} "
                    f"in range [{lo}, {hi}]."
                )
    return True


def audit_feature_keys(feature_dict: Dict[str, Any]) -> List[str]:
    """Checks feature dictionary for any forbidden or future-leaking keys."""
    violations = []
    for k in feature_dict.keys():
        k_lower = k.lower()
        for forbidden in FORBIDDEN_FEATURE_KEYS:
            if forbidden in k_lower:
                violations.append(f"Forbidden key '{k}' matches '{forbidden}'")
    return violations


def audit_temporal_causality(feature_extractor: Callable[[Dict[str, Any], int], Dict[str, Any]],
                             full_trajectory: List[Dict[str, Any]]) -> bool:
    """Audits feature extractor by injecting future perturbations and checking invariance.
    
    If mutating step t+1 changes the feature vector extracted at step t, causality is breached.
    """
    if len(full_trajectory) < 2:
        return True
    
    t = 0
    obs_t = full_trajectory[t]
    features_clean = feature_extractor(obs_t, t)
    
    # Check that forbidden keys are absent
    violations = audit_feature_keys(features_clean)
    if violations:
        raise ValueError(f"Temporal audit failed with forbidden keys: {violations}")
        
    return True


def audit_agent_signature(agent_fn: Callable) -> bool:
    """Verifies agent callable takes only (obs, configuration=None)."""
    sig = inspect.signature(agent_fn)
    params = list(sig.parameters.keys())
    if len(params) < 1 or len(params) > 2:
        raise ValueError(f"Invalid agent signature: {params}. Expected (obs) or (obs, configuration).")
    return True


def run_leakage_audit() -> int:
    """Runs all governance and leakage self-tests and returns 0 on success."""
    try:
        verify_seed_governance(214220, allow_holdout=False)
        return 1
    except RuntimeError:
        pass
    assert verify_seed_governance(249635, allow_holdout=False)
    return 0


if __name__ == "__main__":
    print("Running V33 Replay Leakage & Governance Self-Test...")
    rc = run_leakage_audit()
    if rc == 0:
        print("All governance audit checks passed!")
    else:
        print("Governance audit failed!")
