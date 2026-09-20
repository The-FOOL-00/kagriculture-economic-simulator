# SPDX-License-Identifier: MIT
"""Phase 022R1: safety-predicate audit tests (§15).

Characterizes the REAL safety behavior (no policy changes):
- unsafe candidates are rejected by evaluated predicates (fail-closed);
- purchase_ok (predicate 1) is an unevaluated placeholder key: absent from
  SafetyChecker.verify, defaulting to True in the certificate; purchase
  affordability itself IS enforced elsewhere (solvency/cash-liquidity);
- market_collision_ok (predicate 2) is an unevaluated placeholder: present but
  never flipped to False; duplicate orders pass it. Novel collisions are
  unreachable under the qualified config because the timing transform emits a
  sub-multiset (pure reorder, count/item preserving) of V3's own basket;
- safe candidates pass; executor falls back to baseline/PASS on failures.
"""

import pytest

from aec.config import MAX_MARKET_ORDERS
from aec.counterfactual.simulator import SimulationOutcome
from aec.integration.backbone_adapter import BackboneAdapter
from aec.integration.executor import AECExecutor
from aec.ir import build_economic_state
from aec.market.transformations import transform_dependency_aware_market_timing
from aec.patches import CoupledPatch
from aec.safety import SafetyChecker

BASELINE = {"farmer": ["PASS"], "hands": [], "market": []}


def _outcome(**kw):
    d = dict(
        candidate_final_money=6000.0, baseline_final_money=5000.0,
        delta_our_money=1000.0, candidate_opp_final_money=5000.0,
        baseline_opp_final_money=5000.0, delta_opponent_money=0.0,
        delta_terminal_margin=1000.0, candidate_overflow_units=0,
        candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=True, horizon=2,
    )
    d.update(kw)
    return SimulationOutcome(**d)


def _state(obs):
    return build_economic_state(obs)


def test_unsafe_candidates_rejected_by_evaluated_predicates(normal_opening_obs):
    st = _state(normal_opening_obs)
    ck = SafetyChecker()

    # 1. Shed overflow in continuation.
    p = CoupledPatch(patch_id="U1", source_opportunity_id="O",
                     market_mutations=[["SELL", "WHEAT", 5]])
    passed, checks, reason = ck.verify(p, _outcome(candidate_overflow_units=5), st, BASELINE)
    assert passed is False and checks["overflow_ok"] is False and reason

    # 2. Negative terminal cash.
    passed, checks, reason = ck.verify(p, _outcome(candidate_final_money=-50.0), st, BASELINE)
    assert passed is False and checks["solvency_ok"] is False and reason

    # 3. Illegal market op.
    p_bad = CoupledPatch(patch_id="U3", source_opportunity_id="O",
                         market_mutations=[["STEAL", "WHEAT", 5]])
    passed, checks, reason = ck.verify(p_bad, _outcome(), st, BASELINE)
    assert passed is False and checks["legality_ok"] is False and reason

    # 4. Oversized basket.
    p_big = CoupledPatch(patch_id="U4", source_opportunity_id="O",
                         market_mutations=[["SELL", "WHEAT", 1]] * (MAX_MARKET_ORDERS + 1))
    passed, checks, reason = ck.verify(p_big, _outcome(), st, BASELINE)
    assert passed is False and checks["legality_ok"] is False and reason

    # 5. Failed counterfactual fidelity.
    passed, checks, reason = ck.verify(p, _outcome(fidelity="FAILED"), st, BASELINE)
    assert passed is False and checks["fidelity_ok"] is False and reason


def test_predicate1_purchase_ok_unevaluated_but_affordability_enforced(normal_opening_obs):
    """purchase_ok is absent from verify(); affordability enforced via solvency."""
    st = _state(normal_opening_obs)
    ck = SafetyChecker()
    safe = CoupledPatch(patch_id="S", source_opportunity_id="O",
                        market_mutations=[["SELL", "WHEAT", 5]])
    passed, checks, _ = ck.verify(safe, _outcome(), st, BASELINE)
    assert passed is True
    assert "purchase_ok" not in checks  # placeholder: executor .get() defaults True

    # An unaffordable purchase IS rejected — by solvency/cash-liquidity instead.
    poor = CoupledPatch(patch_id="P", source_opportunity_id="O",
                        market_mutations=[["BUY_ANIMAL", "COW", 50]])
    passed, checks, reason = ck.verify(poor, _outcome(candidate_final_money=-100.0), st, BASELINE)
    assert passed is False
    assert checks["solvency_ok"] is False and checks["cash_liquidity_ok"] is False
    assert reason


