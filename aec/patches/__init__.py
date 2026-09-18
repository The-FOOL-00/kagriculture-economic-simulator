# SPDX-License-Identifier: MIT
"""AEC Coupled Patches and Candidate Generation."""

from aec.patches.coupled_patch import (
    CoupledPatch,
    CoupledPatchRequest,
    CoupledPatchResult,
    CoupledPatchState,
    CoupledPatchStep,
    PatchPostcondition,
    PatchPrecondition,
    PatchStateDelta,
    TrajectoryPreservationCertificate,
)
from aec.patches.coupled_patch_engine import CoupledPatchEngine
from aec.patches.generator import PatchGenerator, reorder_frontload
from aec.patches.harvest_patch import HarvestCoupledPatchGenerator
from aec.patches.pruning import is_patch_statically_feasible, prune_patches

__all__ = [
    "CoupledPatch",
    "CoupledPatchRequest",
    "CoupledPatchResult",
    "CoupledPatchState",
    "CoupledPatchStep",
    "PatchPrecondition",
    "PatchPostcondition",
    "PatchStateDelta",
    "TrajectoryPreservationCertificate",
    "CoupledPatchEngine",
    "HarvestCoupledPatchGenerator",
    "PatchGenerator",
    "reorder_frontload",
    "prune_patches",
    "is_patch_statically_feasible",
]
