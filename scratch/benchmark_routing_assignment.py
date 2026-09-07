import sys, os
import time
from collections import deque
import numpy as np

BOARD = 10
SHED_ACCESS = [(4, 4), (5, 4), (4, 5), (5, 5)]

# Synthetic farm state:
# 6 workers at various positions
# 20 pending crop chores (watering/harvesting in NW quadrant)
# 4 pending animal chores (in corridor (4,4), (4,3), (4,2), (3,4))

workers = [(4, 4), (4, 4), (4, 4), (2, 2), (1, 1), (3, 3)]
crop_tasks = [(x, y) for y in range(4) for x in range(5)]
animal_tasks = [(4, 4), (4, 3), (4, 2), (3, 4)]
all_tasks = crop_tasks + animal_tasks

def dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# 1. Greedy Nearest-Task (Grandmaster style)
def greedy_assignment(workers, tasks):
    assigned = {}
    claimed = set()
    total_cost = 0
    t0 = time.perf_counter()
    for w_i, w_pos in enumerate(workers):
        avail = [t for t in tasks if t not in claimed]
        if avail:
            best_t = min(avail, key=lambda t: dist(w_pos, t))
            claimed.add(best_t)
            assigned[w_i] = best_t
            total_cost += dist(w_pos, best_t)
    t1 = time.perf_counter()
    return total_cost, t1 - t0, assigned

# 2. Hungarian Assignment (Scipy linear_sum_assignment)
from scipy.optimize import linear_sum_assignment

def hungarian_assignment(workers, tasks):
    cost_matrix = np.zeros((len(workers), len(tasks)))
    for i, w in enumerate(workers):
        for j, t in enumerate(tasks):
            cost_matrix[i, j] = dist(w, t)
    t0 = time.perf_counter()
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    t1 = time.perf_counter()
    total_cost = cost_matrix[row_ind, col_ind].sum()
    assigned = {r: tasks[c] for r, c in zip(row_ind, col_ind)}
    return total_cost, t1 - t0, assigned

# 3. Zoned Assignment + Serpentine Sweep
def zoned_serpentine_assignment(workers, tasks):
    t0 = time.perf_counter()
    # Partition workers:
    # W0: dedicated livestock corridor
    # W1-W5: assigned to spatial slices/columns of crops
    assigned = {}
    total_cost = 0
    
    # Corridor worker
    corridor_tasks = [t for t in tasks if t in animal_tasks]
    if corridor_tasks:
        assigned[0] = min(corridor_tasks, key=lambda t: dist(workers[0], t))
        total_cost += dist(workers[0], assigned[0])
        
    # Crop workers assigned to column/row buckets
    crop_t = [t for t in tasks if t not in animal_tasks]
    # Sort crop tasks in serpentine order (alternating rows)
    crop_t.sort(key=lambda p: (p[1], p[0] if p[1] % 2 == 0 else -p[0]))
    
    for w_i in range(1, len(workers)):
        if crop_t:
            # pick nearest task in sequence
            avail = [t for t in crop_t if t not in assigned.values()]
            if avail:
                best = min(avail[:3], key=lambda t: dist(workers[w_i], t))
                assigned[w_i] = best
                total_cost += dist(workers[w_i], best)
    t1 = time.perf_counter()
    return total_cost, t1 - t0, assigned

if __name__ == "__main__":
    print("=== Benchmarking Assignment Architectures ===")
    cost_g, time_g, ass_g = greedy_assignment(workers, all_tasks)
    print(f"Greedy Nearest:      Total Distance = {cost_g:2.0f}, Compute Time = {time_g*1000:6.3f} ms")
    
    cost_h, time_h, ass_h = hungarian_assignment(workers, all_tasks)
    print(f"Hungarian Assignment: Total Distance = {cost_h:2.0f}, Compute Time = {time_h*1000:6.3f} ms (Distance Reduction: {cost_g - cost_h:2.0f})")
    
    cost_z, time_z, ass_z = zoned_serpentine_assignment(workers, all_tasks)
    print(f"Zoned Serpentine:    Total Distance = {cost_z:2.0f}, Compute Time = {time_z*1000:6.3f} ms")
