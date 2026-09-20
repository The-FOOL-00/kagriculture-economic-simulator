# SPDX-License-Identifier: MIT
"""Phase 022R1: competition-loader contract regression test (§5).

Simulates the real competition loader against the PACKAGED artifact only:
- no __file__ in the exec namespace (exact KE get_last_callable semantics)
- no repository imports (subprocess isolation; packaged aec proven by path)
- no working-directory assumptions (cwd is the scratch dir, harness-owned)
- no network, no external service, no development environment

Covers: import/load, initial observation, first action, multiple turns,
full game, terminal reward. Asserts: no exception, not-always-PASS, real AEC
execution, normal termination.
"""

import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import tokenize
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ARCHIVE = REPO_ROOT / "submission_aec_v22r1.tar.gz"
SMOKE_SEED = 249376  # consumed fresh-cohort seed; RELEASE_SMOKE_ONLY use
MIN_V3_SCALE_REWARD = 10_000.0

DRIVER = r'''
import json, os, sys, tarfile, tempfile

archive, episode_steps, seed, out_path = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
report = {"ok": True, "errors": []}

# The ONLY importable project path is the extraction dir (mirrors KE exec_dir).
work = tempfile.mkdtemp(prefix="v22r1_loader_")
with tarfile.open(archive, "r:gz") as tar:
    tar.extractall(work)
# Mirror KE get_last_callable exactly: exec_dir appended during exec, popped after.
sys.path.append(work)
report["exec_dir_on_path_during_exec"] = True

# Prove no repository leakage: repo root must not be importable here.
repo_markers = [p for p in sys.path if os.path.basename(os.path.normpath(p)) == "Kagriculture"]
report["repo_on_path"] = repo_markers

source = open(os.path.join(work, "main.py"), encoding="utf-8").read()
namespace = {"__name__": "__main__"}  # NO __file__, NO __package__, NO module path
try:
    exec(compile(source, "main.py", "exec"), namespace)
    report["load_exception"] = None
    sys.path.pop()  # KE pops exec_dir after exec; sys.modules retains imports
except BaseException as e:
    report["ok"] = False
    report["errors"].append(f"load: {type(e).__name__}: {e}")
    report["load_exception"] = f"{type(e).__name__}: {e}"

report["dunder_file_leaked"] = "__file__" in namespace
agent = [v for v in namespace.values() if callable(v)][-1] if report["load_exception"] is None else None
report["agent_defined"] = callable(agent)

import aec.integration.executor as _exe
report["aec_module_file"] = getattr(_exe, "__file__", None)
report["aec_from_package"] = bool(report["aec_module_file"]) and os.path.realpath(report["aec_module_file"]).startswith(os.path.realpath(work))

import tarfile as _tar
_v3dir = os.path.join(work, "_v3ref")
os.makedirs(_v3dir, exist_ok=True)
with _tar.open(os.path.join(work, "submission_Vj_kc_v3.tar.gz"), "r:gz") as _t:
    _t.extractall(_v3dir)
v3_path = os.path.join(_v3dir, "main.py")
report["v3_opponent_from_package"] = os.path.isfile(v3_path)

from kaggle_environments import make
env = make("kaggriculture", configuration={"episodeSteps": episode_steps, "seed": seed}, debug=True)
try:
    # Treatment (loader-simulated) vs packaged V3 reference (Phase 022 design).
    env.run([agent, v3_path])
    report["run_exception"] = None
except BaseException as e:
    report["ok"] = False
    report["errors"].append(f"run: {type(e).__name__}: {e}")
    report["run_exception"] = f"{type(e).__name__}: {e}"

if report["run_exception"] is None:
    last = env.steps[-1]
    report["p0_status"] = last[0].status
    report["p1_status"] = last[1].status
    report["p0_reward"] = last[0].reward
    report["p1_reward"] = last[1].reward
    report["n_steps"] = len(env.steps)
    seq = []
    for st in env.steps:
        a = st[0].action
        try:
            d = a.to_dict() if hasattr(a, "to_dict") else dict(a)
        except Exception:
            d = {}
        seq.append(d)
    report["all_pass_corpse"] = all(
        (not s.get("market")) and all(h == ["PASS"] for h in (s.get("hands") or [])) and (s.get("farmer") == ["PASS"])
        for s in seq
    )
    report["distinct_actions"] = len({json.dumps(s, sort_keys=True, default=str) for s in seq})
    exe = namespace.get("_EXECUTOR")
    hist = getattr(exe, "_telemetry_history", []) if exe is not None else []
    decisions = {}
    commits = 0
    mechs = {}
    for t in hist:
        decisions[t.decision] = decisions.get(t.decision, 0) + 1
        for c in t.candidates:
            if c.commit_decision:
                commits += 1
                mechs[c.mechanism_family] = mechs.get(c.mechanism_family, 0) + 1
    report["executor_alive"] = exe is not None
    report["decisions"] = decisions
    report["commits"] = commits
    report["commit_mechanisms"] = mechs

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(report, f)
'''


