# SPDX-License-Identifier: MIT
"""D1–D8 static conformance + G-IMPL forbidden-reference + artifact hashes.

Validation battery §33 items 2–8 (structural part) and item 20.
"""

import hashlib
import os
import re

import pytest

import h1_agent
import h1_const
import h1_dominance
import h1_search
import h1_shadow
import h1_telemetry

H1_FILES = ["h1_const.py", "h1_units.py", "h1_baseline.py", "h1_shadow.py",
            "h1_search.py", "h1_dominance.py", "h1_telemetry.py",
            "h1_agent.py"]


def _read(h1_dir, name):
    with open(os.path.join(h1_dir, name)) as handle:
        return handle.read()


# ------------------------------------------------------------- D1 whitelist
def test_d1_whitelist_exact():
    assert h1_const.WHITELIST_UNIT_OPS == frozenset({
        "NORTH", "SOUTH", "EAST", "WEST",
        "HARVEST", "COLLECT_FERTILIZER", "DROP", "PASS"})
    assert "PLACE" not in h1_const.WHITELIST_UNIT_OPS


def test_d1_move_emitters_only_cardinal(h1_dir):
    # Proposals must never CONSTRUCT non-whitelist commands.  Tile-kind
    # READS (== "PLANT") are legitimate (bundle discovery).
    src = _read(h1_dir, "h1_search.py")
    assert '"PLACE"' not in src and "'PLACE'" not in src
    for op in ("FERTILIZE", "PLANT", "WATER", "FEED", "CARE", "BUILD",
               "HIRE", "PICKUP"):
        assert re.search(r'\["%s"' % op, src) is None, op
        assert re.search(r"\['%s'" % op, src) is None, op


def test_d1_agent_never_names_non_whitelist_ops(h1_dir):
    # The agent must never CONSTRUCT non-whitelist commands (it only
    # re-emits stored plan units + live markets).  The WEED_BLOCKED_OPS
    # rejection set is legitimate and asserted frozen below.
    src = _read(h1_dir, "h1_agent.py")
    for op in ("PLACE", "FERTILIZE", "WATER", "FEED", "CARE", "PICKUP",
               "HIRE", "BUY_SEED", "BUY_ANIMAL", "BUY_LAND"):
        assert re.search(r'\["%s"' % op, src) is None, op
    assert h1_agent.WEED_BLOCKED_OPS == frozenset(
        {"PLANT", "BUILD_COOP", "BUILD_PASTURE"})
    assert h1_agent.ADMITTED_MARKET_OPS == frozenset(
        {"SELL", "BUY_PRODUCT"})


def test_d1_proposals_emit_whitelist_only(fresh_baseline):
    # Structural: _walk/_return emit moves + DROP; proposals add
    # HARVEST/COLLECT/PASS only (verified by emission scan below on a
    # live planning run in test_h1_identity activation test).
    assert set(h1_search._walk((0, 0), (2, 3))[0]) <= {"EAST"}
    cmds = h1_search._return((0, 0))
    assert cmds[-1] == ["DROP"]
    assert {c[0] for c in cmds} <= {"NORTH", "SOUTH", "EAST", "WEST",
                                    "DROP"}


# ------------------------------------------------------------------ D2/D3
def test_d2_entry_step():
    assert h1_const.ENTRY_STEP == 712
    assert h1_const.FINAL_STEP == 718
    assert h1_const.WINDOW_LEN == 7
    assert h1_const.WINDOW_STEPS == (712, 713, 714, 715, 716, 717, 718)


def test_d3_agent_builds_no_market_orders(h1_dir):
    # The G3b ADMISSION set legitimately names SELL/BUY_PRODUCT; order
    # CONSTRUCTION is what D3 forbids.
    src = _read(h1_dir, "h1_agent.py")
    assert re.search(r'\["SELL"', src) is None
    assert re.search(r'\["BUY', src) is None
    assert "terminal_market" not in src
    assert "liquidat" not in src


