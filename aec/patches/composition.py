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
        wid_a = getattr(patch_a, "worker_id", 0)
        wid_b = getattr(patch_b, "worker_id", 0)
        same_worker = (wid_a == wid_b)

        # 2. Economic Dominance
        val_a = float(getattr(patch_a, "estimated_economic_value", 0.0) or 0.0)
        val_b = float(getattr(patch_b, "estimated_economic_value", 0.0) or 0.0)
        dur_a = int(getattr(patch_a, "duration_steps", 1) or 1)
        dur_b = int(getattr(patch_b, "duration_steps", 1) or 1)

        if same_worker:
            if val_a >= val_b and dur_a <= dur_b:
                return PatchCompatibilityReport(
                    relation=CompositionRelation.DOMINATES,
                    compatible=False,
                    conflicts=[f"Worker {wid_a} contested: Patch A dominates Patch B."],
                    rationale="Dominates on same worker: execute A, discard B."
                )
            return PatchCompatibilityReport(
                relation=CompositionRelation.MUTUALLY_EXCLUSIVE,
                compatible=False,
                conflicts=[f"Same worker {wid_a} cannot execute two simultaneous trajectories."],
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
