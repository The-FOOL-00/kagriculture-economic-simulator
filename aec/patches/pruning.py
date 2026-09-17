# SPDX-License-Identifier: MIT
"""Static Pruning and Feasibility Filtering for Candidate Patches."""

from __future__ import annotations

from typing import Dict, List

from aec.config import BOARD_SIZE, MAX_MARKET_ORDERS, MOVES
from aec.ir.economic_state import EconomicState
from aec.patches.patch import CoupledPatch


def is_patch_statically_feasible(
    patch: CoupledPatch,
    econ_state: EconomicState
) -> bool:
    """Fast, cheap static rejection of obviously infeasible or illegal patches."""
    # 1. Market order limits
    if patch.market_mutations is not None:
        if len(patch.market_mutations) > MAX_MARKET_ORDERS:
            return False
        for order in patch.market_mutations:
            if not isinstance(order, (list, tuple)) or not order:
                return False
            op = order[0]
            if op in ("SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL"):
                if len(order) < 3:
                    return False
                try:
                    qty = int(order[2])
                    if qty <= 0:
                        return False
                except (TypeError, ValueError):
                    return False

    # 2. Worker move bounds
    for worker_id, cmd in patch.worker_mutations.items():
        worker = econ_state.workers.get_worker(worker_id)
        if worker is None:
            return False
        if cmd and cmd[0] in MOVES:
            dx, dy = MOVES[cmd[0]]
            x, y = worker.position
            if not (0 <= x + dx < BOARD_SIZE and 0 <= y + dy < BOARD_SIZE):
                return False  # would walk off board

    return True


def prune_patches(
    patches: List[CoupledPatch],
    econ_state: EconomicState,
    max_candidates: int = 8
) -> List[CoupledPatch]:
    """Prune patches down to statically feasible subset, capped at budget."""
    feasible: List[CoupledPatch] = []
    seen_ids = set()

    for p in patches:
        if p.patch_id in seen_ids:
            continue
        if is_patch_statically_feasible(p, econ_state):
            feasible.append(p)
            seen_ids.add(p.patch_id)
            if len(feasible) >= max_candidates:
                break

    return feasible
