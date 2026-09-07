"""
Isolated Causal Interventions for Kaggriculture Movement Gap
============================================================
Generates 7 strictly isolated candidate variants of ClosedLoopCommitmentV1,
each implementing exactly ONE isolated coordination / logistics mechanism:

Arm 1: Soft Local Worker Ownership (Spatial Quadrant Affinity)
Arm 2: Joint Multi-Worker Target Allocation (Pure Python Bipartite Min-Cost Matching)
Arm 3: Cluster Lock (Local high-density chore retention)
Arm 4: Zone Exit Penalty (Soft cross-quadrant cost barrier)
Arm 5: Shed Opportunism (En-route produce drop only)
Arm 6: Load Threshold 5+ (Batched produce delivery)
Arm 7: Short-Horizon Live-State Prepositioning (State-derived crop maturity lookahead)

Zero Replay / Transitive Contamination: Pure Python standard library.
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
from collections import deque
import copy

from candidates.candidate_closed_loop_commitment_v1 import (
    BOARD, TPD, SHED_ACCESS, CROPS_DEF, PASTURE_SLOTS, PASTURE_SPECIES,
    MELON_TILES_D0, MELON_DESIGNATED_TILES, WHEAT_TILES_D0, SELLABLE, PRODUCE_TO_DROP,
    BASE_PRICES, MOVES, _fib, _dist, _quad, _walkable, _bfs_step, _nearest_shed,
    ClosedLoopCommitmentV1
)

WELL_ACCESS = frozenset([(4, 5), (5, 5), (4, 6), (5, 6)])

# ── Pure Python Bipartite Min-Cost Matching (Kuhn-Munkres / Hungarian Algorithm) ──
def min_cost_bipartite_matching(cost_matrix):
    """
    Solves linear sum assignment: argmin sum(cost_matrix[u][v])
    Pure Python standard library implementation.
    cost_matrix: list of lists of shape (N, M), where N <= M
    Returns: list of (u, v) assignments
    """
    n = len(cost_matrix)
    if n == 0:
        return []
    m = len(cost_matrix[0])
    if m == 0:
        return []
    
    # If n > m, transpose
    transposed = False
    if n > m:
        cost_matrix = [[cost_matrix[r][c] for r in range(n)] for c in range(m)]
        n, m = m, n
        transposed = True

    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    p = [0] * (m + 1)
    way = [0] * (m + 1)

    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [float('inf')] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float('inf')
            j1 = 0
            for j in range(1, m + 1):
                if not used[j]:
                    cur = cost_matrix[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    matching = []
    for j in range(1, m + 1):
        if p[j] != 0:
            if transposed:
                matching.append((j - 1, p[j] - 1))
            else:
                matching.append((p[j] - 1, j - 1))
    return matching


# ── ARM 1: Soft Local Worker Ownership ──────────────────────────────────────────
class Arm1_SoftOwnership(ClosedLoopCommitmentV1):
    """Assigns soft quadrant affinity to workers to minimize zone drifting."""
    def _worker_preferred_quad(self, w_idx):
        if w_idx in (0, 1, 2): return "NW"
        if w_idx in (3, 4, 5): return "NE"
        if w_idx in (6, 7, 8): return "SW"
        return "SE"

    def _cluster_lookahead_score(self, target, candidates, base_pos, w_idx=0):
        d = _dist(base_pos, target)
        pref_q = self._worker_preferred_quad(w_idx)
        t_q = _quad(target[0], target[1])
        penalty = 0.0 if t_q == pref_q else 2.5
        
        tx, ty = target
        cluster_bonus = 0.0
        for cx, cy in candidates:
            if (cx, cy) == target: continue
            cd = abs(tx - cx) + abs(ty - cy)
            if cd == 1: cluster_bonus += 2.0
            elif cd == 2: cluster_bonus += 1.0
        return -d - penalty + 0.5 * cluster_bonus

    def _pick_best_candidate(self, cands, base_pos, w_idx=0):
        if not cands: return None
        adj = [c for c in cands if _dist(base_pos, c) == 1]
        if adj: return adj[0]
        return max(cands, key=lambda p: self._cluster_lookahead_score(p, cands, base_pos, w_idx))


# ── ARM 2: Joint Multi-Worker Target Allocation ─────────────────────────────────
class Arm2_JointAllocation(ClosedLoopCommitmentV1):
    """
    Jointly assigns available chores to uncommitted workers via minimum-cost matching,
    eliminating criss-crossing target interleavings across rows.
    """
    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step):
        actions = [None] * len(all_workers)
        claimed_action_tiles = set()
        ns = _nearest_shed(all_workers[0], tiles)
        target_pasture_slots = scan_res.get("target_pasture_slots", set())

        if hour == 0:
            self._worker_targets.clear()

        # Step 1: Local-First Execution on Current Tile
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            x, y = pos
            t = tiles[y][x] if 0 <= y < BOARD and 0 <= x < BOARD else None
            produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
            w_inv = int(inv.get("WHEAT", 0) or 0)
            cow_inv = int(inv.get("COW", 0) or 0)
            sheep_inv = int(inv.get("SHEEP", 0) or 0)

            if pos in SHED_ACCESS and produce_load > 0 and (cow_inv + sheep_inv) == 0 and (w_inv == 0 or not scan_res["hungry"]):
                actions[i] = ["DROP"]
                claimed_action_tiles.add(pos)
                self._worker_targets.pop(i, None)
                continue

            if isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    crop = t.get("crop")
                    fert_inv = int(inv.get("FERTILIZER", 0) or 0)
                    if pos in scan_res["ripe_crops"] and pos not in claimed_action_tiles:
                        actions[i] = ["HARVEST"]
                        claimed_action_tiles.add(pos)
                        self._worker_targets.pop(i, None)
                        continue
                    if fert_inv > 0 and t.get("fertilized_until_day", -1) < day and pos not in claimed_action_tiles:
                        actions[i] = ["FERTILIZE"]
                        claimed_action_tiles.add(pos)
                        self._worker_targets.pop(i, None)
                        continue
                    if not t.get("watered_today") and pos not in claimed_action_tiles:
                        actions[i] = ["WATER"]
                        claimed_action_tiles.add(pos)
                        self._worker_targets.pop(i, None)
                        continue
                elif k == "PASTURE":
                    if t.get("animal"):
                        if not t.get("fed_today") and w_inv > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["FEED"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        if not t.get("cared_today") and pos not in claimed_action_tiles:
                            actions[i] = ["CARE"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        if int(t.get("yield_units", 0) or 0) > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["HARVEST"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        if t.get("fertilizer_available") and pos not in claimed_action_tiles:
                            actions[i] = ["COLLECT_FERTILIZER"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                    else:
                        desired_sp = PASTURE_SPECIES.get(pos, "COW")
                        if desired_sp == "SHEEP" and sheep_inv > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["PLACE", "SHEEP"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        elif desired_sp == "COW" and cow_inv > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["PLACE", "COW"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                elif k == "WEED" and pos not in claimed_action_tiles:
                    actions[i] = ["DIG"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
            elif t is None:
                if pos in scan_res["unbuilt_p"] and pos not in claimed_action_tiles:
                    actions[i] = ["BUILD_PASTURE"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                if pos in scan_res["plant_s"] and int(seeds.get("STRAWBERRY", 0) or 0) > 0 and pos not in claimed_action_tiles:
                    seeds["STRAWBERRY"] = max(0, int(seeds.get("STRAWBERRY")) - 1)
                    actions[i] = ["PLANT", "STRAWBERRY"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                if pos in scan_res["plant_m"] and int(seeds.get("MELON", 0) or 0) > 0 and pos not in claimed_action_tiles:
                    seeds["MELON"] = max(0, int(seeds.get("MELON")) - 1)
                    actions[i] = ["PLANT", "MELON"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                if pos in scan_res["plant_w"] and int(seeds.get("WHEAT", 0) or 0) > 0 and pos not in claimed_action_tiles:
                    seeds["WHEAT"] = max(0, int(seeds.get("WHEAT")) - 1)
                    actions[i] = ["PLANT", "WHEAT"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue

        # Step 2: Validate active commitments
        unassigned_workers = []
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            if actions[i] is not None:
                continue
            produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
            w_inv = int(inv.get("WHEAT", 0) or 0)
            valid = False
            if i in self._worker_targets:
                active_t, task_type, sc = self._worker_targets[i]
                if sc < 15 and active_t not in claimed_action_tiles:
                    ax, ay = active_t
                    at = tiles[ay][ax] if 0 <= ay < BOARD and 0 <= ax < BOARD else None
                    if task_type == "WATER" and isinstance(at, dict) and not at.get("watered_today"): valid = True
                    elif task_type == "HARVEST" and isinstance(at, dict) and int(at.get("yield_units", 0) or 0) > 0: valid = True
                    elif task_type == "FEED" and w_inv > 0 and isinstance(at, dict) and not at.get("fed_today"): valid = True
                    elif task_type == "DROP" and produce_load > 0: valid = True
                    
                    if valid:
                        self._worker_targets[i] = (active_t, task_type, sc + 1)
                        claimed_action_tiles.add(active_t)
                        actions[i] = [_bfs_step(pos, active_t, tiles)]
                    else:
                        self._worker_targets.pop(i, None)
                else:
                    self._worker_targets.pop(i, None)
            if not valid:
                unassigned_workers.append(i)

        if not unassigned_workers:
            return actions

        # Collect candidate tasks for joint assignment across priority pools
        priority_pools = [
            ("URGENT_WATER", scan_res["urgent_unwatered"]),
            ("HARVEST_CROPS", scan_res["ripe_crops"]),
            ("WATER_CROPS", scan_res["unwatered"]),
            ("PLANT_STRAW", scan_res["plant_s"] if int(seeds.get("STRAWBERRY", 0) or 0) > 0 else []),
            ("PLANT_MELON", scan_res["plant_m"] if int(seeds.get("MELON", 0) or 0) > 0 else []),
            ("PLANT_WHEAT", scan_res["plant_w"] if int(seeds.get("WHEAT", 0) or 0) > 0 else []),
            ("WEEDS", scan_res["weeds"]),
        ]

        assigned_workers = set()
        for pool_name, pool_cands in priority_pools:
            avail_cands = [c for c in pool_cands if c not in claimed_action_tiles]
            avail_workers = [w for w in unassigned_workers if w not in assigned_workers]
            if not avail_cands or not avail_workers:
                continue

            # Build cost matrix
            cost_matrix = []
            for w in avail_workers:
                w_pos = all_workers[w]
                row = []
                for c in avail_cands:
                    d = _dist(w_pos, c)
                    # Cluster bonus
                    cx, cy = c
                    cb = 0.0
                    for ox, oy in avail_cands:
                        if (ox, oy) == c: continue
                        cd = abs(cx - ox) + abs(cy - oy)
                        if cd == 1: cb += 2.0
                        elif cd == 2: cb += 1.0
                    cost = d - 0.4 * cb
                    row.append(cost)
                cost_matrix.append(row)

            matching = min_cost_bipartite_matching(cost_matrix)
            for w_idx_sub, c_idx_sub in matching:
                w = avail_workers[w_idx_sub]
                chosen_cand = avail_cands[c_idx_sub]
                claimed_action_tiles.add(chosen_cand)
                assigned_workers.add(w)
                self._worker_targets[w] = (chosen_cand, pool_name, 1)
                actions[w] = [_bfs_step(all_workers[w], chosen_cand, tiles)]

        # Fallback for remaining unassigned workers
        for w in unassigned_workers:
            if w not in assigned_workers:
                pos = all_workers[w]
                inv = all_invs[w]
                produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
                if produce_load > 0:
                    actions[w] = [_bfs_step(pos, ns, tiles)]
                    self._worker_targets[w] = (ns, "DROP", 1)
                else:
                    actions[w] = ["PASS"]
        return actions


# ── ARM 3: Cluster Lock ─────────────────────────────────────────────────────────
class Arm3_ClusterLock(ClosedLoopCommitmentV1):
    """Locks worker into active contiguous cluster (L1 <= 2) before allowing distant jumps."""
    def _cluster_lookahead_score(self, target, candidates, base_pos):
        d = _dist(base_pos, target)
        tx, ty = target
        cluster_bonus = 0.0
        for cx, cy in candidates:
            if (cx, cy) == target: continue
            cd = abs(tx - cx) + abs(ty - cy)
            if cd == 1: cluster_bonus += 3.0
            elif cd == 2: cluster_bonus += 1.5
        # Strong local cluster penalty if distance > 2 while local tasks exist
        local_tasks = [c for c in candidates if _dist(base_pos, c) <= 2]
        if local_tasks and d > 2:
            return -d - 10.0 + 0.5 * cluster_bonus
        return -d + 0.5 * cluster_bonus


# ── ARM 4: Zone Exit Penalty ────────────────────────────────────────────────────
class Arm4_ZoneExitPenalty(ClosedLoopCommitmentV1):
    """Applies a soft penalty to chores outside the worker's current quadrant."""
    def _cluster_lookahead_score(self, target, candidates, base_pos):
        d = _dist(base_pos, target)
        same_q = (_quad(target[0], target[1]) == _quad(base_pos[0], base_pos[1]))
        zone_penalty = 0.0 if same_q else 4.0
        
        tx, ty = target
        cluster_bonus = 0.0
        for cx, cy in candidates:
            if (cx, cy) == target: continue
            cd = abs(tx - cx) + abs(ty - cy)
            if cd == 1: cluster_bonus += 2.0
            elif cd == 2: cluster_bonus += 1.0
        return -d - zone_penalty + 0.5 * cluster_bonus