def test_d3_search_builds_no_market_orders(h1_dir):
    src = _read(h1_dir, "h1_search.py")
    assert '"SELL"' not in src and "'SELL'" not in src
    assert "BUY_PRODUCT" not in src
    assert "terminal_market" not in src
    assert "liquidat" not in src


# ------------------------------------------------------------------ D4/D6
def test_d4_search_budget_frozen():
    assert h1_const.MAX_SIMULATIONS == 128
    assert h1_const.PASSES == 1
    assert h1_const.PROPOSALS_PER_ACTOR == 8
    assert h1_const.START_OFFSETS == (0, 1, 2, 3, 4, 5, 6)
    assert h1_const.TOP_SINGLES == 6
    assert h1_const.TOP_PAIR_HALF == 3
    assert h1_const.DIRECT_RETURN_RESERVE == 2
    assert h1_search.MAX_SIMULATIONS == 128
    assert h1_search.PASSES == 1
    assert h1_search.PROPOSALS_PER_ACTOR == 8


def test_d6_tie_semantics_present(h1_dir):
    src = _read(h1_dir, "h1_search.py")
    assert "score > best_value" in src  # strict greater-than
    assert "epsilon" not in src.lower()
    assert "tolerance" not in src.lower()
    assert "random" not in src.lower()
    src2 = _read(h1_dir, "h1_dominance.py")
    assert "epsilon" not in src2.lower()
    assert "tolerance" not in src2.lower()


# ------------------------------------------------------------------ D5/D7
def test_d5_coverage_constant():
    assert h1_const.BUY_COVERAGE_PER_UNIT == 125
    assert h1_dominance.coverage_required(50) == 6250
    assert h1_dominance.coverage_required(0) == 0


def test_d7_reason_enum_frozen_exact():
    assert h1_telemetry.REASONS == (
        "OK_ACTIVATED", "ABSTAIN_CONFIG", "ABSTAIN_SHED",
        "ABSTAIN_ITEMS", "ABSTAIN_WINDOW_OPS", "ABSTAIN_MARKET_OP",
        "ABSTAIN_BUY_COVERAGE", "ABSTAIN_HANDSHAKE", "ABSTAIN_BUDGET",
        "ABSTAIN_NO_GAIN", "ABSTAIN_DOMINANCE", "ABSTAIN_NOSTEAL",
        "ABSTAIN_ACCEPT", "ABANDON_MISMATCH_T",
        "ABANDON_NONCONSECUTIVE")
    assert len(h1_telemetry.REASONS) == 15
    assert set(h1_telemetry.SUBCAUSE_SCHEMA) == set(
        h1_telemetry.REASONS)


def test_d7_no_salvage_mode(h1_dir):
    for name in H1_FILES:
        src = _read(h1_dir, name)
        assert re.search(r"salvage\s*\(", src.lower()) is None, name
        assert re.search(r"def \w*salvage", src.lower()) is None, name
        assert "recover_observed" not in src.lower(), name
        assert "_recover" not in src, name
        assert "resume_parent" not in src.lower(), name
    # ...while the abandonment helper provably returns the live action
    # (behavioral identity is asserted in test_h1_identity).
    src = _read(h1_dir, "h1_agent.py")
    assert "no salvage mode" in src.lower()


# ------------------------------------------------------------------ D8/G0
def test_d8_baseline_identity_pinned():
    assert h1_const.BASELINE_PATH == \
        "candidates/compiled_v54_plus_residual.py"
    assert h1_const.BASELINE_SHA256 == \
        "18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb"


def test_g0_pins():
    assert (h1_const.PIN_BOARD_SIZE, h1_const.PIN_TURNS_PER_DAY,
            h1_const.PIN_EPISODE_STEPS, h1_const.PIN_SHED_CAPACITY,
            h1_const.PIN_MAX_ORDERS) == (10, 24, 720, 100, 10)


