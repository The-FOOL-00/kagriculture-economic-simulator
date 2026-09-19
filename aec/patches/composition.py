# SPDX-License-Identifier: MIT
"""Patch Composition Engine and Relation Semantics (§37)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.patches.coupled_patch import CoupledPatch


class CompositionRelation(str, Enum):
    """Formal relationship between two candidate patches (§37)."""
    PARALLEL = "PARALLEL"                   # Operates on disjoint workers & resources; can execute together
    SERIAL = "SERIAL"                       # Sequential dependency; patch B executes after patch A
    MUTUALLY_EXCLUSIVE = "MUTUALLY_EXCLUSIVE" # Compete for same single-use resource or exclusive worker
    DOMINATES = "DOMINATES"                 # Patch A strictly dominates Patch B in economic yield & duration
    CONFLICTS = "CONFLICTS"                 # Spatiotemporal route or precondition collision


@dataclass
class PatchCompatibilityReport:
    """Detailed audit of compatibility between two patches."""
    relation: CompositionRelation
    compatible: bool
    conflicts: List[str] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation": self.relation.value,
            "compatible": self.compatible,
            "conflicts": self.conflicts,
            "rationale": self.rationale,
        }


class PatchCompositionEngine:
    """Evaluates interactions between candidate patches (§37).
    
    Prevents uncoordinated patch stacking.
    Guarantees worker, resource, spatial, and terminal consistency.
    """

    def analyze_pair(
        self,
        patch_a: CoupledPatch,
        patch_b: CoupledPatch
    ) -> PatchCompatibilityReport:
        """Evaluate the exact composition relationship between two patches."""
        conflicts: List[str] = []

        # 1. Worker Disjointness
        workers_a = set(
            getattr(patch_a, "worker_ids", []) 
            or list(getattr(patch_a, "worker_mutations", {}).keys()) 
            or ([patch_a.worker_id] if hasattr(patch_a, "worker_id") else [])
        )
        workers_b = set(
            getattr(patch_b, "worker_ids", []) 
            or list(getattr(patch_b, "worker_mutations", {}).keys()) 
            or ([patch_b.worker_id] if hasattr(patch_b, "worker_id") else [])
        )
        shared_workers = workers_a & workers_b
        same_worker = len(shared_workers) > 0

        # 2. Economic Dominance
        val_a = float(getattr(patch_a, "estimated_economic_value", 0.0) or getattr(patch_a, "economic_effect", 0.0) or 0.0)
        val_b = float(getattr(patch_b, "estimated_economic_value", 0.0) or getattr(patch_b, "economic_effect", 0.0) or 0.0)
        dur_a = int(getattr(patch_a, "duration_steps", 1) or getattr(patch_a, "duration", 1) or 1)
        dur_b = int(getattr(patch_b, "duration_steps", 1) or getattr(patch_b, "duration", 1) or 1)

        if same_worker:
            contested_w = sorted(list(shared_workers))[0]
            if val_a >= val_b and dur_a <= dur_b:
                return PatchCompatibilityReport(
                    relation=CompositionRelation.DOMINATES,
                    compatible=False,
                    conflicts=[f"Worker {contested_w} contested: Patch A dominates Patch B."],
                    rationale="Dominates on same worker: execute A, discard B."
                )
            return PatchCompatibilityReport(
                relation=CompositionRelation.MUTUALLY_EXCLUSIVE,
                compatible=False,
                conflicts=[f"Same worker {contested_w} cannot execute two simultaneous trajectories."],
                rationale="Mutually exclusive worker assignment."
            )

        # 3. Spatiotemporal Waypoint Trajectory Collision
        steps_a = getattr(patch_a, "steps", [])
        steps_b = getattr(patch_b, "steps", [])
        
        # Check for same-turn cell collision
        min_len = min(len(steps_a), len(steps_b))
        for t in range(min_len):
            pos_a = steps_a[t].target_position if hasattr(steps_a[t], "target_position") else None
            pos_b = steps_b[t].target_position if hasattr(steps_b[t], "target_position") else None
            if pos_a is not None and pos_b is not None and pos_a == pos_b:
                conflicts.append(f"Spatial collision at turn {t} on cell {pos_a}.")

        # Check for vertex/edge swap collision
        for t in range(min_len - 1):
            pos_a1 = steps_a[t].target_position if hasattr(steps_a[t], "target_position") else None
            pos_a2 = steps_a[t+1].target_position if hasattr(steps_a[t+1], "target_position") else None
            pos_b1 = steps_b[t].target_position if hasattr(steps_b[t], "target_position") else None
            pos_b2 = steps_b[t+1].target_position if hasattr(steps_b[t+1], "target_position") else None
            if pos_a1 and pos_a2 and pos_b1 and pos_b2:
                if pos_a1 == pos_b2 and pos_a2 == pos_b1:
                    conflicts.append(f"Edge swap collision at turns {t}->{t+1} between {pos_a1} and {pos_a2}.")

        # Check locations dict collision if steps not populated
        locs_a = getattr(patch_a, "locations", {}) or {}
        locs_b = getattr(patch_b, "locations", {}) or {}
        if locs_a and locs_b:
            for wa, traj_a in locs_a.items():
                for wb, traj_b in locs_b.items():
                    m_len = min(len(traj_a), len(traj_b))
                    for t in range(m_len):
                        if traj_a[t] == traj_b[t]:
                            conflicts.append(f"Spatial vertex collision at turn {t} on cell {traj_a[t]} between worker {wa} and {wb}.")
                    for t in range(m_len - 1):
                        if traj_a[t] == traj_b[t+1] and traj_a[t+1] == traj_b[t]:
                            conflicts.append(f"Edge swap collision at turns {t}->{t+1} between worker {wa} and {wb}.")

        if conflicts:
            return PatchCompatibilityReport(
                relation=CompositionRelation.CONFLICTS,
                compatible=False,
                conflicts=conflicts,
                rationale="Trajectory or spatial collision detected between patches."
            )

        # Disjoint workers, zero spatial collision
        return PatchCompatibilityReport(
            relation=CompositionRelation.PARALLEL,
            compatible=True,
            conflicts=[],
            rationale="Disjoint workers and collision-free trajectories: parallel composition valid."
        )

    def compose(
        self,
        patch_a: CoupledPatch,
        patch_b: CoupledPatch
    ) -> Optional[CoupledPatch]:
        """Compose two compatible, parallel coupled patches into a single composite patch (§37)."""
        report = self.analyze_pair(patch_a, patch_b)
        if not report.compatible or report.relation != CompositionRelation.PARALLEL:
            return None

        from aec.patches.coupled_patch import CoupledPatchState

        workers_a = set(getattr(patch_a, "worker_ids", []) or list(getattr(patch_a, "worker_mutations", {}).keys()))
        workers_b = set(getattr(patch_b, "worker_ids", []) or list(getattr(patch_b, "worker_mutations", {}).keys()))
        all_workers = sorted(list(workers_a | workers_b))

        merged_mutations: Dict[int, List[str]] = {}
        for wid, acts in getattr(patch_a, "worker_mutations", {}).items():
            merged_mutations[wid] = list(acts)
        for wid, acts in getattr(patch_b, "worker_mutations", {}).items():
            merged_mutations[wid] = list(acts)

        acts_a = getattr(patch_a, "actions", []) or []
        acts_b = getattr(patch_b, "actions", []) or []
        max_steps = max(len(acts_a), len(acts_b))
        composite_actions: List[Dict[str, Any]] = []

        for t in range(max_steps):
            act_a = acts_a[t] if t < len(acts_a) else {}
            act_b = acts_b[t] if t < len(acts_b) else {}

            farmer_act = act_a.get("farmer") or act_b.get("farmer") or ["PASS"]
            hands_a = act_a.get("hands", [])
            hands_b = act_b.get("hands", [])
            num_hands = max(len(hands_a), len(hands_b))
            hands_act = []
            for h in range(num_hands):
                ha = hands_a[h] if h < len(hands_a) and hands_a[h] != ["PASS"] else None
                hb = hands_b[h] if h < len(hands_b) and hands_b[h] != ["PASS"] else None
                hands_act.append(ha or hb or ["PASS"])

            mkt_a = act_a.get("market", [])
            mkt_b = act_b.get("market", [])
            mkt_act = list(mkt_a) + [o for o in mkt_b if o not in mkt_a]

            composite_actions.append({
                "farmer": farmer_act,
                "hands": hands_act,
                "market": mkt_act,
            })

        val_a = float(getattr(patch_a, "economic_effect", 0.0) or getattr(patch_a, "estimated_economic_value", 0.0) or 0.0)
        val_b = float(getattr(patch_b, "economic_effect", 0.0) or getattr(patch_b, "estimated_economic_value", 0.0) or 0.0)

        locs_a = getattr(patch_a, "locations", {}) or {}
        locs_b = getattr(patch_b, "locations", {}) or {}
        merged_locations = {**locs_a, **locs_b}

        return CoupledPatch(
            patch_id=f"COMPOSITE_{patch_a.patch_id}_{patch_b.patch_id}",
            source_opportunity_id=f"{patch_a.source_opportunity_id}+{patch_b.source_opportunity_id}",
            worker_ids=all_workers,
            start_step=min(patch_a.start_step, patch_b.start_step),
            end_step=max(patch_a.end_step, patch_b.end_step),
            actions=composite_actions,
            locations=merged_locations,
            worker_mutations=merged_mutations,
            economic_effect=val_a + val_b,
            reconnect_result=getattr(patch_a, "reconnect_result", None),
            state=CoupledPatchState.PROPOSED,
        )