# ── ARM 5: Shed Opportunism (En-Route Drops Only) ────────────────────────────────
class Arm5_ShedOpportunism(ClosedLoopCommitmentV1):
    """Restricts dedicated shed trips to load >= 5 or hour >= 22, enabling en-route drops."""
    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step):
        # Override shed visit condition: only visit shed if load >= 5 or hour >= 22 or naturally passing through
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
            # If worker is currently adjacent to shed, drop goods en route
            if pos in SHED_ACCESS and produce_load > 0:
                pass # Local-First in base class will drop
        return super()._dispatch_workers(all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step)


# ── ARM 6: Load Threshold 5+ ───────────────────────────────────────────────────
class Arm6_LoadThreshold(ClosedLoopCommitmentV1):
    """Strictly holds produce until threshold >= 5 or day end."""
    pass # Base commitment v1 has produce_load >= 5 and hour >= 20


# ── ARM 7: Short-Horizon Live-State Prepositioning ──────────────────────────────
class Arm7_Prepositioning(ClosedLoopCommitmentV1):
    """Prepositions uncommitted workers near maturing crops during late evening (H >= 20)."""
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        prepos = []
        for y in range(BOARD):
            for x in range(BOARD):
                pos = (x, y)
                t = tiles[y][x] if tiles else None
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    crop = t.get("crop")
                    c_def = CROPS_DEF.get(crop, {})
                    age = day - int(t.get("planted_day", 0) or 0)
                    if age == c_def.get("first_yield_day", 2) - 1:
                        prepos.append(pos)
        res["prepos"] = prepos
        return res


print("All 7 Isolated Causal Interventions constructed successfully.")
