# SPDX-License-Identifier: MIT
"""V29 isolation tests: process/import/order invariance (consumed seeds).

Covers brief s33 items 6-8. The full 7-context matrix runs in
scripts/v29_isolation_audit.py; these committed tests pin the key
regressions (V27 import-cache bug, candidate-order dependence).
"""

import hashlib
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from aec.backbone.v25_p3_adapter import V25P3BackboneAdapter  # noqa: E402
from aec.backbone.v27_ablation_adapters import V27AblationAdapter  # noqa: E402
from aec.backbone.v3_adapter import V3BackboneAdapter  # noqa: E402
from kaggle_environments import make  # noqa: E402


def play(cand, base, seed, seat):
    a = lambda o, c=None: cand.act(o, c)  # noqa: E731
    b = lambda o, c=None: base.act(o, c)  # noqa: E731
    env = make("kaggriculture", configuration={"seed": seed})
    env.run([a, b] if seat == 0 else [b, a])
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    acts = [s[seat].get("action") for s in env.steps]
    d = hashlib.sha256(json.dumps(acts, sort_keys=True).encode()).hexdigest()
    return (r0 if seat == 0 else r1, r1 if seat == 0 else r0, d)


def test_no_main_module_contamination():
    assert "main" not in sys.modules
    V27AblationAdapter(variant="V27-ABL-A7")
    V3BackboneAdapter()
    V25P3BackboneAdapter()
    assert "main" not in sys.modules


def test_adapter_namespaces_distinct():
    a1 = V27AblationAdapter(variant="V27-ABL-A7")
    a2 = V27AblationAdapter(variant="V27-ABL-A7")
    v = V3BackboneAdapter()
    nss = [a1._v3_agent_callable.__globals__,
           a2._v3_agent_callable.__globals__, v._agent_fn.__globals__]
    assert len({id(n) for n in nss}) == 3


def test_no_cross_candidate_state_leakage():
    """P3-primer-then-A7 in one process equals fresh A7 (V27 bug dead)."""
    seed = 249432
    p3 = V25P3BackboneAdapter()
    play(p3, V3BackboneAdapter(), seed, 0)
    primed = play(V27AblationAdapter(variant="V27-ABL-A7"),
                  V3BackboneAdapter(), seed, 0)
    v3 = V3BackboneAdapter()
    a7 = V27AblationAdapter(variant="V27-ABL-A7")
    unprimed = play(a7, v3, seed, 0)
    assert primed == unprimed


def test_execution_order_invariance():
    """V3->A7->V3->A7 vs A7->V3->A7->V3 agree exactly (consumed seed)."""
    seed = 249433
    seq_a = [play(V27AblationAdapter(variant="V27-ABL-A7")
                  if k == "A7" else V3BackboneAdapter(),
                  V3BackboneAdapter(), seed, 0)
             for k in ("V3", "A7", "V3", "A7")]
    seq_b = [play(V27AblationAdapter(variant="V27-ABL-A7")
                  if k == "A7" else V3BackboneAdapter(),
                  V3BackboneAdapter(), seed, 0)
             for k in ("A7", "V3", "A7", "V3")]
    assert seq_a[1] == seq_a[3] == seq_b[0] == seq_b[2]
    assert seq_a[0] == seq_a[2] == seq_b[1] == seq_b[3]


def test_selfplay_order_invariance():
    """A7vA7/V3vV3 invariant to prior-candidate history (consumed seed)."""
    seed = 249436
    first_a = play(V27AblationAdapter(variant="V27-ABL-A7"),
                   V27AblationAdapter(variant="V27-ABL-A7"), seed, 0)
    play(V25P3BackboneAdapter(), V3BackboneAdapter(), seed, 0)  # primer
    second_a = play(V27AblationAdapter(variant="V27-ABL-A7"),
                    V27AblationAdapter(variant="V27-ABL-A7"), seed, 0)
    assert first_a == second_a
    first_v = play(V3BackboneAdapter(), V3BackboneAdapter(), seed, 0)
    play(V27AblationAdapter(variant="V27-ABL-A7"),
         V3BackboneAdapter(), seed, 0)  # A7 primer
    second_v = play(V3BackboneAdapter(), V3BackboneAdapter(), seed, 0)
    assert first_v == second_v
