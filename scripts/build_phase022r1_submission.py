#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 022R1: Repaired Submission Packager & Hardened Integrity Verifier.

Builds submission_aec_v22r1.tar.gz (V22 is RETIRED, never overwritten) with:
1. Loader-safe root main.py (no unconditional __file__; see template below).
2. Bit-exact frozen V3 tarball (SHA 845e0d10...).
3. Byte-identical aec/ runtime (economics frozen; entrypoint-only repair).
4. LF line endings.
5. Hardened QA: bare-exec loader simulation, KE full-game vs starter with
   V3-scale reward bar, KE head-to-head vs V3 reference, packaged determinism
   (rewards + full action sequences), coarse latency sanity, both rewards
   recorded, agent stderr surfaced (debug=True fails loudly on any agent
   exception).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
import time
from typing import Any, Dict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
V3_EXPECTED_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
OUTPUT_TARBALL = os.path.join(REPO_ROOT, "submission_aec_v22r1.tar.gz")
RETIRED_TARBALL = os.path.join(REPO_ROOT, "submission_aec_v22.tar.gz")

# QA bars (grounded in measured V22R1 behavior on the release machine;
# corpse signature is $3,000.00 at ~7 ms/step; live is V3-scale at ~54 ms/step).
MIN_V3_SCALE_REWARD = 10_000.0
STARTING_MONEY = 3_000.0
MIN_AVG_STEP_MS = 15.0
MAX_AVG_STEP_MS = 2_000.0
QA_SEED = 249376  # consumed fresh-cohort seed; RELEASE_SMOKE_ONLY use

SUBMISSION_MAIN_CODE = '''# SPDX-License-Identifier: MIT
"""Kagriculture Competition Entrypoint — AEC Robust Qualified Foundation (V22R1).

Loader-safe entrypoint. The competition loader executes this source in a bare
namespace WITHOUT __file__ (kaggle_environments/agent.py:get_last_callable
uses exec(source) with only an exec_dir sys.path entry during exec). Nothing
here assumes __file__ exists:

- sys.path fallback is append-only (never shadows an already-configured path)
  and engages only for directories validated by submission markers.
- The V3 tarball is located by ordered, existence-validated candidates; when
  none resolve, the config default is kept and BackboneAdapter resolves the
  tarball relative to its own (real, imported) module file — the same file.
- No cwd, repo-layout, or absolute-path assumptions anywhere.
"""

import os
import sys
from typing import Any, Dict, Optional

_V3_ARCHIVE_NAME = "submission_Vj_kc_v3.tar.gz"


def _submission_root_candidates():
    """Ordered candidate submission roots. Never raises for missing __file__."""
    roots = []
    f = globals().get("__file__")
    if isinstance(f, str) and f:
        roots.append(os.path.dirname(os.path.abspath(f)))
    try:
        code_file = _submission_root_candidates.__code__.co_filename
    except Exception:
        code_file = None
    if isinstance(code_file, str) and code_file not in ("", "<string>"):
        roots.append(os.path.dirname(os.path.abspath(code_file)))
    return roots


def _looks_like_submission_root(d):
    """True only if d contains the submission markers (validated, not assumed)."""
    try:
        return (
            isinstance(d, str)
            and bool(d)
            and os.path.isfile(os.path.join(d, "aec", "__init__.py"))
            and os.path.isfile(os.path.join(d, _V3_ARCHIVE_NAME))
        )
    except Exception:
        return False


for _root in _submission_root_candidates():
    if _looks_like_submission_root(_root) and _root not in sys.path:
        sys.path.append(_root)

from aec.config import build_robust_qualified_config
from aec.integration.executor import AECExecutor

_EXECUTOR: Optional[AECExecutor] = None


def _find_v3_tarball(configuration=None):
    """Locate the bundled V3 tarball without assuming __file__.

    Ordered candidates (first existing file wins):
    1. __file__-derived / code-filename-derived submission roots.
    2. The imported aec package location (same derivation BackboneAdapter uses).
    3. The KE-injected configuration['__raw_path__'] agent path directory.
    Returns None when nothing resolves; the caller then keeps the config
    default, which BackboneAdapter resolves relative to its own module file.
    """
    cands = []
    for _r in _submission_root_candidates():
        cands.append(os.path.join(_r, _V3_ARCHIVE_NAME))
    try:
        import aec.integration.backbone_adapter as _ba
        _bf = getattr(_ba, "__file__", None)
        if isinstance(_bf, str) and _bf:
            _bd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(_bf))))
            cands.append(os.path.join(_bd, _V3_ARCHIVE_NAME))
    except Exception:
        pass
    try:
        _raw = configuration.get("__raw_path__") if configuration is not None else None
    except Exception:
        _raw = None
    if isinstance(_raw, str) and _raw and os.path.isfile(_raw):
        cands.append(os.path.join(os.path.dirname(os.path.abspath(_raw)), _V3_ARCHIVE_NAME))
    for c in cands:
        try:
            if c and os.path.isfile(c):
                return c
        except Exception:
            pass
    return None


def agent(observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Kaggle competition agent entrypoint (V22R1, loader-safe)."""
    global _EXECUTOR
    step = int(observation.get("step", 0) or 0)

    if _EXECUTOR is None or step == 0:
        cfg = build_robust_qualified_config()
        local_v3 = _find_v3_tarball(configuration)
        if local_v3:
            cfg.v3_tarball_path = local_v3
        _EXECUTOR = AECExecutor(config=cfg)

    return _EXECUTOR.act(observation, configuration)
'''