def _run_driver(episode_steps: int, seed: int) -> dict:
    assert ARCHIVE.exists(), f"V22R1 archive missing: {ARCHIVE}"
    with tempfile.TemporaryDirectory(prefix="v22r1_pytest_") as tmp:
        driver_path = os.path.join(tmp, "driver.py")
        out_path = os.path.join(tmp, "report.json")
        with open(driver_path, "w", encoding="utf-8") as f:
            f.write(DRIVER)
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        proc = subprocess.run(
            [sys.executable, driver_path, str(ARCHIVE), str(episode_steps), str(seed), out_path],
            cwd=tmp, env=env, capture_output=True, text=True, timeout=1500,
        )
        assert proc.returncode == 0, f"loader driver crashed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        with open(out_path, "r", encoding="utf-8") as f:
            return json.load(f)


def test_entrypoint_has_no_unconditional_dunder_file():
    """Static: packaged main.py must not use bare __file__ (V22 root cause)."""
    assert ARCHIVE.exists(), f"V22R1 archive missing: {ARCHIVE}"
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(ARCHIVE, "r:gz") as tar:
            tar.extractall(tmp, members=[m for m in tar.getmembers() if m.name == "main.py"])
        src = Path(tmp, "main.py").read_text(encoding="utf-8")
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.NAME and tok.string == "__file__":
            line = tok.line or ""
            assert "globals().get" in line or "getattr(" in line, \
                f"unguarded __file__ at main.py:{tok.start[0]}: {line.strip()}"


def test_competition_loader_import_and_first_actions():
    """Bare-exec load + initial obs + first actions + multiple turns (short game)."""
    rep = _run_driver(episode_steps=12, seed=SMOKE_SEED)
    assert rep["load_exception"] is None, f"loader exec failed: {rep['load_exception']}"
    assert not rep["dunder_file_leaked"], "__file__ leaked into loader namespace"
    assert rep["agent_defined"], "no agent callable defined by packaged main.py"
    assert rep["aec_from_package"], f"aec not loaded from package: {rep['aec_module_file']}"
    assert rep["v3_opponent_from_package"], "V3 opponent not loaded from packaged tarball"
    assert rep["run_exception"] is None, f"short game failed: {rep['run_exception']}"
    assert rep["n_steps"] == 12, f"expected 12 turns, got {rep['n_steps']}"
    assert rep["executor_alive"], "packaged executor never instantiated (dead agent?)"
    assert rep["distinct_actions"] >= 1


def test_competition_loader_full_game_terminal_reward():
    """Full 720-step game under loader semantics: real behavior, DONE, V3-scale.

    Uses seed 249380 (consumed cohort), where the foundation commits real
    market-timing interventions — proving AEC decisions execute end-to-end
    through the loader, not merely backbone passthrough.
    """
    rep = _run_driver(episode_steps=720, seed=249380)
    assert rep["load_exception"] is None, f"loader exec failed: {rep['load_exception']}"
    assert rep["run_exception"] is None, f"full game failed: {rep['run_exception']}"
    assert rep["p0_status"] == "DONE" and rep["p1_status"] == "DONE", \
        f"abnormal termination: {rep['p0_status']}/{rep['p1_status']}"
    assert rep["aec_from_package"], "aec not loaded from packaged source"
    assert rep["v3_opponent_from_package"], "V3 opponent not loaded from packaged tarball"
    assert rep["p0_reward"] is not None and rep["p0_reward"] > MIN_V3_SCALE_REWARD, \
        f"corpse-scale reward ${rep['p0_reward']} (bar ${MIN_V3_SCALE_REWARD})"
    assert not rep["all_pass_corpse"], "every action degraded to all-PASS (V22 failure mode)"
    assert rep["executor_alive"], "packaged executor never ran"
    assert rep["commits"] > 0, "no AEC intervention committed through the loader"
    assert set(rep["commit_mechanisms"]) <= {
        "DEPENDENCY_AWARE_MARKET_TIMING", "TERMINAL_LIQUIDATION", "PHASE_SHUTDOWN",
    }, rep["commit_mechanisms"]
    # KE convention: with episodeSteps=N the agent is called N-1 times
    # (steps 0..N-2); the final env.steps entry is terminal with no agent call.
    assert sum(rep["decisions"].values()) == rep["n_steps"] - 1, \
        f"telemetry steps {rep['decisions']} != agent decisions {rep['n_steps'] - 1}"
    assert set(rep["decisions"]) <= {"BACKBONE", "ABSTAIN", "COMMIT"}, rep["decisions"]