def test_loader_verifies_baseline_hash(fresh_baseline):
    origin = fresh_baseline.module.__spec__.origin
    with open(origin, "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()
    assert digest == h1_const.BASELINE_SHA256
    assert fresh_baseline.config is not None
    # Live config premises the in-window proofs rest on.
    cfg = fresh_baseline.config
    assert cfg.defer_enabled is False
    assert cfg.market_maker_enabled is False
    assert cfg.active_stop <= 712
    assert cfg.maximum_orders == 10


def test_loader_rejects_tampered_file(h1_dir, tmp_path, monkeypatch):
    import h1_baseline
    src = os.path.join(
        os.path.abspath(os.path.join(h1_dir, "..", "..")),
        "candidates/compiled_v54_plus_residual.py")
    with open(src, "rb") as handle:
        data = bytearray(handle.read())
    data[-20] ^= 0xFF
    bad = tmp_path / "tampered.py"
    bad.write_bytes(bytes(data))
    monkeypatch.setattr(h1_baseline, "BASELINE_PATH",
                        os.path.relpath(str(bad), os.path.abspath(
                            os.path.join(h1_dir, "..", ".."))))
    with pytest.raises(h1_baseline.BaselineLoadError):
        h1_baseline.load_baseline()


# ------------------------------------------------------- G-IMPL forbidden
# Forbidden MECHANISM references (G-IMPL/P1–P10).  Comment/docstring
# mentions of a SKIPPED mechanism (e.g. "_defer — SKIPPED") are allowed;
# calls, definitions, attribute access, and instantiation are not.
# (Residual-controller exact-function reuse is prereg-mandated (H3),
# so controller names are NOT forbidden; only construction is.)
FORBIDDEN = [
    r"\bHORIZON_GUARD_THRESHOLD\b", r"\bREJECT_HORIZON\b",
    r"\bremaining_horizon\b", r"\bMarketMaker\w*\b",
    r"\bmarket_maker\b", r"build_residual_controller\s*\(",
    r"ResidualValueController\s*\(",
    r"\._defer\b", r"\._preempt\b",
    r"\bdef _defer\b", r"\bdef _preempt\b",
    r"\badvance\b", r"\bsubtract\b",
    r"\bcheckpoint\b", r"\bvaluation\b", r"\bregistry\b",
    r"\bdev_00[456]\b", r"\bH500\b", r"\bH=500\b",
]


@pytest.mark.parametrize("name", H1_FILES)
def test_gimpl_no_forbidden_references(h1_dir, name):
    src = _read(h1_dir, name)
    for pattern in FORBIDDEN:
        match = re.search(pattern, src)
        assert match is None, (name, pattern, match.group(0) if match
                               else None)


def test_gimpl_no_rng_or_wallclock_gates(h1_dir):
    for name in H1_FILES:
        src = _read(h1_dir, name)
        assert "random." not in src, name
        assert "import random" not in src, name
        assert "time.sleep" not in src, name
        assert "threading" not in src, name
        assert "multiprocessing" not in src, name
        assert "concurrent" not in src, name


# ------------------------------------------------- item 20: frozen hashes
FROZEN = {
    "candidates/compiled_v54_plus_residual.py":
        "18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb",
    "candidates/compiled_v54_plus_shop.py":
        "f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8",
    "candidates/closed_loop_architecture/dev_005_confirmed_shop_scheduler.py":
        "f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78",
    "candidates/closed_loop_architecture/dev_006_horizon_guard_scheduler.py":
        "06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb",
    "experiments/EXP-DEV-007_MECHANISM_EXPOSURE/PROTOCOL.md":
        "d10ee1857b380ee1254a29bf9fc1a49e33c10783b9e49ef1e68beb75bab80cff",
    "extracted_agents/dmitrii_lb2800/unit_model.py":
        "c03e8c5cd10466c229ee0a44dece9a3943c10bff135d96a7822ffe75d6922724",
}


@pytest.mark.parametrize("relpath,want", sorted(FROZEN.items()))
def test_protected_artifact_hashes(repo_root, relpath, want):
    with open(os.path.join(repo_root, relpath), "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()
    assert digest == want, relpath


def test_arch002_governing_docs_present(h1_dir):
    for name in ("01_ISOLATION_AUDIT.md", "02_PREREGISTRATION.md"):
        path = os.path.join(h1_dir, name)
        assert os.path.isfile(path), name
        assert os.path.getsize(path) > 10000, name
