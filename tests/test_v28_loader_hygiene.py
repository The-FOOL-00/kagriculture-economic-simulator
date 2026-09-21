# SPDX-License-Identifier: MIT
"""V28 loader-hygiene tests: the V27 import-cache bug cannot recur.

All matches run on CONSUMED seeds (249432/249433, V25 cohort A).
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
    # Primer: run P3 first in THIS process (the V27 contamination pattern).
    p3 = V25P3BackboneAdapter()
    play(p3, V3BackboneAdapter(), seed, 0)
    primed = play(V27AblationAdapter(variant="V27-ABL-A7"),
                  V3BackboneAdapter(), seed, 0)
    # Fresh adapters, reverse construction order.
    v3 = V3BackboneAdapter()
    a7 = V27AblationAdapter(variant="V27-ABL-A7")
    unprimed = play(a7, v3, seed, 0)
    assert primed == unprimed


def test_a7_step0_rewrite_deploys():
    a7 = V27AblationAdapter(variant="V27-ABL-A7")
    play(a7, V3BackboneAdapter(), 249433, 0)
    assert a7.step0_rewritten is True
    assert a7.step0_unexpected_shape is False


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