def test_predicate2_market_collision_ok_unevaluated_placeholder(normal_opening_obs):
    """market_collision_ok never flips; duplicate orders pass it (documented)."""
    st = _state(normal_opening_obs)
    ck = SafetyChecker()
    dup = CoupledPatch(patch_id="D", source_opportunity_id="O",
                       market_mutations=[["SELL", "WHEAT", 30], ["SELL", "WHEAT", 30]])
    passed, checks, reason = ck.verify(dup, _outcome(), st, BASELINE)
    assert "market_collision_ok" in checks
    assert checks["market_collision_ok"] is True  # never evaluated to False
    assert passed is True and reason is None  # fail-open for this class, structurally
    # ...but novel collisions are unreachable: the timing transform only reorders.
    orders = [["SELL", "WHEAT", 30], ["BUY_PRODUCT", "EGG", 5], ["HIRE", "", 1],
              ["SELL", "MELON", 2], ["BUY_SEED", "WHEAT", 4]]
    reordered, _ = transform_dependency_aware_market_timing(orders)
    assert sorted(map(str, reordered)) == sorted(map(str, orders))  # pure permutation


def test_safe_candidate_passes(normal_opening_obs):
    st = _state(normal_opening_obs)
    ck = SafetyChecker()
    safe = CoupledPatch(patch_id="S", source_opportunity_id="O",
                        market_mutations=[["SELL", "WHEAT", 5]])
    passed, checks, reason = ck.verify(safe, _outcome(), st, BASELINE)
    assert passed is True and reason is None
    assert all(v is True for v in checks.values())


def test_fallback_backbone_failure_returns_safe_pass(normal_opening_obs):
    def boom(*a, **k):
        raise RuntimeError("V3 exploded")

    adapter = BackboneAdapter(agent_fn=boom)
    executor = AECExecutor(backbone_adapter=adapter)
    action = executor.act(dict(normal_opening_obs))
    assert action == {"farmer": ["PASS"], "hands": [], "market": []}
    assert executor.latest_telemetry.decision == "FAIL_SAFE"


def _load_consolidation_module():
    """Import the kagsim-bound consolidation script with a stubbed engine."""
    import sys
    import types
    from pathlib import Path

    if "kagsim" not in sys.modules:
        stub = types.ModuleType("kagsim")
        stub.Game = object
        sys.modules["kagsim"] = stub
    import importlib.util

    path = Path(__file__).resolve().parent.parent.parent / "scripts" / "run_phase022_consolidation.py"
    spec = importlib.util.spec_from_file_location("r1_consolidation_probe", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["r1_consolidation_probe"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_repaired_counter_measures_observable_safety_outcomes():
    """R1 counter: rejections counted; unsafe commits counted as violations."""
    from types import SimpleNamespace

    mod = _load_consolidation_module()
    hist = [
        SimpleNamespace(candidates=[
            SimpleNamespace(safety_pass=False, commit_decision=False,  # rejected, safe
                            safety_rejection_reason="Negative cash balance ($-5.00)"),
            SimpleNamespace(safety_pass=True, commit_decision=True,  # committed, safe
                            safety_rejection_reason=None),
        ]),
        SimpleNamespace(candidates=[
            SimpleNamespace(safety_pass=False, commit_decision=True,  # UNSAFE COMMIT
                            safety_rejection_reason="Candidate caused 3 units of shed overflow"),
        ]),
    ]
    violations, rejections = mod.count_safety_outcomes(hist)
    assert rejections == 2  # both safety_pass=False events observed
    assert violations == 1  # only the unsafe COMMIT is a violation
    # The V22 substring logic would have seen zero (no 'SAFETY_FAIL' anywhere).
    legacy = sum(1 for t in hist for c in t.candidates
                 if c.safety_rejection_reason and "SAFETY_FAIL" in c.safety_rejection_reason)
    assert legacy == 0


def test_fallback_aec_exception_returns_baseline(normal_opening_obs):
    base = {"farmer": ["PASS"], "hands": [], "market": [["SELL", "WHEAT", 1]]}
    adapter = BackboneAdapter(agent_fn=lambda o, c=None: dict(base))
    executor = AECExecutor(backbone_adapter=adapter)

    def faulty_detector(*a, **k):
        raise RuntimeError("injected optimizer crash")

    executor.event_bus.publish_many = faulty_detector
    action = executor.act(dict(normal_opening_obs))
    assert action == base
    assert executor.latest_telemetry.decision == "ABSTAIN_EXCEPTION"
