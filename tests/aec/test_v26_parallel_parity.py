# SPDX-License-Identifier: MIT
"""Tests for Serial vs Parallel Execution Equivalence (§22)."""

import pytest
from concurrent.futures import ProcessPoolExecutor
from scripts.run_v26_transfer_tournament import run_single_v26_match


def test_serial_vs_parallel_match_parity():
    """Verify identical execution, rewards, and action digests across serial and worker paths."""
    spec = {
        "arm": "ARM1_V25_STANDALONE",
        "seed": 249470,
        "seat": 0,
    }

    # 1. Serial Execution
    res_serial = run_single_v26_match(spec)

    # 2. Worker / Subprocess Execution
    with ProcessPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(run_single_v26_match, spec)
        res_parallel = fut.result()

    # Exact deterministic assertions
    assert res_serial["terminal_reward"] == res_parallel["terminal_reward"], (
        f"Reward mismatch: {res_serial['terminal_reward']} vs {res_parallel['terminal_reward']}"
    )
    assert res_serial["paired_delta"] == res_parallel["paired_delta"], (
        f"Delta mismatch: {res_serial['paired_delta']} vs {res_parallel['paired_delta']}"
    )
    assert res_serial["action_digest"] == res_parallel["action_digest"], (
        f"Action digest mismatch: {res_serial['action_digest']} vs {res_parallel['action_digest']}"
    )
    assert res_serial["completion_status"] == "COMPLETED"
    assert res_parallel["completion_status"] == "COMPLETED"
