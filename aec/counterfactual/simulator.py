# SPDX-License-Identifier: MIT
"""Isolated Forward Counterfactual Simulator (§10, §17, §18)."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from aec.config import (
    BOARD_SIZE,
    CROP_SEED_PRICE,
    PRODUCTS,
    SHED_CAPACITY,
    TURNS_PER_DAY,
)
from aec.counterfactual.opponent_pressure import OpponentPressureModel
from aec.counterfactual.v3_continuation import (
    V3ContinuationPolicy,
    restore_v3_state,
    snapshot_v3_state,
)
from aec.ir.economic_state import EconomicState
from aec.patches.patch import CoupledPatch

# Import verified unit & market physics
try:
    from extracted_agents.dmitrii_lb2800.unit_model import (
        _apply_unit_action,
        _decay_plants,
    )
except ImportError:
    import os
    import sys
    _REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sys.path.insert(0, _REPO)
    from extracted_agents.dmitrii_lb2800.unit_model import (
        _apply_unit_action,
        _decay_plants,
    )

try:
    from config import compute_market_price, fib_hire_cost, FARMER_MOVES
except ImportError:
    import os
    import sys
    _REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if _REPO not in sys.path:
        sys.path.insert(0, _REPO)
    from config import compute_market_price, fib_hire_cost, FARMER_MOVES

from aec.ir.market_state import BASE_PRICES, TOWN_SHOP_CONSUMPTION


class CounterfactualFidelityLevel(Enum):
    """Fidelity classification for counterfactual evaluations (§14)."""
    VERIFIED = "VERIFIED"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    FAILED = "FAILED"


@dataclass
class SimulationOutcome:
    """Complete economic record of an isolated counterfactual evaluation."""
    candidate_final_money: float
    baseline_final_money: float
    delta_our_money: float
    
    candidate_opp_final_money: float
    baseline_opp_final_money: float
    delta_opponent_money: float
    
    delta_terminal_margin: float
    
    candidate_overflow_units: int
    candidate_sold: Dict[str, int]
    baseline_sold: Dict[str, int]
    
    intermediate_solvency_ok: bool
    horizon: int

    baseline_trace: Optional[List[Dict[str, Any]]] = None
    candidate_trace: Optional[List[Dict[str, Any]]] = None
    spatial_consistency_ok: bool = True
    desynchronization_reason: str = ""

    # Counterfactual fidelity certification (§14)
    fidelity: str = "VERIFIED"
    fidelity_reasons: List[str] = field(default_factory=list)

    # Resource and Feed Security Invariants (§5, §6, §17)
    feed_security_ok: bool = True
    feed_deficit_units: int = 0

    # Phase 016 Macro-Aware Continuation Invariants (§5, §15, §16)
    macro_escalated: bool = False
    macro_regime_type: str = "NONE"
    macro_escalation_reason: str = ""
    first_divergence_turn: Optional[int] = None
    direct_intervention_effect: float = 0.0
    macro_induced_continuation_delta: float = 0.0
    executed_baseline_actions: Optional[List[Dict[str, Any]]] = None
    executed_candidate_actions: Optional[List[Dict[str, Any]]] = None


class ShadowRolloutState:
    """Isolated memory container for forward simulation."""

    def __init__(self, econ_state: EconomicState):
        self.step = econ_state.step
        self.day = econ_state.day
        self.money = float(econ_state.farm.cash)
        self.opp_money = float(econ_state.opponent.observed_cash)
        
        # Clone farm tiles, shed, inventories
        self.tiles = copy.deepcopy(econ_state.farm.tiles)
        self.shed = copy.deepcopy(econ_state.farm.shed_inventory)
        self.seeds = copy.deepcopy(econ_state.farm.seeds)
        
        # Workers: positions and inventories
        self.farmer_pos = list(econ_state.workers.workers[0].position)
        self.hands_pos = [list(w.position) for w in econ_state.workers.workers[1:]]
        self.inventories = [copy.deepcopy(w.cargo) for w in econ_state.workers.workers]
        
        # Market state
        self.market_prices = copy.deepcopy(econ_state.market.current_prices)
        self.market_inv = copy.deepcopy(econ_state.market.market_inventory)
        self.unlocked_shops = list(econ_state.market.unlocked_shops)
        
        # Tracking
        self.overflow_units = 0
        self.cumulative_sold: Dict[str, int] = {p: 0 for p in PRODUCTS}
        self.rows: List[Dict[str, Any]] = []
        self.hires_today = int(getattr(econ_state.farm, "hires_today", 0) or 0)
        self.spatial_desynchronized: bool = False
        self.desynchronization_reason: str = ""
        self.worker_positions_history: List[List[List[int]]] = []
        self.feed_security_ok: bool = True
        self.feed_deficit_units: int = 0
        self.escaped_animals_count: int = 0

    def get_farm_dict(self) -> Dict[str, Any]:
        return {
            "money": self.money,
            "farmer": self.farmer_pos,
            "hands": self.hands_pos,
            "tiles": self.tiles,
            "hires_today": self.hires_today,
        }

    def get_private_dict(self) -> Dict[str, Any]:
        return {
            "shed": self.shed,
            "seeds": self.seeds,
            "inventories": self.inventories,
        }


def execute_market_lockstep(
    rollout: ShadowRolloutState,
    own_orders: List[List[Any]],
    opp_orders: List[List[Any]]
) -> None:
    """Execute own orders against opponent orders in lockstep per-unit semantics matching sim.hpp."""
    own_q = list(own_orders)[:10]
    opp_q = list(opp_orders)[:10]
    max_len = max(len(own_q), len(opp_q))

    for i in range(max_len):
        # 1. Atomic orders resolve once in player order (HIRE, BUY_LAND)
        if i < len(own_q):
            o = own_q[i]
            if isinstance(o, (list, tuple)) and o and o[0] == "HIRE":
                h_cost = float(fib_hire_cost(rollout.hires_today))
                if rollout.money >= h_cost:
                    rollout.money -= h_cost
                    rollout.hires_today += 1
            elif isinstance(o, (list, tuple)) and o and o[0] == "BUY_LAND":
                pass

        if i < len(opp_q):
            o = opp_q[i]
            if isinstance(o, (list, tuple)) and o and o[0] == "HIRE":
                pass

        # 2. Per-unit lockstep loop for goods orders at slot i (matching sim.hpp:578-617)
        own_live = False
        own_op, own_item, own_rem = None, None, 0
        if i < len(own_q):
            o = own_q[i]
            if isinstance(o, (list, tuple)) and len(o) >= 3:
                own_op, own_item = o[0], o[1]
                try:
                    own_rem = int(o[2])
                except (ValueError, TypeError):
                    own_rem = 0
                own_live = own_rem > 0 and own_op in ("SELL", "BUY_PRODUCT", "BUY_SEED")

        opp_live = False
        opp_op, opp_item, opp_rem = None, None, 0
        if i < len(opp_q):
            o = opp_q[i]
            if isinstance(o, (list, tuple)) and len(o) >= 3:
                opp_op, opp_item = o[0], o[1]
                try:
                    opp_rem = int(o[2])
                except (ValueError, TypeError):
                    opp_rem = 0
                opp_live = opp_rem > 0 and opp_op in ("SELL", "BUY_PRODUCT", "BUY_SEED")

        while own_live or opp_live:
            # PHASE 1: QUOTE BOTH PLAYERS FROM IDENTICAL PRE-COMMIT INVENTORY SNAPSHOT (sim.hpp:578-597)
            q0_ok = False
            q0_op = own_op
            q0_item = own_item
            q0_price = 0
            if own_live and own_rem > 0:
                if own_op == "SELL":
                    avail = rollout.shed.get(own_item, 0)
                    if avail > 0:
                        cur_inv = rollout.market_inv.get(own_item, 10000)
                        q0_price = compute_market_price(own_item, cur_inv)
                        q0_ok = True
                    else:
                        own_live = False
                elif own_op == "BUY_PRODUCT":
                    cur_inv = rollout.market_inv.get(own_item, 10000)
                    q0_price = compute_market_price(own_item, cur_inv - 1)
                    if rollout.money >= q0_price and sum(rollout.shed.values()) < SHED_CAPACITY and cur_inv > 0:
                        q0_ok = True
                    else:
                        own_live = False
                elif own_op == "BUY_SEED":
                    seed_cost = CROP_SEED_PRICE.get(own_item, 20)
                    if rollout.money >= seed_cost:
                        q0_price = seed_cost
                        q0_ok = True
                    else:
                        own_live = False

            # Player 1 (Opponent) quote
            q1_ok = False
            q1_op = opp_op
            q1_item = opp_item
            q1_price = 0
            if opp_live and opp_rem > 0:
                if opp_op == "SELL":
                    cur_inv = rollout.market_inv.get(opp_item, 10000)
                    q1_price = compute_market_price(opp_item, cur_inv)
                    q1_ok = True
                elif opp_op == "BUY_PRODUCT":
                    cur_inv = rollout.market_inv.get(opp_item, 10000)
                    q1_price = compute_market_price(opp_item, cur_inv - 1)
                    if rollout.opp_money >= q1_price and cur_inv > 0:
                        q1_ok = True
                    else:
                        opp_live = False
                elif opp_op == "BUY_SEED":
                    seed_cost = CROP_SEED_PRICE.get(opp_item, 20)
                    if rollout.opp_money >= seed_cost:
                        q1_price = seed_cost
                        q1_ok = True
                    else:
                        opp_live = False

            if not q0_ok and not q1_ok:
                break

            # PHASE 2: COMMIT QUOTED UNITS (sim.hpp:598-617)
            committed_any = False

            # Player 0 unit commit
            if q0_ok:
                if q0_op == "SELL":
                    avail = rollout.shed.get(q0_item, 0)
                    if avail > 0:
                        rollout.money += q0_price
                        rollout.shed[q0_item] -= 1
                        rollout.cumulative_sold[q0_item] += 1
                        if q0_price > 1:
                            rollout.market_inv[q0_item] = rollout.market_inv.get(q0_item, 10000) + 1
                        rollout.market_prices[q0_item] = compute_market_price(q0_item, rollout.market_inv[q0_item])
                        own_rem -= 1
                        committed_any = True
                    else:
                        own_live = False
                elif q0_op == "BUY_PRODUCT":
                    cur_inv = rollout.market_inv.get(q0_item, 10000)
                    if rollout.money >= q0_price and sum(rollout.shed.values()) < SHED_CAPACITY and cur_inv > 0:
                        rollout.money -= q0_price
                        rollout.shed[q0_item] = rollout.shed.get(q0_item, 0) + 1
                        rollout.market_inv[q0_item] = cur_inv - 1
                        rollout.market_prices[q0_item] = compute_market_price(q0_item, rollout.market_inv[q0_item])
                        own_rem -= 1
                        committed_any = True
                    else:
                        own_live = False
                elif q0_op == "BUY_SEED":
                    if rollout.money >= q0_price:
                        rollout.money -= q0_price
                        rollout.seeds[q0_item] = rollout.seeds.get(q0_item, 0) + 1
                        own_rem -= 1
                        committed_any = True
                    else:
                        own_live = False

                if own_rem <= 0:
                    own_live = False

            # Player 1 unit commit
            if q1_ok:
                if q1_op == "SELL":
                    rollout.opp_money += q1_price
                    if q1_price > 1:
                        rollout.market_inv[q1_item] = rollout.market_inv.get(q1_item, 10000) + 1
                    rollout.market_prices[q1_item] = compute_market_price(q1_item, rollout.market_inv[q1_item])
                    opp_rem -= 1
                    committed_any = True
                elif q1_op == "BUY_PRODUCT":
                    cur_inv = rollout.market_inv.get(q1_item, 10000)
                    if rollout.opp_money >= q1_price and cur_inv > 0:
                        rollout.opp_money -= q1_price
                        rollout.market_inv[q1_item] = cur_inv - 1
                        rollout.market_prices[q1_item] = compute_market_price(q1_item, rollout.market_inv[q1_item])
                        opp_rem -= 1
                        committed_any = True
                    else:
                        opp_live = False
                elif q1_op == "BUY_SEED":
                    if rollout.opp_money >= q1_price:
                        rollout.opp_money -= q1_price
                        opp_rem -= 1
                        committed_any = True
                    else:
                        opp_live = False

                if opp_rem <= 0:
                    opp_live = False

            if not committed_any:
                break

    # Town consumption tick every 4 steps
    if rollout.step % 4 == 0 and rollout.unlocked_shops:
        for shop in rollout.unlocked_shops:
            for it, q in TOWN_SHOP_CONSUMPTION.get(shop, ()):
                if it in rollout.market_inv:
                    rollout.market_inv[it] = max(0, rollout.market_inv[it] - q)
                    rollout.market_prices[it] = compute_market_price(it, rollout.market_inv[it])


def simulate_rollout(
    econ_state: EconomicState,
    initial_action: Dict[str, Any],
    horizon: int,
    opp_model: OpponentPressureModel,
    continuation_actions: Optional[List[Dict[str, Any]]] = None,
    trace_log: Optional[List[Dict[str, Any]]] = None,
    baseline_positions: Optional[List[List[List[int]]]] = None,
    spliced_workers: Optional[Set[int]] = None,
    reconnect_result: Optional[Any] = None,
    v3_policy: Optional[Any] = None,
    executed_actions: Optional[List[Dict[str, Any]]] = None,
    player: int = 0,
) -> ShadowRolloutState:
    """Run an isolated forward rollout starting with initial_action at step 0, followed by continuation."""
    rollout = ShadowRolloutState(econ_state)
    n_workers = len(rollout.inventories)
    tile_ops = {
        "PLANT", "WATER", "HARVEST", "FERTILIZE", "BUILD_COOP", "BUILD_PASTURE",
        "DROP", "PICKUP", "PLACE", "FEED", "CARE", "COLLECT_FERTILIZER"
    }

    for offset in range(horizon):
        cur_step = econ_state.step + offset
        if cur_step >= 720:
            break
        rollout.step = cur_step
        rollout.day = cur_step // TURNS_PER_DAY
        
        # Step action: initial_action on offset 0; dynamic V3 or continuation thereafter
        if offset == 0:
            action = copy.deepcopy(initial_action)
        else:
            if v3_policy is not None:
                action = v3_policy.step_action(rollout, player=player)
            elif continuation_actions and (offset - 1) < len(continuation_actions):
                action = copy.deepcopy(continuation_actions[offset - 1])
            else:
                action = {"farmer": ["PASS"], "hands": [["PASS"] for _ in range(n_workers - 1)], "market": []}

        if executed_actions is not None:
            executed_actions.append(copy.deepcopy(action))

        # 1. Apply worker movements and tasks
        farm_dict = rollout.get_farm_dict()
        private_dict = rollout.get_private_dict()
        
        pre_market_shed = dict(rollout.shed)
        commands = [action.get("farmer", ["PASS"])] + (action.get("hands", []) or [])
        while len(commands) < n_workers:
            commands.append(["PASS"])
        commands = commands[:n_workers]

        # Spatial consistency check against baseline worker trajectory
        if baseline_positions is not None and offset >= 1 and (offset - 1) < len(baseline_positions):
            expected_positions = baseline_positions[offset - 1]
            for actor in range(n_workers):
                # If actor is managed by route splicing, check route continuity instead of raw baseline positions
                if spliced_workers is not None and actor in spliced_workers:
                    cmd_actor = commands[actor] if actor < len(commands) and commands[actor] else ["PASS"]
                    cur_pos = farm_dict["farmer"] if actor == 0 else (farm_dict["hands"][actor - 1] if actor - 1 < len(farm_dict["hands"]) else None)
                    if cur_pos is not None and not (0 <= cur_pos[0] < BOARD_SIZE and 0 <= cur_pos[1] < BOARD_SIZE):
                        rollout.spatial_desynchronized = True
                        rollout.desynchronization_reason = f"Spliced Worker {actor} moved out of bounds: {cur_pos}"
                        commands[actor] = ["PASS"]
                    continue

                cur_pos = farm_dict["farmer"] if actor == 0 else (farm_dict["hands"][actor - 1] if actor - 1 < len(farm_dict["hands"]) else None)
                exp_pos = expected_positions[actor] if actor < len(expected_positions) else None
                if cur_pos != exp_pos and exp_pos is not None:
                    cmd_actor = commands[actor] if actor < len(commands) and commands[actor] else ["PASS"]
                    op_actor = cmd_actor[0] if cmd_actor else "PASS"
                    if op_actor in tile_ops or op_actor in FARMER_MOVES:
                        rollout.spatial_desynchronized = True
                        if not rollout.desynchronization_reason:
                            rollout.desynchronization_reason = (
                                f"Worker {actor} spatially desynchronized at offset {offset}: "
                                f"expected {exp_pos}, actual {cur_pos}; cannot execute {op_actor}"
                            )
                        commands[actor] = ["PASS"]

        for actor in range(n_workers):
            cmd = commands[actor] if actor < len(commands) and commands[actor] else ["PASS"]
            watch_drop = bool(cmd and cmd[0] == "DROP")
            before_inv_sum = sum(private_dict["inventories"][actor].values()) if watch_drop else 0
            before_shed_sum = sum(private_dict["shed"].values()) if watch_drop else 0

            try:
                _apply_unit_action(
                    farm_dict,
                    private_dict,
                    actor,
                    cmd,
                    BOARD_SIZE,
                    rollout.day,
                    TURNS_PER_DAY,
                    SHED_CAPACITY
                )
            except Exception:
                pass  # Ignore invalid worker step in simulation

            if watch_drop:
                after_shed_sum = sum(private_dict["shed"].values())
                after_inv_sum = sum(private_dict["inventories"][actor].values())
                shed_delta = max(0, after_shed_sum - before_shed_sum)
                inv_dropped = max(0, before_inv_sum - after_inv_sum)
                lost_units = max(0, inv_dropped - shed_delta)
                if lost_units > 0:
                    rollout.overflow_units += lost_units

        # Synchronize worker positions back to rollout state
        rollout.farmer_pos = list(farm_dict["farmer"])
        rollout.hands_pos = [list(p) for p in farm_dict.get("hands", [])]
        rollout.worker_positions_history.append([list(farm_dict["farmer"])] + [list(p) for p in farm_dict.get("hands", [])])

        # 2. Market execution under opponent pressure
        opp_market = opp_model.generate_simulated_opponent_market(econ_state.step, offset)
        execute_market_lockstep(rollout, action.get("market", []), opp_market)

        # 3. Plant decay
        try:
            _decay_plants(farm_dict, cur_step)
        except Exception:
            pass

        # 3b. Daily livestock refresh and feed security tracking (§5, §6)
        if (cur_step + 1) % TURNS_PER_DAY == 0:
            for row in farm_dict.get("tiles", []):
                for tile in row:
                    if isinstance(tile, dict) and "animal" in tile:
                        if tile.get("fed_today"):
                            tile["consecutive_unfed"] = 0
                        else:
                            tile["consecutive_unfed"] = tile.get("consecutive_unfed", 0) + 1
                            rollout.feed_deficit_units += 1
                            if tile["consecutive_unfed"] >= 2:
                                rollout.escaped_animals_count += 1
                                rollout.feed_security_ok = False
                        tile["fed_today"] = False
                        tile["cared_today"] = False

        # 4. Record row
        row_data = {
            "step": cur_step,
            "pre_market_shed": pre_market_shed,
            "post_market_shed": dict(rollout.shed),
            "money": rollout.money,
            "opp_money": rollout.opp_money,
        }
        rollout.rows.append(row_data)

        # 5. Record trace if requested
        if trace_log is not None:
            trace_entry = {
                "offset": offset,
                "step": cur_step,
                "worker_positions": [list(farm_dict["farmer"])] + [list(p) for p in farm_dict.get("hands", [])],
                "worker_actions": commands,
                "inventory": copy.deepcopy(private_dict["inventories"]),
                "shed": dict(private_dict["shed"]),
                "cash": rollout.money,
                "opp_cash": rollout.opp_money,
                "market_prices": dict(rollout.market_prices),
                "market_inventory": dict(rollout.market_inv),
                "opponent_pressure": {p: opp_model.state.sale_pressure.get(p, 0.0) for p in PRODUCTS} if opp_model.state else {},
            }
            trace_log.append(trace_entry)

    return rollout


class CounterfactualSimulator:
    """Evaluates candidate patches against baseline under opponent pressure with full continuation."""

    def evaluate(
        self,
        candidate_patch: CoupledPatch,
        baseline_action: Dict[str, Any],
        econ_state: EconomicState,
        horizon: int,
        continuation_trajectory: Optional[List[Dict[str, Any]]] = None,
        trace: bool = False,
        opponent_mode: str = "CALIBRATED_ESTIMATE",
        v3_agent_callable: Optional[Any] = None,
        macro_escalated: bool = False,
        macro_escalation_reason: str = "",
        macro_regime_type: str = "NONE",
        macro_invariant: bool = False,
        backbone: Optional[Any] = None,
    ) -> SimulationOutcome:
        opp_model = OpponentPressureModel(
            opponent_state=econ_state.opponent,
            mode=opponent_mode
        )

        use_backbone = bool(macro_escalated and backbone is not None and hasattr(backbone, "create_continuation_policy"))
        use_dynamic_v3 = bool(macro_escalated and v3_agent_callable is not None and not use_backbone)

        if use_backbone:
            backbone_snap = backbone.snapshot_state()
            v3_snap = {}
        elif use_dynamic_v3:
            v3_snap = snapshot_v3_state(v3_agent_callable)
            backbone_snap = {}
        else:
            backbone_snap = {}
            v3_snap = {}

        # 1. Simulate Baseline Future
        baseline_trace: Optional[List[Dict[str, Any]]] = [] if trace else None
        base_executed_actions: List[Dict[str, Any]] = []

        if use_backbone:
            backbone.restore_state(backbone_snap)
            base_policy = backbone.create_continuation_policy()
        elif use_dynamic_v3:
            restore_v3_state(v3_agent_callable, v3_snap)
            base_policy = V3ContinuationPolicy(v3_agent_callable)
        else:
            base_policy = None

        baseline_rollout = simulate_rollout(
            econ_state=econ_state,
            initial_action=baseline_action,
            horizon=horizon,
            opp_model=opp_model,
            continuation_actions=continuation_trajectory,
            trace_log=baseline_trace,
            v3_policy=base_policy,
            executed_actions=base_executed_actions,
            player=econ_state.player,
        )

        # 2. Simulate Candidate Future
        cand_action = candidate_patch.apply(baseline_action)
        candidate_trace: Optional[List[Dict[str, Any]]] = [] if trace else None
        cand_executed_actions: List[Dict[str, Any]] = []
        
        cand_continuation = (
            candidate_patch.spliced_continuation
            if getattr(candidate_patch, "spliced_continuation", None) is not None
            else continuation_trajectory
        )
        spliced_workers: Optional[Set[int]] = None
        reconnect_res = getattr(candidate_patch, "reconnect_result", None)
        if reconnect_res is not None:
            spliced_workers = getattr(reconnect_res, "affected_workers", None)
        elif getattr(candidate_patch, "spliced_continuation", None) is not None:
            spliced_workers = set(candidate_patch.worker_mutations.keys())

        if use_backbone:
            backbone.restore_state(backbone_snap)
            if macro_invariant:
                cand_policy = None
                cand_continuation = base_executed_actions[1:] if len(base_executed_actions) > 1 else []
            else:
                cand_policy = backbone.create_continuation_policy()
        elif use_dynamic_v3:
            restore_v3_state(v3_agent_callable, v3_snap)
            if macro_invariant:
                # Diagnostic mode: hold out macro regime shift by replaying baseline actions
                cand_policy = None
                cand_continuation = base_executed_actions[1:] if len(base_executed_actions) > 1 else []
            else:
                cand_policy = V3ContinuationPolicy(v3_agent_callable)
        else:
            cand_policy = None

        candidate_rollout = simulate_rollout(
            econ_state=econ_state,
            initial_action=cand_action,
            horizon=horizon,
            opp_model=opp_model,
            continuation_actions=cand_continuation,
            trace_log=candidate_trace,
            baseline_positions=baseline_rollout.worker_positions_history,
            spliced_workers=spliced_workers,
            reconnect_result=reconnect_res,
            v3_policy=cand_policy,
            executed_actions=cand_executed_actions,
            player=econ_state.player,
        )

        # Restore state to ensure 100% pure isolation from live game
        if use_backbone:
            backbone.restore_state(backbone_snap)
        elif use_dynamic_v3:
            restore_v3_state(v3_agent_callable, v3_snap)

        # 3. Detect Action Divergence Turn
        first_div_turn: Optional[int] = None
        if base_executed_actions and cand_executed_actions:
            for offset_idx in range(min(len(base_executed_actions), len(cand_executed_actions))):
                if base_executed_actions[offset_idx] != cand_executed_actions[offset_idx]:
                    first_div_turn = econ_state.step + offset_idx
                    break

        # 4. Compute Deltas & Margins (Total Economic Wealth Accounting)
        prices = econ_state.market.current_prices if hasattr(econ_state, "market") else {}
        
        cand_shed_val = sum(q * float(prices.get(p, 20.0)) for p, q in candidate_rollout.shed.items())
        base_shed_val = sum(q * float(prices.get(p, 20.0)) for p, q in baseline_rollout.shed.items())
        
        cand_inv_val = sum(sum(q * float(prices.get(p, 20.0)) for p, q in inv.items()) for inv in candidate_rollout.inventories)
        base_inv_val = sum(sum(q * float(prices.get(p, 20.0)) for p, q in inv.items()) for inv in baseline_rollout.inventories)
        
        cand_total_wealth = candidate_rollout.money + cand_shed_val + cand_inv_val
        base_total_wealth = baseline_rollout.money + base_shed_val + base_inv_val
        
        delta_our_money = candidate_rollout.money - baseline_rollout.money
        delta_opp_money = candidate_rollout.opp_money - baseline_rollout.opp_money
        
        cand_margin = cand_total_wealth - candidate_rollout.opp_money
        base_margin = base_total_wealth - baseline_rollout.opp_money
        delta_terminal_margin = cand_margin - base_margin

        # Direct intervention effect vs macro continuation delta (§16)
        cand_money_step0 = candidate_rollout.rows[0]["money"] if candidate_rollout.rows else candidate_rollout.money
        base_money_step0 = baseline_rollout.rows[0]["money"] if baseline_rollout.rows else baseline_rollout.money
        direct_effect = cand_money_step0 - base_money_step0
        macro_continuation_delta = delta_terminal_margin - direct_effect

        # 5. Intermediate Solvency Check
        intermediate_solvency_ok = True
        for offset in range(min(len(candidate_rollout.rows), len(baseline_rollout.rows))):
            cand_pre = candidate_rollout.rows[offset]["pre_market_shed"]
            for p in PRODUCTS:
                if cand_pre.get(p, 0) < 0:
                    intermediate_solvency_ok = False
                    break

        # 6. Counterfactual Fidelity Certification (§14)
        fidelity = CounterfactualFidelityLevel.VERIFIED.value
        fidelity_reasons: List[str] = []

        if not intermediate_solvency_ok:
            fidelity = CounterfactualFidelityLevel.FAILED.value
            fidelity_reasons.append("Intermediate shed solvency breached during rollout")

        if not candidate_rollout.feed_security_ok:
            fidelity = CounterfactualFidelityLevel.FAILED.value
            fidelity_reasons.append(
                f"Feed security breached during rollout: {candidate_rollout.escaped_animals_count} animal(s) escaped, "
                f"{candidate_rollout.feed_deficit_units} deficit units"
            )

        if candidate_rollout.spatial_desynchronized:
            fidelity = CounterfactualFidelityLevel.PARTIAL.value
            fidelity_reasons.append(candidate_rollout.desynchronization_reason)

        return SimulationOutcome(
            candidate_final_money=candidate_rollout.money,
            baseline_final_money=baseline_rollout.money,
            delta_our_money=delta_our_money,
            candidate_opp_final_money=candidate_rollout.opp_money,
            baseline_opp_final_money=baseline_rollout.opp_money,
            delta_opponent_money=delta_opp_money,
            delta_terminal_margin=delta_terminal_margin,
            candidate_overflow_units=candidate_rollout.overflow_units,
            candidate_sold=candidate_rollout.cumulative_sold,
            baseline_sold=baseline_rollout.cumulative_sold,
            intermediate_solvency_ok=intermediate_solvency_ok,
            horizon=horizon,
            baseline_trace=baseline_trace,
            candidate_trace=candidate_trace,
            spatial_consistency_ok=not candidate_rollout.spatial_desynchronized,
            desynchronization_reason=candidate_rollout.desynchronization_reason,
            fidelity=fidelity,
            fidelity_reasons=fidelity_reasons,
            feed_security_ok=candidate_rollout.feed_security_ok,
            feed_deficit_units=candidate_rollout.feed_deficit_units,
            macro_escalated=macro_escalated,
            macro_regime_type=macro_regime_type,
            macro_escalation_reason=macro_escalation_reason,
            first_divergence_turn=first_div_turn,
            direct_intervention_effect=direct_effect,
            macro_induced_continuation_delta=macro_continuation_delta,
            executed_baseline_actions=base_executed_actions if (use_backbone or use_dynamic_v3) else None,
            executed_candidate_actions=cand_executed_actions if (use_backbone or use_dynamic_v3) else None,
        )
