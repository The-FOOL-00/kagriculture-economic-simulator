# SPDX-License-Identifier: MIT
"""Coupled Patch Representation for AEC (Canonical re-export)."""

from __future__ import annotations

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
]
