import sys
import os
import json
import numpy as np

# Phase 10: Sheep slot reservation & lost wool accounting
# Phase 11: Worker labor contention decomposition

def compute_lost_cycles_accounting(sheep_shed_days_delta, wool_delta, wheat_rev_delta):
    """
    Computes exact opportunity costs:
    Sheep production parameters:
    first_yield_day = 6
    interval = 3
    max_held = 6
    product = WOOL (base price ~ $200)
    With CARE bonus: yield = 2 units per cycle (base 1 + bonus 1).
    Gross revenue per 3-day cycle = 2 * $200 = $400.
    Lost sheep-day = 1/3 of a cycle = ~$133.33/day.
    """
    lost_sheep_days = sheep_shed_days_delta
    lost_wool_cycles = wool_delta / 2.0 # each cycle produces 2 units of wool when cared+fed
    gross_wool_loss = abs(wool_delta) * 200.0
    net_economic_drag = gross_wool_loss - wheat_rev_delta
    
    return {
        "lost_sheep_days": lost_sheep_days,
        "lost_wool_cycles": lost_wool_cycles,
        "gross_wool_loss_dollars": gross_wool_loss,
        "wheat_rev_delta": wheat_rev_delta,
        "net_economic_drag": net_economic_drag
    }

if __name__ == "__main__":
    print("Helper module for Phase 10 & 11 ready.")
