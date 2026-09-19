# SPDX-License-Identifier: MIT
"""Phase 015: 40-Scenario Synthetic Functional Matrix Test Suite (§26).

Covers:
- Asset-Holding Valuation Trigger (20 Adversarial Cases)
- Autonomous Tranche Order Synthesizer (20 Adversarial Cases)
Total: 40 Scenarios.
"""

import copy
import pytest
from typing import Any, Dict

from aec.config import (
    AECConfig,
    PRODUCTS,
    build_phase015_treatment_config,
)
from aec.events.detectors import detect_events
from aec.events.event_types import EventType
from aec.ir.economic_state import build_economic_state
from aec.market.tranche_synthesizer import AutonomousTrancheOrderSynthesizer
from aec.opportunities.asset_holding import (
    AssetHoldingFingerprint,
    AssetHoldingOpportunityAnalyzer,
    AssetHoldingValuationTrigger,
    HoldingOpportunityType,
    OpportunityLifecycle,
    RealizationOption,
)


def _canonical_obs(
    step: int = 300,
    shed: Dict[str, int] = None,
    prices: Dict[str, int] = None,
    cash: float = 4000.0,
    animals: list = None,
    hands: list = None,
    cargo: Dict[str, int] = None,
) -> Dict[str, Any]:
    full_shed = {p: 0 for p in PRODUCTS}
    if shed:
        full_shed.update(shed)

    full_prices = {
        "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 100,
        "MELON": 200, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100
    }
    if prices:
        full_prices.update(prices)

    invs = [{}]
    if cargo:
        invs[0] = copy.deepcopy(cargo)

    tiles = [[None] * 10 for _ in range(10)]
    if animals:
        for idx, a in enumerate(animals):
            k = a.get("structure", "PASTURE")
            sub = a.get("kind", "COW")
            tiles[idx][0] = {"kind": k, "animal": sub, "fed_today": a.get("fed_today", False)}

    return {
        "step": step,
        "day": step // 24,
        "hour": step % 24,
        "player": 0,
        "farms": [
            {
                "money": cash,
                "farmer": [4, 4],
                "hands": hands or [],
                "tiles": tiles,
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
            {
                "money": 3000.0,
                "farmer": [4, 4],
                "hands": [],
                "tiles": [[None] * 10 for _ in range(10)],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
        ],
        "private": {
            "shed": full_shed,
            "seeds": {},
            "inventories": invs,
        },
        "market": {
            "prices": full_prices,
            "inventory": {p: 1000 for p in full_prices},
        },
        "town": {"unlocked_shops": []},
    }


# =============================================================================
# PART 1: ASSET-HOLDING VALUATION TRIGGER (20 SCENARIOS)
# =============================================================================

class MockPressure:
    def __init__(self, rival_dist=999, collision=False):
        self.rival_distance_to_market = rival_dist
        self.market_collision_risk = collision


def test_scenario_01_favorable_price_trigger():
    """Case 1: Favorable price regime (P=140 vs base=100) emits FAVOURABLE_MARKET_HOLDING."""
    obs = _canonical_obs(shed={"STRAWBERRY": 25}, prices={"STRAWBERRY": 140})
    econ = build_economic_state(obs)
    trigger = AssetHoldingValuationTrigger()
    feat = trigger.extract_structural_features(econ, "STRAWBERRY")
    assert feat is not None
    assert feat.price_ratio >= 1.15
    res = trigger.evaluate_opportunity(feat)
    assert res is not None
    opp_type, rationale, relevance = res
    assert opp_type == HoldingOpportunityType.FAVOURABLE_MARKET_HOLDING
    assert relevance > 0


def test_scenario_02_unfavorable_price_abstain():
    """Case 2: Depressed market price (P=60 vs base=100) abstains."""
    obs = _canonical_obs(shed={"STRAWBERRY": 25}, prices={"STRAWBERRY": 60})
    econ = build_economic_state(obs)
    trigger = AssetHoldingValuationTrigger()
    feat = trigger.extract_structural_features(econ, "STRAWBERRY")
    assert feat is not None
    assert feat.price_ratio < 1.0
    res = trigger.evaluate_opportunity(feat)
    assert res is None


def test_scenario_03_price_rising_realization_option():
    """Case 3: Rising price trajectory sets SELL_LATER option."""
    obs = _canonical_obs(shed={"MELON": 15}, prices={"MELON": 260})
    econ = build_economic_state(obs)
    econ.market.liquidity_ratios["MELON"] = 1.20
    trigger = AssetHoldingValuationTrigger()
    feat = trigger.extract_structural_features(econ, "MELON")
    assert feat.price_trajectory == "RISING"
    assert RealizationOption.SELL_LATER.value in feat.realization_options


def test_scenario_04_market_saturation_risk():
    """Case 4: Congested shed with falling price emits MARKET_SATURATION_RISK."""
    obs = _canonical_obs(shed={"CARROT": 75, "WHEAT": 10}, prices={"CARROT": 30})
    econ = build_economic_state(obs)
    econ.market.liquidity_ratios["CARROT"] = 0.85
    trigger = AssetHoldingValuationTrigger()
    feat = trigger.extract_structural_features(econ, "CARROT")
    res = trigger.evaluate_opportunity(feat)
    assert res is not None
    assert res[0] == HoldingOpportunityType.MARKET_SATURATION_RISK


def test_scenario_05_persistent_state_deduplication():
    """Case 5: Repeated identical state does not spam trigger once rejected."""
    obs = _canonical_obs(shed={"STRAWBERRY": 20}, prices={"STRAWBERRY": 140})
    econ = build_economic_state(obs)
    trigger = AssetHoldingValuationTrigger()
    feat1 = trigger.extract_structural_features(econ, "STRAWBERRY")
    assert trigger.evaluate_opportunity(feat1) is not None
    
    # Simulate exact rejection
    fp_str = feat1.fingerprint.fingerprint_string()
    trigger.record_counterfactual_outcome(fp_str, was_accepted=False)
    
    # Next turn with identical structural features: suppressed
    feat2 = trigger.extract_structural_features(econ, "STRAWBERRY")
    assert trigger.evaluate_opportunity(feat2) is None


def test_scenario_06_terminal_holding_risk():
    """Case 6: Endgame turn (step 680) with held inventory emits TERMINAL_HOLDING_RISK."""
    obs = _canonical_obs(step=680, shed={"MELON": 10}, prices={"MELON": 200})
    econ = build_economic_state(obs)
    trigger = AssetHoldingValuationTrigger()
    feat = trigger.extract_structural_features(econ, "MELON")
    res = trigger.evaluate_opportunity(feat)
    assert res is not None
    assert res[0] == HoldingOpportunityType.TERMINAL_HOLDING_RISK


def test_scenario_07_liquidity_holding_conflict():
    """Case 7: Cash deficit below daily wage buffer emits LIQUIDITY_HOLDING_CONFLICT."""
    obs = _canonical_obs(cash=20.0, shed={"STRAWBERRY": 15}, prices={"STRAWBERRY": 110})
    econ = build_economic_state(obs)
    trigger = AssetHoldingValuationTrigger()
    feat = trigger.extract_structural_features(econ, "STRAWBERRY")
    assert feat.liquidity_deficit > 0
    res = trigger.evaluate_opportunity(feat)
    assert res is not None
    assert res[0] == HoldingOpportunityType.LIQUIDITY_HOLDING_CONFLICT


def test_scenario_08_hard_feed_dependency_reservation():
    """Case 8: Livestock herd of 2 reserves 6 wheat; only excess is uncommitted."""
    animals = [{"kind": "COW", "fed_today": True}, {"kind": "SHEEP", "fed_today": True}]
    obs = _canonical_obs(shed={"WHEAT": 15}, animals=animals)
    econ = build_economic_state(obs)
    trigger = AssetHoldingValuationTrigger()
    feat = trigger.extract_structural_features(econ, "WHEAT")
    assert feat.quantity_held == 15
    # 15 held - 6 reserved = 9 uncommitted
    assert feat.uncommitted_quantity == 9


def test_scenario_09_feed_reservation_exhaustion_abstain():
    """Case 9: When all held wheat is reserved for animals, trigger returns None."""
    animals = [{"kind": "COW", "fed_today": True}, {"kind": "SHEEP", "fed_today": True}]
    obs = _canonical_obs(shed={"WHEAT": 5}, animals=animals)
    econ = build_economic_state(obs)
    trigger = AssetHoldingValuationTrigger()
    feat = trigger.extract_structural_features(econ, "WHEAT")
    assert feat.uncommitted_quantity == 0
    res = trigger.evaluate_opportunity(feat)
    assert res is None


def test_scenario_10_opponent_pressure_trigger():
    """Case 10: Rival within distance 2 of market emits OPPONENT_PRESSURE."""
    obs = _canonical_obs(shed={"TOMATO": 20}, prices={"TOMATO": 65})
    econ = build_economic_state(obs)
    trigger = AssetHoldingValuationTrigger()
    feat = trigger.extract_structural_features(econ, "TOMATO", pressure_state=MockPressure(rival_dist=2))
    assert feat.rival_proximity == 2
    res = trigger.evaluate_opportunity(feat)
    assert res is not None
    assert res[0] == HoldingOpportunityType.OPPONENT_PRESSURE


def test_scenario_11_dependency_coupled_holding_congestion():
    """Case 11: Shed congestion (total >= 80 units) emits DEPENDENCY_COUPLED_HOLDING."""
    obs = _canonical_obs(shed={"CARROT": 50, "WHEAT": 35}, prices={"CARROT": 35, "WHEAT": 25})
    econ = build_economic_state(obs)
    trigger = AssetHoldingValuationTrigger()
    feat = trigger.extract_structural_features(econ, "CARROT")
    assert feat.storage_utilization >= 0.80
    res = trigger.evaluate_opportunity(feat)
    assert res is not None
    assert res[0] == HoldingOpportunityType.DEPENDENCY_COUPLED_HOLDING


def test_scenario_12_multi_product_portfolio_evaluation():
    """Case 12: Analyzer independently detects multiple held assets in shed."""
    obs = _canonical_obs(shed={"STRAWBERRY": 30, "MELON": 15}, prices={"STRAWBERRY": 140, "MELON": 300})
    econ = build_economic_state(obs)
    analyzer = AssetHoldingOpportunityAnalyzer()
    opps = analyzer.analyze(econ, events=[])
    commodities = {o.affected_entities[0] for o in opps}
    assert "STRAWBERRY" in commodities
    assert "MELON" in commodities


def test_scenario_13_worker_cargo_trigger_when_shed_empty():
    """Case 13: Held cargo carried by worker is detected when shed is empty."""
    obs = _canonical_obs(shed={}, cargo={"MELON": 8}, prices={"MELON": 260})
    econ = build_economic_state(obs)
    trigger = AssetHoldingValuationTrigger()
    feat = trigger.extract_structural_features(econ, "MELON")
    assert feat is not None
    assert feat.quantity_held == 8
    assert RealizationOption.REPOSITION.value in feat.realization_options


def test_scenario_14_baseline_already_selling_defers():
    """Case 14: If baseline is already selling commodity, trigger defers."""
    obs = _canonical_obs(shed={"STRAWBERRY": 25}, prices={"STRAWBERRY": 140})
    econ = build_economic_state(obs)
    trigger = AssetHoldingValuationTrigger()
    feat = trigger.extract_structural_features(econ, "STRAWBERRY")
    res = trigger.evaluate_opportunity(feat, baseline_has_sell=True)
    assert res is None


def test_scenario_15_empty_inventory_returns_none():
    """Case 15: Zero physical inventory returns None."""
    obs = _canonical_obs(shed={"STRAWBERRY": 0})
    econ = build_economic_state(obs)
    trigger = AssetHoldingValuationTrigger()
    feat = trigger.extract_structural_features(econ, "STRAWBERRY")
    assert feat is None


def test_scenario_16_insufficient_volume_abstains():
    """Case 16: Favorable price with tiny volume (1 unit) does not trigger favorable holding."""
    obs = _canonical_obs(shed={"STRAWBERRY": 1}, prices={"STRAWBERRY": 140})
    econ = build_economic_state(obs)
    trigger = AssetHoldingValuationTrigger()
    feat = trigger.extract_structural_features(econ, "STRAWBERRY")
    res = trigger.evaluate_opportunity(feat)
    assert res is None


def test_scenario_17_fingerprint_reset_on_price_shift():
    """Case 17: Price shift to a new band resets deduplication and permits fresh trigger."""
    obs1 = _canonical_obs(shed={"STRAWBERRY": 20}, prices={"STRAWBERRY": 120})
    econ1 = build_economic_state(obs1)
    trigger = AssetHoldingValuationTrigger()
    feat1 = trigger.extract_structural_features(econ1, "STRAWBERRY")
    trigger.record_counterfactual_outcome(feat1.fingerprint.fingerprint_string(), was_accepted=False)

    # Price jumps to 150 (new price band)
    obs2 = _canonical_obs(shed={"STRAWBERRY": 20}, prices={"STRAWBERRY": 150})
    econ2 = build_economic_state(obs2)
    feat2 = trigger.extract_structural_features(econ2, "STRAWBERRY")
    assert feat2.fingerprint.fingerprint_string() != feat1.fingerprint.fingerprint_string()
    res2 = trigger.evaluate_opportunity(feat2)
    assert res2 is not None


def test_scenario_18_terminal_phase_shift_resets_fingerprint():
    """Case 18: Step advance into terminal phase resets fingerprint."""
    obs_mid = _canonical_obs(step=450, shed={"STRAWBERRY": 20}, prices={"STRAWBERRY": 100})
    econ_mid = build_economic_state(obs_mid)
    trigger = AssetHoldingValuationTrigger()
    feat_mid = trigger.extract_structural_features(econ_mid, "STRAWBERRY")
    trigger.record_counterfactual_outcome(feat_mid.fingerprint.fingerprint_string(), was_accepted=False)

    obs_late = _canonical_obs(step=680, shed={"STRAWBERRY": 20}, prices={"STRAWBERRY": 100})
    econ_late = build_economic_state(obs_late)
    feat_late = trigger.extract_structural_features(econ_late, "STRAWBERRY")
    assert feat_late.fingerprint.terminal_phase != feat_mid.fingerprint.terminal_phase
    assert trigger.evaluate_opportunity(feat_late) is not None


def test_scenario_19_static_turn_350_emits_event():
    """Case 19: detect_events emits E13 on static turn 350 without delta_cash or delta_shed."""
    obs = _canonical_obs(step=350, shed={"STRAWBERRY": 30}, prices={"STRAWBERRY": 135})
    econ = build_economic_state(obs)
    cfg = build_phase015_treatment_config()
    events = detect_events(econ, previous_state=econ, config=cfg)
    e13s = [e for e in events if e.event_type == EventType.E13_ASSET_HOLDING_STATE]
    assert len(e13s) == 1
    assert "STRAWBERRY" in e13s[0].payload["commodities"]


def test_scenario_20_opportunity_metadata_completeness():
    """Case 20: Emitted opportunity contains required structural metadata and realization options."""
    obs = _canonical_obs(shed={"STRAWBERRY": 40}, prices={"STRAWBERRY": 140})
    econ = build_economic_state(obs)
    analyzer = AssetHoldingOpportunityAnalyzer()
    opps = analyzer.analyze(econ, events=[])
    assert len(opps) >= 1
    opp = opps[0]
    assert "realization_options" in opp.dependency_info
    assert "fingerprint" in opp.dependency_info
    assert opp.required_horizon in (6, 18)


# =============================================================================
# PART 2: AUTONOMOUS TRANCHE ORDER SYNTHESIZER (20 SCENARIOS)
# =============================================================================

def test_scenario_21_synthesis_from_empty_market_queue():
    """Case 21: Synthesizes valid market order when baseline queue is empty."""
    obs = _canonical_obs(shed={"STRAWBERRY": 30}, prices={"STRAWBERRY": 140})
    econ = build_economic_state(obs)
    synth = AutonomousTrancheOrderSynthesizer()
    ok, real_q, _ = synth.verify_inventory_realizability(econ, "STRAWBERRY", 10)
    assert ok is True
    orders = synth.construct_sequential_market_orders([], "STRAWBERRY", real_q)
    assert len(orders) == 1
    assert orders[0] == ["SELL", "STRAWBERRY", 10]


def test_scenario_22_minimal_tranche_anchor():
    """Case 22: Generates minimal tranche quantity anchor."""
    obs = _canonical_obs(shed={"MELON": 20})
    econ = build_economic_state(obs)
    synth = AutonomousTrancheOrderSynthesizer()
    qs = synth.compute_structural_quantities(econ, "MELON", 20)
    assert any(q == 5 and r == "MINIMAL_TRANCHE" for q, r in qs)


def test_scenario_23_depth_compatible_tranche():
    """Case 23: Generates 10-unit depth parcel."""
    obs = _canonical_obs(shed={"CARROT": 40})
    econ = build_economic_state(obs)
    synth = AutonomousTrancheOrderSynthesizer()
    qs = synth.compute_structural_quantities(econ, "CARROT", 40)
    assert any(q == 10 and r == "DEPTH_COMPATIBLE_TRANCHE" for q, r in qs)


def test_scenario_24_full_liquidation_anchor():
    """Case 24: Generates full uncommitted inventory anchor."""
    obs = _canonical_obs(shed={"MELON": 25})
    econ = build_economic_state(obs)
    synth = AutonomousTrancheOrderSynthesizer()
    qs = synth.compute_structural_quantities(econ, "MELON", 25)
    assert any(q == 25 and r == "FULL_UNCOMMITTED_LIQUIDATION" for q, r in qs)


def test_scenario_25_storage_clearing_anchor():
    """Case 25: Shed total >= 80 units generates storage clearing tranche."""
    obs = _canonical_obs(shed={"WHEAT": 85})
    econ = build_economic_state(obs)
    synth = AutonomousTrancheOrderSynthesizer()
    qs = synth.compute_structural_quantities(econ, "WHEAT", 85)
    assert any(r == "STORAGE_CLEARING" for q, r in qs)


def test_scenario_26_liquidity_clearing_anchor():
    """Case 26: Cash deficit generates liquidity clearing tranche."""
    obs = _canonical_obs(cash=20.0, shed={"STRAWBERRY": 20}, prices={"STRAWBERRY": 100})
    econ = build_economic_state(obs)
    synth = AutonomousTrancheOrderSynthesizer()
    qs = synth.compute_structural_quantities(econ, "STRAWBERRY", 20)
    assert any(r == "LIQUIDITY_CLEARING" for q, r in qs)


def test_scenario_27_terminal_liquidation_anchor():
    """Case 27: Endgame step 690 generates terminal liquidation anchor."""
    obs = _canonical_obs(step=690, shed={"MELON": 15})
    econ = build_economic_state(obs)
    synth = AutonomousTrancheOrderSynthesizer()
    qs = synth.compute_structural_quantities(econ, "MELON", 15)
    assert any(q == 15 and r == "TERMINAL_LIQUIDATION" for q, r in qs)


def test_scenario_28_multi_order_partitioning():
    """Case 28: Quantity > 10 is partitioned into atomic orders <= 10."""
    synth = AutonomousTrancheOrderSynthesizer()
    orders = synth.construct_sequential_market_orders([], "STRAWBERRY", 25)
    assert len(orders) == 3
    assert orders[0] == ["SELL", "STRAWBERRY", 10]
    assert orders[1] == ["SELL", "STRAWBERRY", 10]
    assert orders[2] == ["SELL", "STRAWBERRY", 5]


def test_scenario_29_order_limit_ceiling():
    """Case 29: Synthesized orders never exceed engine limit of 10 orders."""
    synth = AutonomousTrancheOrderSynthesizer()
    base_orders = [["BUY_SEED", "CARROT", 1] for _ in range(8)]
    orders = synth.construct_sequential_market_orders(base_orders, "STRAWBERRY", 40)
    assert len(orders) <= 10


def test_scenario_30_sequential_sell_before_buy():
    """Case 30: SELL orders are placed ahead of baseline BUY orders to unlock cash."""
    synth = AutonomousTrancheOrderSynthesizer()
    base_orders = [["BUY_SEED", "STRAWBERRY", 5], ["BUY_PRODUCT", "FERTILIZER", 1]]
    orders = synth.construct_sequential_market_orders(base_orders, "MELON", 10)
    assert orders[0] == ["SELL", "MELON", 10]
    assert orders[1] == ["BUY_SEED", "STRAWBERRY", 5]
    assert orders[2] == ["BUY_PRODUCT", "FERTILIZER", 1]


def test_scenario_31_preserves_existing_sells():
    """Case 31: Existing baseline SELL orders are preserved alongside synthesized tranche."""
    synth = AutonomousTrancheOrderSynthesizer()
    base_orders = [["SELL", "CARROT", 5], ["BUY_SEED", "WHEAT", 2]]
    orders = synth.construct_sequential_market_orders(base_orders, "STRAWBERRY", 10)
    # synthesized SELL first, then existing SELL, then BUY
    assert orders[0] == ["SELL", "STRAWBERRY", 10]
    assert orders[1] == ["SELL", "CARROT", 5]
    assert orders[2] == ["BUY_SEED", "WHEAT", 2]


def test_scenario_32_unadmissible_product_rejection():
    """Case 32: Unadmissible commodity is rejected by realizability check."""
    obs = _canonical_obs()
    econ = build_economic_state(obs)
    synth = AutonomousTrancheOrderSynthesizer()
    ok, q, reason = synth.verify_inventory_realizability(econ, "DIAMOND", 10)
    assert ok is False
    assert "UNADMISSIBLE_PRODUCT" in reason


def test_scenario_33_zero_inventory_rejection():
    """Case 33: Zero physical inventory is rejected."""
    obs = _canonical_obs(shed={"MELON": 0})
    econ = build_economic_state(obs)
    synth = AutonomousTrancheOrderSynthesizer()
    ok, q, reason = synth.verify_inventory_realizability(econ, "MELON", 5)
    assert ok is False
    assert "ZERO_PHYSICAL_INVENTORY" in reason


def test_scenario_34_livestock_wheat_reservation_enforced():
    """Case 34: Livestock feed reservation prevents selling essential wheat."""
    animals = [{"kind": "COW", "fed_today": True}, {"kind": "SHEEP", "fed_today": True}]
    obs = _canonical_obs(shed={"WHEAT": 5}, animals=animals)
    econ = build_economic_state(obs)
    synth = AutonomousTrancheOrderSynthesizer()
    ok, q, reason = synth.verify_inventory_realizability(econ, "WHEAT", 5)
    assert ok is False
    assert "FEED_SECURITY_RESERVED" in reason


def test_scenario_35_partial_wheat_realizability():
    """Case 35: Excess wheat beyond feed reservation is realizable."""
    animals = [{"kind": "COW", "fed_today": True}, {"kind": "SHEEP", "fed_today": True}]
    obs = _canonical_obs(shed={"WHEAT": 10}, animals=animals)
    econ = build_economic_state(obs)
    synth = AutonomousTrancheOrderSynthesizer()
    ok, q, _ = synth.verify_inventory_realizability(econ, "WHEAT", 10)
    assert ok is True
    # 10 - 6 = 4 realizable
    assert q == 4


def test_scenario_36_causal_attribution_logging():
    """Case 36: why_v3_did_not_do_this records worker traveling when farmer moving."""
    obs = _canonical_obs()
    econ = build_economic_state(obs)
    synth = AutonomousTrancheOrderSynthesizer()
    base_act = {"farmer": ["MOVE", "NORTH"], "hands": [], "market": []}
    why = synth.determine_why_v3_did_not_do_this(econ, base_act, "STRAWBERRY")
    assert "V3_WORKER_TRAVELING" in why


def test_scenario_37_adaptive_horizon_selection():
    """Case 37: Synthesizer assigns short horizon (6) for depth tranche, normal (18) for terminal."""
    obs_mid = _canonical_obs(step=300, shed={"STRAWBERRY": 20}, prices={"STRAWBERRY": 140})
    econ_mid = build_economic_state(obs_mid)
    analyzer = AssetHoldingOpportunityAnalyzer()
    opps = analyzer.analyze(econ_mid, events=[])
    synth = AutonomousTrancheOrderSynthesizer()
    patches = synth.synthesize_candidates(opps[0], econ_mid, {"farmer": ["PASS"], "market": []})
    depth_patch = [p for p in patches if "DEPTH" in p.rationale][0]
    assert depth_patch.expected_horizon == 6

    obs_term = _canonical_obs(step=690, shed={"STRAWBERRY": 20}, prices={"STRAWBERRY": 140})
    econ_term = build_economic_state(obs_term)
    opps_term = analyzer.analyze(econ_term, events=[])
    patches_term = synth.synthesize_candidates(opps_term[0], econ_term, {"farmer": ["PASS"], "market": []})
    assert any(p.expected_horizon == 18 for p in patches_term)


def test_scenario_38_quantity_clamping_to_uncommitted():
    """Case 38: Candidate quantities never exceed uncommitted physical units."""
    obs = _canonical_obs(shed={"STRAWBERRY": 7})
    econ = build_economic_state(obs)
    synth = AutonomousTrancheOrderSynthesizer()
    qs = synth.compute_structural_quantities(econ, "STRAWBERRY", 7)
    for q, _ in qs:
        assert 1 <= q <= 7


def test_scenario_39_deduplication_of_overlapping_anchors():
    """Case 39: When q_min and q_depth overlap (e.g. qty=5), duplicate quantities are pruned."""
    obs = _canonical_obs(shed={"STRAWBERRY": 5})
    econ = build_economic_state(obs)
    synth = AutonomousTrancheOrderSynthesizer()
    qs = synth.compute_structural_quantities(econ, "STRAWBERRY", 5)
    quantities = [q for q, _ in qs]
    assert len(quantities) == len(set(quantities))


def test_scenario_40_structural_fingerprint_in_patch_metadata():
    """Case 40: Synthesized patch metadata contains structural fingerprint and causal reason."""
    obs = _canonical_obs(shed={"STRAWBERRY": 30}, prices={"STRAWBERRY": 140})
    econ = build_economic_state(obs)
    analyzer = AssetHoldingOpportunityAnalyzer()
    opps = analyzer.analyze(econ, events=[])
    synth = AutonomousTrancheOrderSynthesizer()
    patches = synth.synthesize_candidates(opps[0], econ, {"farmer": ["PASS"], "market": []})
    assert len(patches) >= 1
    p = patches[0]
    assert "structural_fingerprint" in p.dependency_info
    assert "why_v3_did_not_do_this" in p.dependency_info
    assert p.dependency_info["is_autonomous_synthesis"] is True