def sha256_of_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def build_submission_tarball() -> str:
    """Package the repaired entrypoint + frozen runtime into v22r1 archive."""
    print(">>> Packaging submission_aec_v22r1.tar.gz (V22 retired, untouched)...")
    if not os.path.exists(RETIRED_TARBALL):
        print("  [WARN] retired V22 archive not found (expected to exist, kept for traceability).")

    v3_sha = sha256_of_file(V3_TARBALL_PATH)
    if v3_sha != V3_EXPECTED_SHA:
        raise RuntimeError(f"FATAL: V3 SHA256 mismatch before packaging: {v3_sha} != {V3_EXPECTED_SHA}")

    with tempfile.TemporaryDirectory() as staging:
        main_path = os.path.join(staging, "main.py")
        with open(main_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(SUBMISSION_MAIN_CODE)

        aec_src = os.path.join(REPO_ROOT, "aec")
        aec_dst = os.path.join(staging, "aec")
        shutil.copytree(aec_src, aec_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))

        shutil.copy2(os.path.join(REPO_ROOT, "config.py"), os.path.join(staging, "config.py"))

        ext_src = os.path.join(REPO_ROOT, "extracted_agents", "dmitrii_lb2800")
        ext_dst = os.path.join(staging, "extracted_agents", "dmitrii_lb2800")
        shutil.copytree(ext_src, ext_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))

        shutil.copy2(V3_TARBALL_PATH, os.path.join(staging, "submission_Vj_kc_v3.tar.gz"))

        with tarfile.open(OUTPUT_TARBALL, "w:gz") as tar:
            for item in sorted(os.listdir(staging)):
                full_p = os.path.join(staging, item)
                tar.add(full_p, arcname=item)

    tar_sha = sha256_of_file(OUTPUT_TARBALL)
    tar_size = os.path.getsize(OUTPUT_TARBALL)
    print(f"  Successfully built: {OUTPUT_TARBALL}")
    print(f"  Size: {tar_size:,} bytes")
    print(f"  SHA-256: {tar_sha}")
    return tar_sha


def _p0_action_sequence(env) -> list:
    seq = []
    for step in env.steps:
        a = step[0].action
        try:
            d = a.to_dict() if hasattr(a, "to_dict") else dict(a)
        except Exception:
            d = repr(a)
        seq.append(json.dumps(d, sort_keys=True, default=str))
    return seq


