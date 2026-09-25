# SPDX-License-Identifier: MIT
"""V32 diversity-aware opponent sampler + replay sampler (V32_SAMPLING_PROTOCOL.md).

Seeded, reproducible, family-floored. No torch dependency.
"""

import hashlib
import json
import random

# Family map (v1, from V32_EXPERT_POPULATION.md strategy families + EXP-1
# clustering; threshold 0.15 merges nothing in the core set — all 9 core
# experts are pairwise distinct by wash/dispatch/reactivity axes).
FAMILIES = {
    "v3-macro": ["E0_V3"],
    "v3-macro+aec": ["E1_V22R1"],
    "wash-30": ["E2_A7"],
    "v3+dispatch": ["E3_V25P3"],
    "wash-30+dispatch": ["E4_A1"],
    "wash-50+dispatch": ["E5_A2"],
    "wash-micro": ["E6_W72"],
    "wash-20-15": ["E7_W2015"],
    "reactive-external": ["E8_DMITRII"],
}

CHAMPION_ANCHOR_FRAC = 0.20
SELF_FRAC = 0.10
FAMILY_FLOOR = 0.05


def family_weights():
    import math
    w = {f: math.sqrt(len(m)) for f, m in FAMILIES.items()}
    s = sum(w.values())
    return {f: v / s for f, v in w.items()}


def sample_opponent(rng, champion_id="E2_A7", learner_tag="LEARNER"):
    """Sample one opponent id (or LEARNER for self-play legs)."""
    u = rng.random()
    if u < CHAMPION_ANCHOR_FRAC:
        return champion_id
    if u < CHAMPION_ANCHOR_FRAC + SELF_FRAC:
        return learner_tag
    # family floor: with prob FAMILY_FLOOR * n_families, force uniform family
    fams = list(FAMILIES)
    if rng.random() < FAMILY_FLOOR * len(fams):
        fam = fams[rng.randrange(len(fams))]
    else:
        w = family_weights()
        x = rng.random()
        acc = 0.0
        fam = fams[-1]
        for f in fams:
            acc += w[f]
            if x <= acc:
                fam = f
                break
    return rng.choice(FAMILIES[fam])


def sample_opponent_sequence(seed, n, **kw):
    rng = random.Random(seed)
    return [sample_opponent(rng, **kw) for _ in range(n)]


# --- replay sampler (BC / loss-mining) ---
PRIORITY = {"win": 1.0, "close": 2.0, "strong_opp": 2.0, "loss": 3.0,
            "catastrophe": 4.0}


def classify_leg(delta, strong_opp=False):
    if delta <= -25000:
        return "catastrophe"
    if delta < 0:
        return "loss"
    if abs(delta) < 2000:
        return "close"
    if strong_opp:
        return "strong_opp"
    return "win"


def sample_replay_batch(rng, legs, k):
    """Weighted sample of leg dicts ({delta, strong_opp,...}) with priorities."""
    import random as _r
    weights = []
    for leg in legs:
        cls = classify_leg(leg["delta"], leg.get("strong_opp", False))
        weights.append(PRIORITY[cls])
    total = sum(weights)
    out = []
    for _ in range(k):
        x = rng.random() * total
        acc = 0.0
        for leg, w in zip(legs, weights):
            acc += w
            if x <= acc:
                out.append(leg)
                break
    return out
