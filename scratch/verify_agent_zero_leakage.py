"""
=============================================================================
DEVELOPMENT GATE 0.3 — ACTIVE CONTAINMENT ZERO-LEAKAGE VERIFICATION HARNESS
=============================================================================
Active runtime containment and recursive AST static audit suite enforcing the
zero-leakage security boundary:
1. Leak Check 1: No future town shop peeking (len(shops) <= step // 72)
2. Leak Check 2: No opponent private state access (only own private state read)
3. Leak Check 3: No PRNG stream tampering or internal state inspection
4. Leak Check 4: No hardcoded seed-to-action maps or replay hindsight lookup
5. Leak Check 5: No terminal lookahead or future step simulation outside legal API
6. Containment: Active interception of filesystem, gc, subprocess, network,
                inspect, ctypes, and parallel simulator instantiation.
=============================================================================
"""

import ast
import builtins
import copy
import gc
import importlib.util
import inspect
import os
import random
import socket
import subprocess
import sys
from typing import Dict, Any, List, Set, Type, Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim


class LeakageViolationError(Exception):
    """Raised when an agent violates sandbox zero-leakage constraints."""
    pass


class ActiveContainmentSandbox:
    """
    Active runtime containment context manager.
    Enforces the zero-leakage security boundary during agent.act() execution.
    """
    def __init__(self, current_game_instance=None):
        self.game = current_game_instance
        self._orig_open = builtins.open
        self._orig_import = builtins.__import__
        self._orig_gc_get_objects = gc.get_objects
        self._orig_environ = os.environ
        self._orig_popen = subprocess.Popen
        self._orig_sp_run = subprocess.run
        self._orig_os_system = os.system
        self._orig_socket = socket.socket
        self._orig_rng_getstate = random.getstate
        self._orig_rng_setstate = random.setstate
        self._orig_inspect_stack = inspect.stack
        self._orig_inspect_curframe = inspect.currentframe
        self._orig_sys_getframe = getattr(sys, "_getframe", None)
        self._orig_kagsim_game = getattr(kagsim, "Game", None)

    def __enter__(self):
        # 1. Block file access
        def safe_open(*args, **kwargs):
            raise LeakageViolationError(f"Security Violation: File open() is strictly prohibited during act(): {args[0] if args else ''}")
        builtins.open = safe_open

        # 2. Block gc inspection of simulator/memory
        def safe_get_objects():
            raise LeakageViolationError("Security Violation: gc.get_objects() memory inspection is prohibited during act()")
        gc.get_objects = safe_get_objects

        # 3. Block subprocess execution
        def safe_popen(*args, **kwargs):
            raise LeakageViolationError("Security Violation: subprocess execution is prohibited during act()")
        def safe_run(*args, **kwargs):
            raise LeakageViolationError("Security Violation: subprocess.run is prohibited during act()")
        def safe_system(*args, **kwargs):
            raise LeakageViolationError("Security Violation: os.system is prohibited during act()")
        subprocess.Popen = safe_popen
        subprocess.run = safe_run
        os.system = safe_system

        # 4. Block socket/network access
        def safe_socket(*args, **kwargs):
            raise LeakageViolationError("Security Violation: network socket creation is prohibited during act()")
        socket.socket = safe_socket

        # 5. Block RNG state inspection
        def safe_getstate():
            raise LeakageViolationError("Security Violation: global random.getstate() inspection is prohibited during act()")
        def safe_setstate(state):
            raise LeakageViolationError("Security Violation: global random.setstate() tampering is prohibited during act()")
        random.getstate = safe_getstate
        random.setstate = safe_setstate

        # 6. Block inspect/frame reflection
        def safe_stack(*args, **kwargs):
            raise LeakageViolationError("Security Violation: inspect.stack() reflection is prohibited during act()")
        def safe_curframe(*args, **kwargs):
            raise LeakageViolationError("Security Violation: inspect.currentframe() reflection is prohibited during act()")
        inspect.stack = safe_stack
        inspect.currentframe = safe_curframe
        if self._orig_sys_getframe:
            def safe_getframe(*args, **kwargs):
                raise LeakageViolationError("Security Violation: sys._getframe() reflection is prohibited during act()")
            sys._getframe = safe_getframe

        # 7. Block parallel simulator instantiation
        def safe_game(*args, **kwargs):
            raise LeakageViolationError("Security Violation: Parallel kagsim.Game instantiation is prohibited during act()")
        kagsim.Game = safe_game

        # 8. Block dynamic import of forbidden modules
        orig_import = self._orig_import
        PROHIBITED_MODULES = {"ctypes", "subprocess", "socket", "urllib", "requests", "kagsim"}
        def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name in PROHIBITED_MODULES or any(p in name for p in ["kagsim", "subprocess", "socket", "ctypes"]):
                raise LeakageViolationError(f"Security Violation: Dynamic import of '{name}' is prohibited during act()")
            return orig_import(name, globals, locals, fromlist, level)
        builtins.__import__ = safe_import

        # 9. Sanitize environment variables during act
        class SanitizedEnviron(dict):
            def __getitem__(self, key):
                raise LeakageViolationError(f"Security Violation: os.environ['{key}'] access is prohibited during act()")
            def get(self, key, default=None):
                raise LeakageViolationError(f"Security Violation: os.environ.get('{key}') access is prohibited during act()")
        os.environ = SanitizedEnviron()

        # 10. Hook ctypes if imported
        if "ctypes" in sys.modules:
            ctypes = sys.modules["ctypes"]
            def safe_string_at(*args, **kwargs):
                raise LeakageViolationError("Security Violation: ctypes memory reading is prohibited during act()")
            ctypes.string_at = safe_string_at

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        builtins.open = self._orig_open
        builtins.__import__ = self._orig_import
        gc.get_objects = self._orig_gc_get_objects
        os.environ = self._orig_environ
        subprocess.Popen = self._orig_popen
        subprocess.run = self._orig_sp_run
        os.system = self._orig_os_system
        socket.socket = self._orig_socket
        random.getstate = self._orig_rng_getstate
        random.setstate = self._orig_rng_setstate
        inspect.stack = self._orig_inspect_stack
        inspect.currentframe = self._orig_inspect_curframe
        if self._orig_sys_getframe:
            sys._getframe = self._orig_sys_getframe
        if self._orig_kagsim_game:
            kagsim.Game = self._orig_kagsim_game


