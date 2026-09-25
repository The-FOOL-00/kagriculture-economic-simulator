# SPDX-License-Identifier: MIT
"""V32 freeze/integrity/quarantine tests (§51 items 1-4, 7, 11). Fast, no matches."""

import json
import os
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, REPO_ROOT)

from v32_common import (DIGESTS, EXPERTS, PATHS, V32_CONFIRM, V32_DEV,  # noqa: E402
                        V32_EXP1, V32_TRAIN, assert_frozen, check_seed_allowed,
                        sha256_file)


def test_v22r1_integrity():
    """§51(1): Slot A artifact untouched."""
    got = sha256_file(os.path.join(REPO_ROOT, PATHS["v22r1_tarball"]))
    assert got == "6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5"


def test_a7_integrity():
    """§51(2): A7 bytes + flag vector (V28 freeze)."""
    from aec.backbone.v27_ablation_adapters import V27AblationAdapter
    got = sha256_file(os.path.join(REPO_ROOT, PATHS["v27_ablation_adapters"]))
    assert got == DIGESTS["v27_ablation_adapters"]
    a7 = V27AblationAdapter(variant="V27-ABL-A7")
    assert (a7.call_v3_at_step0, a7.open_units, a7.dispatch,
            a7.rewrite_step0_wash) == (True, 30, False, True)


def test_expert_hash_integrity():
    """§51(3): every expert resolves to its frozen digest."""
    assert_frozen()  # asserts all PATHS digests + engine version
    man = json.load(open(os.path.join(REPO_ROOT, "V32_EXPERT_POPULATION.json")))
    by_id = {e["expert_id"]: e for e in man["experts"]}
    assert set(by_id) == set(EXPERTS), set(by_id) ^ set(EXPERTS)
    assert by_id["E0_V3"]["hash_sha256"] == DIGESTS["v3_tarball"]
    assert by_id["E1_V22R1"]["hash_sha256"] == DIGESTS["v22r1_tarball"]
    assert by_id["E2_A7"]["hash_sha256"] == DIGESTS["v27_ablation_adapters"]
    assert by_id["E6_W72"]["hash_sha256"] == DIGESTS["v31r2_wash_adapter"]
    assert by_id["E8_DMITRII"]["hash_sha256"] == DIGESTS["dmitrii"]
    assert by_id["E9_AST"]["hash_sha256"] == DIGESTS["a7_standalone"]


def test_simulator_integrity():
    """§51(4): exact engine version."""
    import kaggle_environments
    assert kaggle_environments.__version__ == "1.32.7"


def _refuses(seed, **kw):
    with pytest.raises(RuntimeError):
        check_seed_allowed(seed, **kw)


def test_seed_quarantine():
    """§51(7): protected/consumed/CONFIRM/out-of-range seeds refused."""
    for s in (214200, 214225, 214249, 340000, 340050, 340050 + 39, 340090,
              340150, 340199, 340200, 340275, 340300, 340349):
        _refuses(s)
    for s in (249530, 249569, 249634, 1, 999999):  # consumed history / junk
        _refuses(s)
    for s in (249695, 249700, 249734):  # CONFIRM without flag
        _refuses(s)
    for s in (249735, 250000):  # beyond registered range
        _refuses(s)
    # CONFIRM allowed only with explicit promotion flag
    check_seed_allowed(249695, allow_confirm=True)
    # TRAIN/DEV/commissioning execute
    for s in (249635, 249640, 249672, 249673, 249674, 249675, 249694):
        check_seed_allowed(s)


def test_cohort_separation():
    """§51(11): TRAIN/DEV/CONFIRM/EXP1 disjoint and ordered; commissioning noted."""
    tr, dv, cf = V32_TRAIN, V32_DEV, V32_CONFIRM
    assert tr[1] < dv[0] <= dv[1] < cf[0] <= cf[1]
    assert V32_EXP1[0] >= tr[0] and V32_EXP1[1] <= tr[1]
    # harness commissioning seeds live inside TRAIN and are documented consumed
    assert tr[0] <= 249673 <= 249674 <= tr[1]
