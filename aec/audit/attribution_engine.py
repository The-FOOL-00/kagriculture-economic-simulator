# SPDX-License-Identifier: MIT
"""AEC Causal Attribution Engine and Detector Coverage Auditor (§12, §13, §14, §30)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from aec.audit.oracle_probe import OracleAlternativeResult, OracleCategory, OracleProbeResult


class CausalFailureLayer(str, Enum):
    """Causal failure hierarchy assigning exactly one primary layer (§12)."""
    NONE_AEC_COMMITTED = "NONE_AEC_COMMITTED"
    NOT_DETECTED = "NOT_DETECTED"                  # Event or Opportunity detector missed the state
    NOT_REPRESENTED = "NOT_REPRESENTED"            # Opportunity detected but candidate generator cannot formulate action
    FILTERED = "FILTERED"                          # Static feasibility pruning or candidate funnel budget drop
    NOT_PATCHABLE = "NOT_PATCHABLE"                # Action malformed, invalid preconditions, or missing trajectory
    RECONNECT_FAILED = "RECONNECT_FAILED"          # Spliced reconnect failed or caused worker spatial desync
    HORIZON_INSUFFICIENT = "HORIZON_INSUFFICIENT"  # Standard horizon H=18 cannot see downstream gain (needs H=36)
    COUNTERFACTUAL_REJECTED = "COUNTERFACTUAL_REJECTED" # Exact simulation evaluates delta <= 0 (model divergence)
    SAFETY_REJECTED = "SAFETY_REJECTED"            # Safety checker rejected (solvency, overflow, or collision)
    MACRO_CONSTRAINED = "MACRO_CONSTRAINED"        # Blocked by macro strategy controller
    OPPONENT_CONTINGENT = "OPPONENT_CONTINGENT"    # Value requires explicit opponent model adaptation
    COMPOSITION_ONLY = "COMPOSITION_ONLY"          # Single transformation weak; requires pairwise coupling


@dataclass
class CandidateGapRecord:
    """Row in the Candidate-Gap Matrix (§14)."""
    oracle_opportunity: str
    current_mechanism: Optional[str]
    detected: bool
    represented: bool
    patchable: bool
    exact_sim: bool
    safety_pass: bool
    final_decision: str
    missing_layer: str
    oracle_delta: float
    seed: int
    step: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "oracle_opportunity": self.oracle_opportunity,
            "current_mechanism": self.current_mechanism,
            "detected": self.detected,
            "represented": self.represented,
            "patchable": self.patchable,
            "exact_sim": self.exact_sim,
            "safety_pass": self.safety_pass,
            "final_decision": self.final_decision,
            "missing_layer": self.missing_layer,
            "oracle_delta": round(self.oracle_delta, 2),
            "seed": self.seed,
            "step": self.step,
        }


@dataclass
class ScorecardRow:
    """Row in the Headroom Scorecard (§30)."""
    gap_class: str
    states_count: int
    positive_headroom_total: float
    mean_headroom: float
    current_aec_coverage: float   # fraction of positive states captured [0.0, 1.0]
    representability: float       # feasibility of AEC representation [0.0, 1.0]
    priority_score: float         # frequency * measurable_headroom * representability

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gap_class": self.gap_class,
            "states_count": self.states_count,
            "positive_headroom_total": round(self.positive_headroom_total, 2),
            "mean_headroom": round(self.mean_headroom, 2),
            "current_aec_coverage": round(self.current_aec_coverage, 4),
            "representability": round(self.representability, 2),
            "priority_score": round(self.priority_score, 2),
        }


class AttributionEngine:
    """Audits detector coverage and attributes missing headroom to causal layers."""

    def __init__(self) -> None:
        self.gap_records: List[CandidateGapRecord] = []

    def attribute_state(
        self,
        probe_result: OracleProbeResult,
        aec_telemetry: Optional[Any],
        seed: int,
    ) -> Tuple[CausalFailureLayer, str, Optional[CandidateGapRecord]]:
        step = probe_result.step
        alt = probe_result.best_alternative

        if alt is None or probe_result.local_headroom <= 0.5:
            return CausalFailureLayer.NONE_AEC_COMMITTED, "Zero detectable headroom", None

        oracle_opp = f"{alt.family}: {alt.description}"
        delta = probe_result.local_headroom

        if aec_telemetry is None:
            rec = CandidateGapRecord(
                oracle_opportunity=oracle_opp,
                current_mechanism=None,
                detected=False,
                represented=False,
                patchable=False,
                exact_sim=False,
                safety_pass=False,
                final_decision="NO_AEC",
                missing_layer=CausalFailureLayer.NOT_DETECTED.value,
                oracle_delta=delta,
                seed=seed,
                step=step,
            )
            self.gap_records.append(rec)
            return CausalFailureLayer.NOT_DETECTED, "No AEC telemetry", rec

        # Check if AEC committed
        dec = getattr(aec_telemetry, "decision", "BACKBONE")
        committed_mech = getattr(aec_telemetry, "committed_mechanism", None)

        if dec == "COMMIT" and committed_mech:
            rec = CandidateGapRecord(
                oracle_opportunity=oracle_opp,
                current_mechanism=committed_mech,
                detected=True,
                represented=True,
                patchable=True,
                exact_sim=True,
                safety_pass=True,
                final_decision="COMMIT",
                missing_layer="NONE_CAPTURED",
                oracle_delta=delta,
                seed=seed,
                step=step,
            )
            self.gap_records.append(rec)
            return CausalFailureLayer.NONE_AEC_COMMITTED, f"Captured by {committed_mech}", rec

        # Step 1: Did EVENT & OPPORTUNITY detectors fire?
        events = getattr(aec_telemetry, "events_detected", []) or []
        opp_count = getattr(aec_telemetry, "opportunities_count", 0)

        if len(events) == 0:
            rec = CandidateGapRecord(
                oracle_opportunity=oracle_opp,
                current_mechanism=None,
                detected=False,
                represented=False,
                patchable=False,
                exact_sim=False,
                safety_pass=False,
                final_decision="NO_EVENTS",
                missing_layer=CausalFailureLayer.NOT_DETECTED.value,
                oracle_delta=delta,
                seed=seed,
                step=step,
            )
            self.gap_records.append(rec)
            return CausalFailureLayer.NOT_DETECTED, "Event detector blind to opportunity state", rec

        if opp_count == 0:
            rec = CandidateGapRecord(
                oracle_opportunity=oracle_opp,
                current_mechanism=None,
                detected=False,
                represented=False,
                patchable=False,
                exact_sim=False,
                safety_pass=False,
                final_decision="NO_OPPORTUNITIES",
                missing_layer=CausalFailureLayer.NOT_DETECTED.value,
                oracle_delta=delta,
                seed=seed,
                step=step,
            )
            self.gap_records.append(rec)
            return CausalFailureLayer.NOT_DETECTED, "Opportunity engine proposed zero opportunities", rec

        # Step 2: Did candidate funnel / generator represent it?
        cands = getattr(aec_telemetry, "candidates", []) or []
        cand_count = getattr(aec_telemetry, "candidates_count", 0)

        if cand_count == 0 and len(cands) == 0:
            rec = CandidateGapRecord(
                oracle_opportunity=oracle_opp,
                current_mechanism=None,
                detected=True,
                represented=False,
                patchable=False,
                exact_sim=False,
                safety_pass=False,
                final_decision="ZERO_CANDIDATES",
                missing_layer=CausalFailureLayer.NOT_REPRESENTED.value,
                oracle_delta=delta,
                seed=seed,
                step=step,
            )
            self.gap_records.append(rec)
            return CausalFailureLayer.NOT_REPRESENTED, "Patch generator failed to construct candidates", rec

        # Find matching candidate family if any
        matching_c = None
        for c in cands:
            c_fam = getattr(c, "mechanism_family", "")
            if alt.family in c_fam or c_fam in alt.family:
                matching_c = c
                break

        if matching_c is None:
            # Opportunities detected, but candidate family not present in active candidates
            rec = CandidateGapRecord(
                oracle_opportunity=oracle_opp,
                current_mechanism=None,
                detected=True,
                represented=False,
                patchable=False,
                exact_sim=False,
                safety_pass=False,
                final_decision="FAMILY_UNREPRESENTED",
                missing_layer=CausalFailureLayer.NOT_REPRESENTED.value,
                oracle_delta=delta,
                seed=seed,
                step=step,
            )
            self.gap_records.append(rec)
            return CausalFailureLayer.NOT_REPRESENTED, f"No candidate matching family {alt.family}", rec

        # Step 3: Was it filtered / pruned?
        was_pruned = getattr(matching_c, "patch_pruned", False)
        econ_rej = getattr(matching_c, "economic_rejection_reason", None) or ""

        if was_pruned and "STATIC_PRUNING" in econ_rej:
            rec = CandidateGapRecord(
                oracle_opportunity=oracle_opp,
                current_mechanism=matching_c.mechanism_family,
                detected=True,
                represented=True,
                patchable=False,
                exact_sim=False,
                safety_pass=False,
                final_decision="STATIC_PRUNED",
                missing_layer=CausalFailureLayer.FILTERED.value,
                oracle_delta=delta,
                seed=seed,
                step=step,
            )
            self.gap_records.append(rec)
            return CausalFailureLayer.FILTERED, "Candidate dropped during static feasibility pruning", rec

        if "MACRO" in econ_rej:
            rec = CandidateGapRecord(
                oracle_opportunity=oracle_opp,
                current_mechanism=matching_c.mechanism_family,
                detected=True,
                represented=True,
                patchable=True,
                exact_sim=False,
                safety_pass=False,
                final_decision="MACRO_INCOMPATIBLE",
                missing_layer=CausalFailureLayer.MACRO_CONSTRAINED.value,
                oracle_delta=delta,
                seed=seed,
                step=step,
            )
            self.gap_records.append(rec)
            return CausalFailureLayer.MACRO_CONSTRAINED, f"Rejected by macro controller: {econ_rej}", rec

        # Step 4: Reconnect / Spatial Consistency
        spatial_ok = getattr(matching_c, "spatial_consistency_ok", True)
        safety_rej = getattr(matching_c, "safety_rejection_reason", None) or ""

        if not spatial_ok or "RECONNECT" in safety_rej:
            rec = CandidateGapRecord(
                oracle_opportunity=oracle_opp,
                current_mechanism=matching_c.mechanism_family,
                detected=True,
                represented=True,
                patchable=False,
                exact_sim=True,
                safety_pass=False,
                final_decision="RECONNECT_FAILED",
                missing_layer=CausalFailureLayer.RECONNECT_FAILED.value,
                oracle_delta=delta,
                seed=seed,
                step=step,
            )
            self.gap_records.append(rec)
            return CausalFailureLayer.RECONNECT_FAILED, "CoupledPatch reconnect failed or desynchronized", rec

        # Step 5: Exact simulation evaluation
        sim_run = getattr(matching_c, "simulation_run", False)
        cand_delta = getattr(matching_c, "delta_margin", getattr(matching_c, "delta_money", 0.0))

        if not sim_run:
            rec = CandidateGapRecord(
                oracle_opportunity=oracle_opp,
                current_mechanism=matching_c.mechanism_family,
                detected=True,
                represented=True,
                patchable=True,
                exact_sim=False,
                safety_pass=False,
                final_decision="UNSIMULATED",
                missing_layer=CausalFailureLayer.FILTERED.value,
                oracle_delta=delta,
                seed=seed,
                step=step,
            )
            self.gap_records.append(rec)
            return CausalFailureLayer.FILTERED, "Simulation budget exhausted before candidate evaluated", rec

        # Step 6: Hard Safety Rejection
        passed_safety = getattr(matching_c, "safety_pass", False)
        if not passed_safety:
            rec = CandidateGapRecord(
                oracle_opportunity=oracle_opp,
                current_mechanism=matching_c.mechanism_family,
                detected=True,
                represented=True,
                patchable=True,
                exact_sim=True,
                safety_pass=False,
                final_decision=f"SAFETY_FAIL: {safety_rej}",
                missing_layer=CausalFailureLayer.SAFETY_REJECTED.value,
                oracle_delta=delta,
                seed=seed,
                step=step,
            )
            self.gap_records.append(rec)
            return CausalFailureLayer.SAFETY_REJECTED, f"Rejected by safety certificate: {safety_rej}", rec

        # Step 7: Economic evaluation rejected
        if cand_delta <= 0:
            rec = CandidateGapRecord(
                oracle_opportunity=oracle_opp,
                current_mechanism=matching_c.mechanism_family,
                detected=True,
                represented=True,
                patchable=True,
                exact_sim=True,
                safety_pass=True,
                final_decision=f"ECONOMIC_FAIL: {cand_delta:.1f}",
                missing_layer=CausalFailureLayer.COUNTERFACTUAL_REJECTED.value,
                oracle_delta=delta,
                seed=seed,
                step=step,
            )
            self.gap_records.append(rec)
            return CausalFailureLayer.COUNTERFACTUAL_REJECTED, f"Evaluated delta {cand_delta:.1f} <= 0", rec

        # Horizon check
        if probe_result.category == OracleCategory.F_HORIZON_INSUFFICIENT:
            rec = CandidateGapRecord(
                oracle_opportunity=oracle_opp,
                current_mechanism=matching_c.mechanism_family,
                detected=True,
                represented=True,
                patchable=True,
                exact_sim=True,
                safety_pass=True,
                final_decision="HORIZON_SHORT",
                missing_layer=CausalFailureLayer.HORIZON_INSUFFICIENT.value,
                oracle_delta=delta,
                seed=seed,
                step=step,
            )
            self.gap_records.append(rec)
            return CausalFailureLayer.HORIZON_INSUFFICIENT, "Advantage visible only at horizon H=36", rec

        # Fallback
        rec = CandidateGapRecord(
            oracle_opportunity=oracle_opp,
            current_mechanism=matching_c.mechanism_family,
            detected=True,
            represented=True,
            patchable=True,
            exact_sim=True,
            safety_pass=True,
            final_decision="ABSTAIN_OTHER",
            missing_layer=CausalFailureLayer.COUNTERFACTUAL_REJECTED.value,
            oracle_delta=delta,
            seed=seed,
            step=step,
        )
        self.gap_records.append(rec)
        return CausalFailureLayer.COUNTERFACTUAL_REJECTED, "AEC abstained despite positive oracle headroom", rec

    def compute_scorecard(
        self,
        all_probes: List[OracleProbeResult],
        all_attributions: List[Tuple[CausalFailureLayer, str, Optional[CandidateGapRecord]]],
    ) -> List[ScorecardRow]:
        """Builds the formal Headroom Scorecard (§30) using objective criteria."""
        categories = [
            ("Detector", [CausalFailureLayer.NOT_DETECTED], 0.9),
            ("Representation", [CausalFailureLayer.NOT_REPRESENTED], 0.8),
            ("Patch", [CausalFailureLayer.NOT_PATCHABLE, CausalFailureLayer.FILTERED], 0.75),
            ("Reconnect", [CausalFailureLayer.RECONNECT_FAILED], 0.7),
            ("Horizon", [CausalFailureLayer.HORIZON_INSUFFICIENT], 0.65),
            ("Economic Evaluation", [CausalFailureLayer.COUNTERFACTUAL_REJECTED], 0.85),
            ("Composition", [CausalFailureLayer.COMPOSITION_ONLY], 0.6),
            ("Opponent", [CausalFailureLayer.OPPONENT_CONTINGENT], 0.5),
            ("Macro", [CausalFailureLayer.MACRO_CONSTRAINED], 0.2),
        ]

        total_positive_states = sum(1 for p in all_probes if p.local_headroom > 0.5)
        total_captured_states = sum(1 for p in all_probes if p.local_headroom > 0.5 and p.aec_committed)
        overall_coverage = total_captured_states / max(1, total_positive_states)

        rows: List[ScorecardRow] = []

        for name, layers, representability in categories:
            matching_deltas: List[float] = []
            matching_captured = 0

            for p, (layer, _, _) in zip(all_probes, all_attributions):
                if layer in layers and p.local_headroom > 0.5:
                    matching_deltas.append(p.local_headroom)
                    if p.aec_committed:
                        matching_captured += 1

            cnt = len(matching_deltas)
            total_headroom = sum(matching_deltas)
            mean_hr = total_headroom / max(1, cnt)
            cov = matching_captured / max(1, cnt) if cnt > 0 else 0.0

            # Priority Score = frequency * measurable_headroom * representability (§30)
            priority = float(cnt) * float(mean_hr) * float(representability)

            rows.append(ScorecardRow(
                gap_class=name,
                states_count=cnt,
                positive_headroom_total=total_headroom,
                mean_headroom=mean_hr,
                current_aec_coverage=cov,
                representability=representability,
                priority_score=priority,
            ))

        return rows
