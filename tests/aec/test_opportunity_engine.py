# SPDX-License-Identifier: MIT
"""Test C — Opportunity Engine Analyzers."""

from aec.events import detect_events
from aec.ir import build_economic_state
from aec.opportunities import OpportunityEngine


def test_route_opportunity_detected_on_weed(weed_obstruction_obs):
    state = build_economic_state(weed_obstruction_obs)
    events = detect_events(state)
    engine = OpportunityEngine()
    
    baseline_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    opps = engine.detect_opportunities(state, events, baseline_act)
    
    assert len(opps) > 0
    route_opp = next((o for o in opps if o.category == "ROUTE"), None)
    assert route_opp is not None
    assert route_opp.candidate_transformation_family == "LOCAL_WEED_DIG"
    assert route_opp.affected_entities[0] == 0  # Farmer ID


def test_terminal_liquidation_opportunity_at_718(terminal_proximity_obs):
    state = build_economic_state(terminal_proximity_obs)
    events = detect_events(state)
    engine = OpportunityEngine()
    
    opps = engine.detect_opportunities(state, events, {"farmer": ["PASS"], "hands": [], "market": []})
    term_opp = next((o for o in opps if o.category == "TERMINAL"), None)
    assert term_opp is not None
    assert term_opp.candidate_transformation_family == "TERMINAL_LIQUIDATION"


def test_opportunity_count_bounded(terminal_proximity_obs):
    state = build_economic_state(terminal_proximity_obs)
    events = detect_events(state)
    engine = OpportunityEngine()
    
    opps = engine.detect_opportunities(state, events, max_opportunities=5)
    assert len(opps) <= 5
