import kagsim
from aec.integration.executor import AECExecutor
from scripts.run_phase017_attribution_audit import build_phase015_treatment_config, build_robust_qualified_config
from aec.config import ENABLED_FOUNDATION_MECHANISMS

# Monkey-patch OpportunityEngine.detect_opportunities to reserve foundation slots
from aec.opportunities import OpportunityEngine

orig_detect = OpportunityEngine.detect_opportunities

def reserved_detect_opportunities(self, econ_state, events, baseline_action=None, max_opportunities=16, config=None, pressure_state=None):
    enabled = set(config.enabled_mechanisms) if config is not None else self.enabled_mechanisms
    is_frozen = config.frozen_mode if config is not None else (self.mode == "frozen")

    raw_opportunities = []
    # 1. Foundation Analyzers
    raw_opportunities.extend(self.route_analyzer.analyze(econ_state, events, baseline_action))
    raw_opportunities.extend(self.market_analyzer.analyze(econ_state, events, baseline_action))
    raw_opportunities.extend(self.terminal_analyzer.analyze(econ_state, events, baseline_action))
    raw_opportunities.extend(self.resource_analyzer.analyze(econ_state, events, baseline_action))
    raw_opportunities.extend(self.labor_analyzer.analyze(econ_state, events, baseline_action))
    raw_opportunities.extend(self.timing_analyzer.analyze(econ_state, events, baseline_action))

    # 2. Phase 007 Analyzers
    raw_opportunities.extend(self.route_compression_detector.detect(econ_state, worker_id=0))
    raw_opportunities.extend(self.cargo_ferry_detector.detect(econ_state, baseline_action))
    raw_opportunities.extend(self.production_arbitrage_detector.detect(econ_state))
    raw_opportunities.extend(self.shop_arbitrage_detector.detect(econ_state))
    raw_opportunities.extend(self.terminal_conversion_detector.detect(econ_state))
    raw_opportunities.extend(self.opponent_preemption_detector.detect(econ_state, pressure_state))
    raw_opportunities.extend(self.emergency_recovery_detector.detect(econ_state, baseline_action))
    raw_opportunities.extend(self.town_cycle_detector.detect(econ_state, baseline_action))

    # 3. Phase 015 Capability A
    trigger_active = (
        "ASSET_HOLDING_VALUATION_TRIGGER" in enabled
        or getattr(config, "enable_asset_holding_trigger", False)
        or not is_frozen
    )
    if trigger_active:
        raw_opportunities.extend(
            self.asset_holding_analyzer.analyze(econ_state, events, baseline_action, pressure_state)
        )

    actionable = []
    quarantined = []
    for opp in raw_opportunities:
        fam = opp.candidate_transformation_family
        if is_frozen:
            if fam in enabled or fam == "LOCAL_WEED_DIG":
                actionable.append(opp)
            else:
                quarantined.append(opp)
        else:
            actionable.append(opp)

    self.last_quarantined_opportunities = quarantined

    # Mechanism Reservation: partition foundation vs experimental
    foundation_opps = [o for o in actionable if o.candidate_transformation_family in ENABLED_FOUNDATION_MECHANISMS]
    other_opps = [o for o in actionable if o.candidate_transformation_family not in ENABLED_FOUNDATION_MECHANISMS]

    foundation_opps.sort(key=lambda o: -o.estimated_economic_relevance)
    other_opps.sort(key=lambda o: -o.estimated_economic_relevance)

    # Reserve up to 4 slots for foundation, fill rest up to max_opportunities
    n_found = min(len(foundation_opps), max(4, max_opportunities // 2))
    selected_foundation = foundation_opps[:n_found]
    rem_budget = max_opportunities - len(selected_foundation)
    selected_other = other_opps[:rem_budget]
    
    # If other didn't use all budget, backfill with remaining foundation
    rem_foundation = foundation_opps[n_found : n_found + (rem_budget - len(selected_other))]
    res = selected_foundation + rem_foundation + selected_other
    return res

OpportunityEngine.detect_opportunities = reserved_detect_opportunities

# Also patch candidate_funnel top-k to respect foundation reservation
from aec.funnel.candidate_funnel import OpportunityCandidateFunnel, FunnelStageRecord, FunnelStage
import time

orig_top_k = OpportunityCandidateFunnel._stage_deterministic_top_k

def reserved_top_k(self, candidates, econ_state, max_k):
    t0 = time.perf_counter()
    def tie_break_key(c):
        val = round(-float(getattr(c, "estimated_economic_value", 0.0) or getattr(c, "estimated_economic_relevance", 0.0)), 4)
        fam = str(getattr(c, "mechanism_family", "") or getattr(c, "candidate_transformation_family", ""))
        wid = int(getattr(c, "worker_id", 0) or 0)
        pos = getattr(c, "target_pos", None) or getattr(c, "target_position", (0, 0))
        pos_x, pos_y = pos[0], pos[1]
        step = int(getattr(c, "step", econ_state.step) or 0)
        cid = str(getattr(c, "patch_id", "") or getattr(c, "opportunity_id", ""))
        return (val, fam, wid, pos_x, pos_y, step, cid)

    found = [c for c in candidates if getattr(c, "mechanism_family", "") in ENABLED_FOUNDATION_MECHANISMS]
    other = [c for c in candidates if getattr(c, "mechanism_family", "") not in ENABLED_FOUNDATION_MECHANISMS]
    found.sort(key=tie_break_key)
    other.sort(key=tie_break_key)

    n_found = min(len(found), max(2, max_k // 2))
    sel_found = found[:n_found]
    rem = max_k - len(sel_found)
    sel_other = other[:rem]
    backfill_found = found[n_found : n_found + (rem - len(sel_other))]
    top_k = sel_found + backfill_found + sel_other

    eliminated = max(0, len(candidates) - len(top_k))
    reasons = {"EXCEEDED_MAX_K_BUDGET": eliminated} if eliminated > 0 else {}
    rec = FunnelStageRecord(
        stage=FunnelStage.S9_DETERMINISTIC_TOP_K,
        candidates_in=len(candidates),
        candidates_out=len(top_k),
        eliminated_count=eliminated,
        elimination_reasons=reasons,
        latency_ms=(time.perf_counter() - t0) * 1000.0
    )
    return top_k, rec

OpportunityCandidateFunnel._stage_deterministic_top_k = reserved_top_k

# Now test seed 249288 full match
def run_mirror(seed):
    trt_cfg = build_phase015_treatment_config()
    ctrl_cfg = build_robust_qualified_config()

    # Match 1: trt=0, ctrl=1
    g1 = kagsim.Game(seed)
    e0 = AECExecutor(config=trt_cfg)
    e1 = AECExecutor(config=ctrl_cfg)
    while not g1.done:
        a0 = e0.act(g1.observe(0))
        a1 = e1.act(g1.observe(1))
        g1.step(a0, a1)
    m1 = float(g1.reward(0)) - float(g1.reward(1))

    # Match 2: trt=1, ctrl=0
    g2 = kagsim.Game(seed)
    e0 = AECExecutor(config=ctrl_cfg)
    e1 = AECExecutor(config=trt_cfg)
    while not g2.done:
        a0 = e0.act(g2.observe(0))
        a1 = e1.act(g2.observe(1))
        g2.step(a0, a1)
    m2 = float(g2.reward(1)) - float(g2.reward(0))

    paired_margin = (m1 + m2) / 2.0
    print(f"Seed {seed}: m1={m1:.2f}, m2={m2:.2f}, paired_margin={paired_margin:.2f}")
    print(f"  Trt commits match 1: {sum(1 for t in e0._telemetry_history if t.decision == 'COMMIT')}")
    print(f"  Trt commits match 2: {sum(1 for t in e1._telemetry_history if t.decision == 'COMMIT')}")

run_mirror(249288)
