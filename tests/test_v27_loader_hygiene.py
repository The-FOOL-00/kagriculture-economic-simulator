# SPDX-License-Identifier: MIT
"""V27: loader hygiene (file-loader order-dependence + adapter hermeticity).

Integration tests (run real matches, ~60-90s total):
  1. A 1-step P2 primer flips a file-loader P3 match to the stale
     DISC-P3 checkpoint row (documents the V25 harness artifact and pins
     the minimal reproducer).
  2. Hermetic adapters are history-independent (filler matches between
     identical adapter matches change nothing).
  3. File loader and adapter agree bit-exactly on a full game (extends
     V26's 50-step equivalence certificate to 719 turns).
"""

import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tarfile
import tempfile
import time

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from aec.backbone.v3_adapter import V3BackboneAdapter  # noqa: E402
from aec.backbone.v25_p3_adapter import V25P3BackboneAdapter  # noqa: E402
from kaggle_environments import make  # noqa: E402

V3_TAR = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
P3_FILE = os.path.join(REPO_ROOT, "candidates", "v25_p3_unified.py")

FRESH_DELTA = 1145.0   # history-free P3:A/249431/s0 (F2 DISC-P3')
FRESH_DIGEST = "e631d38d557d341b"
STALE_DELTA = 1286.0   # P2-residue DISC-P3 checkpoint row
STALE_DIGEST = "3d5a28604da33861"


def vendor_p2():
    import subprocess
    dest_dir = "/tmp/v27_vendor"
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, "v25_p2_production.py")
    if not os.path.exists(dest):
        blob = subprocess.run(
            ["git", "show", "research/v25-coherent-planner:candidates/v25_p2_production.py"],
            cwd=REPO_ROOT, capture_output=True, check=True).stdout
        with open(dest, "wb") as f:
            f.write(blob)
    return dest


def load_agent(path, tag):
    spec = importlib.util.spec_from_file_location(f"{tag}_{time.time_ns()}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def play_file(cand_path, seed, seat, episode_steps=None):
    work = tempfile.mkdtemp(prefix="v27test_")
    try:
        with tarfile.open(V3_TAR, "r:gz") as tar:
            tar.extractall(work)
        v3 = load_agent(os.path.join(work, "main.py"), "v3")
        cand = load_agent(cand_path, "cand")
        cfg = {"seed": seed}
        if episode_steps:
            cfg["episodeSteps"] = episode_steps
        env = make("kaggriculture", configuration=cfg)
        env.run([cand, v3] if seat == 0 else [v3, cand])
        return env
    finally:
        shutil.rmtree(work, ignore_errors=True)


def digest_of(env, seat):
    acts = [s[seat].get("action") for s in env.steps]
    return hashlib.sha256(json.dumps(acts, sort_keys=True).encode()).hexdigest()


@pytest.fixture(autouse=True)
def _fresh_module_cache():
    """Isolate the process-global `import main` V3 cache per test.

    The file loader resolves V3 through sys.modules['main']; without
    isolation, test order would change results (the V25 artifact itself).
    """
    saved_main = sys.modules.pop("main", None)
    saved_path = list(sys.path)
    try:
        yield
    finally:
        sys.modules.pop("main", None)
        if saved_main is not None:
            sys.modules["main"] = saved_main
        sys.path[:] = saved_path


def play_adapter(seed, seat):
    p3 = V25P3BackboneAdapter()
    v3 = V3BackboneAdapter()
    a = lambda o, c=None: p3.act(o, c)  # noqa: E731
    b = lambda o, c=None: v3.act(o, c)  # noqa: E731
    env = make("kaggriculture", configuration={"seed": seed})
    env.run([a, b] if seat == 0 else [b, a])
    return env


class TestFileLoaderOrderDependence:
    def test_one_step_p2_primer_flips_target(self):
        # Fresh control first (module never saw step 0 via P2).
        assert "main" not in sys.modules
        env = play_file(P3_FILE, 249431, 0)
        r0, r1 = env.steps[-1][0]["reward"], env.steps[-1][1]["reward"]
        assert (r0 - r1) == FRESH_DELTA
        assert digest_of(env, 0).startswith(FRESH_DIGEST)
        # 1-step P2 primer (its V3 call at step 0 contaminates the cache).
        play_file(vendor_p2(), 249430, 0, episode_steps=1)
        env2 = play_file(P3_FILE, 249431, 0)
        s0, s1 = env2.steps[-1][0]["reward"], env2.steps[-1][1]["reward"]
        assert (s0 - s1) == STALE_DELTA
        assert digest_of(env2, 0).startswith(STALE_DIGEST)

    def test_file_loader_matches_adapter_full_game(self):
        assert "main" not in sys.modules
        env_f = play_file(P3_FILE, 249430, 0)
        env_a = play_adapter(249430, 0)
        assert env_f.steps[-1][0]["reward"] == env_a.steps[-1][0]["reward"]
        assert env_f.steps[-1][1]["reward"] == env_a.steps[-1][1]["reward"]
        assert digest_of(env_f, 0) == digest_of(env_a, 0)


class TestAdapterHermeticity:
    def test_adapter_history_independent(self):
        e1 = play_adapter(249431, 0)
        d1 = (digest_of(e1, 0), e1.steps[-1][0]["reward"], e1.steps[-1][1]["reward"])
        # filler matches (would contaminate a file-loader worker)
        play_adapter(249430, 1)
        play_adapter(249463, 0)
        e2 = play_adapter(249431, 0)
        d2 = (digest_of(e2, 0), e2.steps[-1][0]["reward"], e2.steps[-1][1]["reward"])
        assert d1 == d2
