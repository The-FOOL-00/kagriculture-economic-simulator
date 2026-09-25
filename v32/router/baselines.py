# SPDX-License-Identifier: MIT
"""R1 deterministic baselines: fixed experts, random, per-opponent lookup."""

import random

from v32.router.split import ROUTER_CLASSES


class FixedExpert:
    def __init__(self, expert_id):
        self.idx = ROUTER_CLASSES.index(expert_id)

    def predict(self, rows):
        return [self.idx] * len(rows)


class RandomExpert:
    def __init__(self, seed=0):
        self.seed = seed

    def predict(self, rows):
        rng = random.Random(self.seed)
        return [rng.randrange(len(ROUTER_CLASSES)) for _ in rows]


class PerOpponentLookup:
    """M1: per-opponent best-fixed by TRAIN mean cash (A+ID diagnostic)."""

    def __init__(self):
        self.table = {}

    def fit(self, rows):
        from collections import defaultdict
        agg = defaultdict(lambda: defaultdict(list))
        for r in rows:
            for i, c in enumerate(r["cash"]):
                agg[r["opp"]][i].append(c)
        for opp, d in agg.items():
            means = {i: sum(v) / len(v) for i, v in d.items()}
            self.table[opp] = max(means, key=lambda i: (means[i], -i))

    def predict(self, rows):
        glob = max(self.table.values()) if self.table else 0
        return [self.table.get(r["opp"], glob) for r in rows]


def global_best_fixed(rows):
    means = [sum(r["cash"][i] for r in rows) / len(rows)
             for i in range(len(ROUTER_CLASSES))]
    return max(range(len(means)), key=lambda i: (means[i], -i))