def verify_submission_integrity(tar_path: str) -> Dict[str, Any]:
    """Hardened QA audit on the repaired submission archive."""
    print("\n>>> Verifying Submission Integrity (hardened QA)...")
    results: Dict[str, Any] = {"tarball": tar_path}

    with tempfile.TemporaryDirectory() as test_dir:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(test_dir)
            archive_members = tar.getnames()

        print(f"  Extracted {len(archive_members)} archive members.")
        assert "main.py" in archive_members, "FATAL: main.py missing from archive root!"
        assert any(m.startswith("aec") for m in archive_members), "FATAL: aec/ package missing!"
        assert "submission_Vj_kc_v3.tar.gz" in archive_members, "FATAL: V3 tarball missing!"

        extracted_v3 = os.path.join(test_dir, "submission_Vj_kc_v3.tar.gz")
        extracted_v3_sha = sha256_of_file(extracted_v3)
        assert extracted_v3_sha == V3_EXPECTED_SHA, f"FATAL: V3 SHA256 mismatch! {extracted_v3_sha}"
        print("  [OK] Bundled V3 SHA256 verified bit-identical.")

        main_py = os.path.join(test_dir, "main.py")
        with open(main_py, "rb") as f:
            raw_main = f.read()
        assert b"\r\n" not in raw_main, "FATAL: CRLF line endings in packaged main.py!"
        main_src = raw_main.decode("utf-8")
        # No unconditional __file__: every CODE occurrence must sit inside a
        # guarded globals().get('__file__') / getattr(..., '__file__', ...)
        # access (docstring/comment mentions ignored via tokenize).
        import io
        import tokenize
        for tok in tokenize.generate_tokens(io.StringIO(main_src).readline):
            if tok.type == tokenize.NAME and tok.string == "__file__":
                line = tok.line or ""
                if "globals().get" not in line and "getattr(" not in line:
                    raise AssertionError(
                        f"FATAL: unguarded __file__ use at main.py:{tok.start[0]}: {line.strip()}")
        print("  [OK] Entrypoint has no unconditional __file__ dependency (LF endings).")

        forbidden_patterns = ["C:\\Users", "/home/", "/Users/", "Sundareswaran"]
        forbidden_modules = ["torch", "tensorflow", "sklearn", "matplotlib", "scipy",
                             "socket", "urllib", "requests", "http.client", "http.server"]
        scan_warnings = []
        for root, _, files in os.walk(test_dir):
            for file in files:
                if file.endswith(".py"):
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, test_dir)
                    with open(full_p, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    for pat in forbidden_patterns:
                        if pat in content:
                            scan_warnings.append(f"Hardcoded path string '{pat}' in {rel_p}")
                    for mod in forbidden_modules:
                        if f"import {mod}" in content or f"from {mod}" in content:
                            scan_warnings.append(f"Heavy/network dependency '{mod}' imported in {rel_p}")
        assert not scan_warnings, f"FATAL: portability scan failed: {scan_warnings[:5]}"
        print("  [OK] Zero absolute user paths, zero heavy/network dependencies.")

        # Packaged config defaults (quarantine governance).
        sys.path.insert(0, test_dir)
        try:
            import importlib
            for mod in [m for m in list(sys.modules) if m == "aec" or m.startswith("aec.")]:
                del sys.modules[mod]
            from aec.config import build_robust_qualified_config
            _qcfg = build_robust_qualified_config()
            assert tuple(_qcfg.enabled_mechanisms) == (
                "DEPENDENCY_AWARE_MARKET_TIMING", "TERMINAL_LIQUIDATION", "PHASE_SHUTDOWN"), \
                f"FATAL: packaged enabled_mechanisms = {_qcfg.enabled_mechanisms}"
            assert _qcfg.frozen_mode is True, "FATAL: packaged frozen_mode is not True!"
            assert _qcfg.enable_tranche_synthesizer is False, "FATAL: tranche enabled!"
            assert _qcfg.enable_asset_holding_trigger is False, "FATAL: asset-holding enabled!"
        finally:
            sys.path.remove(test_dir)
            for mod in [m for m in list(sys.modules) if m == "aec" or m.startswith("aec.")]:
                del sys.modules[mod]
        print("  [OK] Packaged config: 3 foundation mechanisms, frozen, quarantines off.")

        from kaggle_environments import make

        # --- Bare-exec loader simulation (exact competition semantics) ---
        print("  Running bare-exec loader simulation (no __file__)...")
        ns: Dict[str, Any] = {"__name__": "__main__"}
        sys.path.append(test_dir)  # mirrors KE exec_dir handling during exec
        try:
            exec(compile(main_src, "main.py", "exec"), ns)
        finally:
            sys.path.pop()
        assert "__file__" not in ns, "FATAL: harness leaked __file__ into namespace!"
        loaded_agent = [v for v in ns.values() if callable(v)][-1]
        assert callable(loaded_agent), "FATAL: no agent callable defined by bare exec!"
        probe_env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": QA_SEED})
        obs0 = probe_env.reset()
        first_action = loaded_agent(dict(obs0[0].observation), {"episodeSteps": 720})
        assert isinstance(first_action, dict) and {"farmer", "hands", "market"} <= set(first_action), \
            f"FATAL: invalid first action: {first_action!r}"
        print("  [OK] Bare-exec load + step-0 action valid (no __file__, no exception).")

        # --- Full KE game vs starter (debug=True: any agent exception fails QA) ---
        print(f"  Running full KE game vs starter (seed {QA_SEED}, debug=True)...")
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": QA_SEED}, debug=True)
        t_start = time.time()
        env.run([main_py, "starter"])
        elapsed = time.time() - t_start
        last_step = env.steps[-1]
        p0_reward, p1_reward = last_step[0].reward, last_step[1].reward
        p0_status, p1_status = last_step[0].status, last_step[1].status
        avg_step_ms = elapsed / max(1, len(env.steps)) * 1000.0
        print(f"  Finished in {elapsed:.1f}s: P0={p0_status} ${p0_reward:,.2f} | P1={p1_status} ${p1_reward:,.2f} "
              f"({avg_step_ms:.1f} ms/step)")
        assert p0_status == "DONE" and p1_status == "DONE", "FATAL: game did not complete cleanly!"
        assert p0_reward is not None and p0_reward > MIN_V3_SCALE_REWARD, \
            f"FATAL: P0 reward ${p0_reward} below V3-scale bar ${MIN_V3_SCALE_REWARD} (corpse=$3,000)!"
        assert abs(p0_reward - STARTING_MONEY) > 1e-6, "FATAL: P0 reward equals starting money (dead agent)!"
        assert MIN_AVG_STEP_MS < avg_step_ms < MAX_AVG_STEP_MS, \
            f"FATAL: avg step time {avg_step_ms:.1f} ms outside [{MIN_AVG_STEP_MS}, {MAX_AVG_STEP_MS}]!"
        seq_a = _p0_action_sequence(env)
        assert any("PASS" not in s or '"market": []' not in s for s in seq_a), \
            "FATAL: every P0 action is empty all-PASS!"
        print("  [OK] V3-scale reward, real (non-corpse) behavior, sane step time.")
        results.update({"qa_vs_starter_p0": p0_reward, "qa_vs_starter_p1": p1_reward,
                        "qa_runtime_sec": round(elapsed, 1), "qa_avg_step_ms": round(avg_step_ms, 1)})

        # --- Head-to-head vs V3 reference ---
        print("  Running head-to-head vs V3 reference...")
        v3_dir = os.path.join(test_dir, "_v3ref")
        os.makedirs(v3_dir, exist_ok=True)
        with tarfile.open(extracted_v3, "r:gz") as tar:
            tar.extractall(v3_dir)
        v3_main = os.path.join(v3_dir, "main.py")
        assert os.path.exists(v3_main), "FATAL: V3 reference main.py missing!"
        env_h2h = make("kaggriculture", configuration={"episodeSteps": 720, "seed": QA_SEED}, debug=True)
        env_h2h.run([main_py, v3_main])
        h2h = env_h2h.steps[-1]
        print(f"  H2H finished: AEC=${h2h[0].reward:,.2f} ({h2h[0].status}) | V3=${h2h[1].reward:,.2f} ({h2h[1].status})")
        assert h2h[0].status == "DONE" and h2h[1].status == "DONE", "FATAL: H2H game incomplete!"
        assert h2h[0].reward > MIN_V3_SCALE_REWARD, "FATAL: AEC H2H reward below V3-scale bar!"
        assert h2h[1].reward > MIN_V3_SCALE_REWARD, "FATAL: V3 H2H reward below V3-scale bar (harness suspect)!"
        print("  [OK] Head-to-head vs V3 completes at V3 scale for both seats.")
        results.update({"qa_h2h_aec": h2h[0].reward, "qa_h2h_v3": h2h[1].reward})

        # --- Packaged determinism: rewards + full P0 action sequences ---
        print("  Verifying packaged determinism (rewards + full action sequences)...")
        env2 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": QA_SEED}, debug=True)
        env2.run([main_py, "starter"])
        p0_r2 = env2.steps[-1][0].reward
        seq_b = _p0_action_sequence(env2)
        assert p0_reward == p0_r2, f"FATAL: reward nondeterminism! {p0_reward} != {p0_r2}"
        assert seq_a == seq_b, "FATAL: P0 action-sequence nondeterminism!"
        print(f"  [OK] Bit-identical repeat (${p0_reward:,.2f}, {len(seq_a)} steps).")
        results["packaged_determinism"] = True

        results.update({
            "sha256": sha256_of_file(tar_path),
            "size_bytes": os.path.getsize(tar_path),
            "v3_payload_sha256": extracted_v3_sha,
            "member_count": len(archive_members),
            "portability_clean": True,
        })
        return results


def main():
    tar_sha = build_submission_tarball()
    audit_results = verify_submission_integrity(OUTPUT_TARBALL)
    print("\n" + "=" * 80)
    print("V22R1 SUBMISSION INTEGRITY AUDIT COMPLETE — HARDENED QA PASSED")
    print(f"Tarball: {OUTPUT_TARBALL}")
    print(f"SHA-256: {tar_sha}")
    print("=" * 80)
    with open(os.path.join(REPO_ROOT, "PHASE022R1_QA_RESULTS.json"), "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2)


if __name__ == "__main__":
    main()
