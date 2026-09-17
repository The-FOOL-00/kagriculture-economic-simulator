# SPDX-License-Identifier: MIT
"""Test D — Coupled Patch Generation and Pruning."""

from aec.events import detect_events
from aec.ir import build_economic_state
from aec.opportunities import OpportunityEngine
from aec.patches import PatchGenerator, prune_patches


def test_coupled_patch_synthesis(weed_obstruction_obs):
    state = build_economic_state(weed_obstruction_obs)
    events = detect_events(state)
    engine = OpportunityEngine()
    generator = PatchGenerator()
    
    baseline = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    opps = engine.detect_opportunities(state, events, baseline)
    patches = generator.generate_patches(opps, state, baseline)
    
    assert len(patches) > 0
    dig_patch = next((p for p in patches if 0 in p.worker_mutations), None)
    assert dig_patch is not None
    assert dig_patch.worker_mutations[0] == ["DIG"]


def test_patch_pruning_bounds(terminal_proximity_obs):
    state = build_economic_state(terminal_proximity_obs)
    events = detect_events(state)
    engine = OpportunityEngine()
    generator = PatchGenerator()
    
    baseline = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    opps = engine.detect_opportunities(state, events, baseline)
    raw_patches = generator.generate_patches(opps, state, baseline)
    pruned = prune_patches(raw_patches, state, max_candidates=3)
    
    assert len(pruned) <= 3
