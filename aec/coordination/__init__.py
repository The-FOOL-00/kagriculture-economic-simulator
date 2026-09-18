# SPDX-License-Identifier: MIT
"""AEC Multi-Worker Logistics Coordination Package (§5-§25)."""

from aec.coordination.assignment import (
    DisplacementOutcome,
    LaborOpportunityCost,
    WorkerAssignment,
    WorkerSchedule,
    compute_marginal_labor_cost,
)
from aec.coordination.dominance import MultiWorkerDominancePruner
from aec.coordination.scheduler import (
    CoordinationStatus,
    MultiWorkerLogisticsCoordinator,
    WorkerCoordinationPlan,
)
from aec.coordination.task_model import (
    TaskActionFamily,
    TaskDependencyGraph,
    TaskPriority,
    WorkerTask,
)
from aec.coordination.worker_model import (
    STANDARD_WORKER_CAPABILITIES,
    WorkerCapability,
    WorkerState,
    WorkerType,
    extract_farm_workers,
)
def __getattr__(name: str):
    if name in (
        "AbstentionReason",
        "LaborOpportunityAssessment",
        "LaborOpportunityCostEngine",
        "LaborOpportunityRequest",
        "ValuationLevel",
    ):
        from aec.resource import labor_engine
        return getattr(labor_engine, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "AbstentionReason",
    "CoordinationStatus",
    "DisplacementOutcome",
    "LaborOpportunityAssessment",
    "LaborOpportunityCost",
    "LaborOpportunityCostEngine",
    "LaborOpportunityRequest",
    "MultiWorkerDominancePruner",
    "MultiWorkerLogisticsCoordinator",
    "STANDARD_WORKER_CAPABILITIES",
    "TaskActionFamily",
    "TaskDependencyGraph",
    "TaskPriority",
    "ValuationLevel",
    "WorkerAssignment",
    "WorkerCapability",
    "WorkerCoordinationPlan",
    "WorkerSchedule",
    "WorkerState",
    "WorkerTask",
    "WorkerType",
    "compute_marginal_labor_cost",
    "extract_farm_workers",
]