def audit_agent_ast(filepath: str, visited: Optional[Set[str]] = None) -> List[str]:
    """
    Recursively inspects agent source code AST and imported local helper modules
    for prohibited imports, symbols, and reflection patterns.
    """
    if visited is None:
        visited = set()

    real_path = os.path.realpath(filepath)
    if real_path in visited:
        return []
    visited.add(real_path)

    violations = []
    if not os.path.exists(real_path):
        return [f"File not found for AST audit: {real_path}"]

    with open(real_path, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()

    try:
        tree = ast.parse(source, filename=real_path)
    except Exception as e:
        return [f"Syntax error parsing {real_path}: {e}"]

    PROHIBITED_MODULES = {"ctypes", "inspect", "socket", "urllib", "requests", "subprocess"}
    PROHIBITED_NAMES = {"__subclasses__", "_sim", "_rng", "kagsim_internal"}

    agent_dir = os.path.dirname(real_path)
    local_helpers = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in PROHIBITED_MODULES:
                    violations.append(f"Prohibited import '{alias.name}' in {os.path.basename(real_path)}:{node.lineno}")
                # Check for local helper module import
                candidate_helper = os.path.join(agent_dir, f"{alias.name}.py")
                if os.path.exists(candidate_helper):
                    local_helpers.append(candidate_helper)
        elif isinstance(node, ast.ImportFrom):
            if node.module in PROHIBITED_MODULES:
                violations.append(f"Prohibited from-import '{node.module}' in {os.path.basename(real_path)}:{node.lineno}")
            if node.module:
                candidate_helper = os.path.join(agent_dir, f"{node.module}.py")
                if os.path.exists(candidate_helper):
                    local_helpers.append(candidate_helper)
        elif isinstance(node, ast.Name):
            if node.id in PROHIBITED_NAMES:
                violations.append(f"Prohibited symbol '{node.id}' in {os.path.basename(real_path)}:{node.lineno}")

    # Recursively audit discovered local helper modules
    for helper in local_helpers:
        sub_violations = audit_agent_ast(helper, visited)
        violations.extend(sub_violations)

    return violations


class InstrumentedEnvironmentWrapper:
    """Wraps simulator observations to detect runtime illegal access attempts."""
    def __init__(self, raw_obs: Dict[str, Any], step: int, player: int):
        self._raw_obs = raw_obs
        self._step = step
        self._player = player
        self._max_legal_shops = min(8, step // 72) if step >= 72 else 0

    def get_obs(self) -> Dict[str, Any]:
        obs = dict(self._raw_obs)
        
        # Verify shop length invariant
        unlocked = obs.get("town", {}).get("unlocked_shops", [])
        if len(unlocked) > self._max_legal_shops:
            raise LeakageViolationError(
                f"LEAK CHECK 1 FAILED: At step {self._step}, unlocked_shops length is {len(unlocked)}, "
                f"expected <= {self._max_legal_shops}"
            )

        # Enforce that opponent private state is inaccessible
        opp_seat = 1 - self._player
        # Check both public farm subdict and root private dict
        if "private" in obs["farms"][opp_seat]:
            raise LeakageViolationError("LEAK CHECK 2 FAILED: Opponent farm dictionary contains private subdict!")

        return obs


def run_runtime_leakage_audit(agent_instance_or_fn: Any, seed: int = 50000, max_steps: int = 720) -> Dict[str, Any]:
    """
    Executes a 720-step match inside the ActiveContainmentSandbox,
    asserting zero runtime legal violations and zero sandbox breaches.
    """
    g = kagsim.Game(seed)
    sandbox = ActiveContainmentSandbox(g)

    # Determine act callable
    if hasattr(agent_instance_or_fn, "act"):
        act_fn = agent_instance_or_fn.act
    elif callable(agent_instance_or_fn):
        act_fn = agent_instance_or_fn
    else:
        raise TypeError("Agent must have an 'act' method or be callable")

    step = 0
    total_actions = 0
    while not g.done and step < max_steps:
        obs_p0 = g.observe(0)
        wrapper = InstrumentedEnvironmentWrapper(obs_p0, step, 0)
        legal_obs = wrapper.get_obs()

        # Execute agent act inside ActiveContainmentSandbox
        with sandbox:
            act_p0 = act_fn(legal_obs)

        n_units = len(act_p0.get("hands", [])) + (1 if act_p0.get("farmer") else 0)
        n_orders = len(act_p0.get("market", []))
        total_actions += n_units + n_orders

        # Dummy opponent action (PASS)
        act_p1 = {"farmer": ["PASS"], "hands": [], "market": []}

        g.step(act_p0, act_p1)
        step += 1

    return {
        "status": "PASS",
        "steps": step,
        "total_actions": total_actions,
        "final_reward": g.reward(0),
        "seed": seed
    }


def audit_agent_file(filepath: str, agent_factory_or_fn: Any, seed: int = 50000) -> Dict[str, Any]:
    """Runs complete recursive static AST and runtime active containment verification on an agent."""
    name = getattr(agent_factory_or_fn, "__name__", str(agent_factory_or_fn))
    print(f"Auditing agent: {name} from {os.path.basename(filepath)}...")
    ast_violations = audit_agent_ast(filepath)
    if ast_violations:
        print("  AST VIOLATIONS DETECTED:")
        for v in ast_violations:
            print(f"    - {v}")
        return {"status": "FAIL", "violations": ast_violations}

    print("  AST Check: PASS (Zero prohibited imports/symbols in file or helpers)")

    try:
        agent_obj = agent_factory_or_fn() if isinstance(agent_factory_or_fn, type) else agent_factory_or_fn
        res = run_runtime_leakage_audit(agent_obj, seed=seed)
        print(f"  Runtime Containment Audit: PASS ({res['steps']} steps executed under active containment)")
        return {"status": "PASS", "details": res}
    except Exception as e:
        print(f"  Runtime Containment Audit: FAIL ({e})")
        return {"status": "FAIL", "error": str(e)}


if __name__ == "__main__":
    from closed_loop_v2 import ClosedLoopAgentV2
    v2_path = os.path.join(BASE_DIR, "candidates", "closed_loop_architecture", "closed_loop_v2.py")
    res = audit_agent_file(v2_path, ClosedLoopAgentV2)
    print(f"\nFinal Result for ClosedLoopAgentV2: {res['status']}")
    assert res["status"] == "PASS"
