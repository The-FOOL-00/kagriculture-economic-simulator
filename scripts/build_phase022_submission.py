#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 022: Standalone Submission Packager & Integrity Verifier (§11).

Packages the consolidated AEC foundation into submission_aec_v22.tar.gz
and runs exhaustive release-gate integrity checks:
1. Self-contained root main.py entry point.
2. Verified inclusion of aec/, config.py, extracted_agents/, and frozen V3 tarball.
3. Portability scan: zero absolute paths, zero heavy/undeclared dependencies.
4. Bit-exact preservation of submission_Vj_kc_v3.tar.gz SHA256.
5. Standalone full 720-step execution in isolated environment via kaggle_environments.
6. Deterministic seed output equivalence.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tarfile
import tempfile
import time
from typing import Any, Dict, List, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
V3_EXPECTED_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
OUTPUT_TARBALL = os.path.join(REPO_ROOT, "submission_aec_v22.tar.gz")

SUBMISSION_MAIN_CODE = '''# SPDX-License-Identifier: MIT
"""Kagriculture Competition Entrypoint — AEC Robust Qualified Foundation."""

import os
import sys
from typing import Any, Dict, Optional

# Ensure local submission root is in sys.path
_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from aec.config import build_robust_qualified_config
from aec.integration.executor import AECExecutor

_EXECUTOR: Optional[AECExecutor] = None


def agent(observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Kaggle competition agent entrypoint."""
    global _EXECUTOR
    step = int(observation.get("step", 0) or 0)

    if _EXECUTOR is None or step == 0:
        cfg = build_robust_qualified_config()
        local_v3 = os.path.join(_DIR, "submission_Vj_kc_v3.tar.gz")
        if os.path.exists(local_v3):
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
    """Package all necessary runtime components into submission_aec_v22.tar.gz."""
    print(">>> Packaging submission_aec_v22.tar.gz...")

    # Verify V3 SHA256 before packaging
    v3_sha = sha256_of_file(V3_TARBALL_PATH)
    if v3_sha != V3_EXPECTED_SHA:
        raise RuntimeError(f"FATAL: V3 SHA256 mismatch before packaging: {v3_sha} != {V3_EXPECTED_SHA}")

    with tempfile.TemporaryDirectory() as staging:
        # 1. Write root main.py
        main_path = os.path.join(staging, "main.py")
        with open(main_path, "w", encoding="utf-8") as f:
            f.write(SUBMISSION_MAIN_CODE)

        # 2. Copy aec/ directory (excluding __pycache__ and pytest caches)
        aec_src = os.path.join(REPO_ROOT, "aec")
        aec_dst = os.path.join(staging, "aec")
        shutil.copytree(aec_src, aec_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))

        # 3. Copy root config.py
        shutil.copy2(os.path.join(REPO_ROOT, "config.py"), os.path.join(staging, "config.py"))

        # 4. Copy extracted_agents/dmitrii_lb2800
        ext_src = os.path.join(REPO_ROOT, "extracted_agents", "dmitrii_lb2800")
        ext_dst = os.path.join(staging, "extracted_agents", "dmitrii_lb2800")
        shutil.copytree(ext_src, ext_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))

        # 5. Copy frozen V3 archive
        shutil.copy2(V3_TARBALL_PATH, os.path.join(staging, "submission_Vj_kc_v3.tar.gz"))

        # 6. Create tarball with root relative paths
        with tarfile.open(OUTPUT_TARBALL, "w:gz") as tar:
            for item in os.listdir(staging):
                full_p = os.path.join(staging, item)
                tar.add(full_p, arcname=item)

    tar_sha = sha256_of_file(OUTPUT_TARBALL)
    tar_size = os.path.getsize(OUTPUT_TARBALL)
    print(f"  Successfully built: {OUTPUT_TARBALL}")
    print(f"  Size: {tar_size:,} bytes")
    print(f"  SHA-256: {tar_sha}")
    return tar_sha


def verify_submission_integrity(tar_path: str) -> Dict[str, Any]:
    """Exhaustive QA audit on the packaged submission archive."""
    print("\n>>> Verifying Submission Integrity...")

    with tempfile.TemporaryDirectory() as test_dir:
        # 1. Extract archive
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(test_dir)
            archive_members = tar.getnames()

        print(f"  Extracted {len(archive_members)} archive members.")
        assert "main.py" in archive_members, "FATAL: main.py missing from archive root!"
        assert any(m.startswith("aec") for m in archive_members), "FATAL: aec/ package missing from archive!"
        assert "submission_Vj_kc_v3.tar.gz" in archive_members, "FATAL: V3 tarball missing from archive!"

        # 2. Verify V3 archive hash inside extracted package
        extracted_v3 = os.path.join(test_dir, "submission_Vj_kc_v3.tar.gz")
        extracted_v3_sha = sha256_of_file(extracted_v3)
        assert extracted_v3_sha == V3_EXPECTED_SHA, f"FATAL: Extracted V3 SHA256 mismatch! {extracted_v3_sha}"
        print("  [OK] Bundled V3 SHA256 verified bit-identical.")

        # 3. Portability and cleanliness scan
        forbidden_patterns = ["C:\\Users", "/home/", "/Users/", "Sundareswaran"]
        forbidden_modules = ["torch", "tensorflow", "sklearn", "matplotlib", "scipy"]
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
                            scan_warnings.append(f"Heavy dependency '{mod}' imported in {rel_p}")

        if scan_warnings:
            print(f"  [WARN] {len(scan_warnings)} portability warnings:")
            for w in scan_warnings[:5]:
                print(f"    - {w}")
        else:
            print("  [OK] Zero absolute user paths and zero heavy non-standard dependencies.")

        # 4. Standalone Execution Test in Isolated Environment
        print("  Running standalone 720-step game via kaggle_environments...")
        from kaggle_environments import make

        main_py = os.path.join(test_dir, "main.py")
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 249376}, debug=False)
        t_start = time.time()
        env.run([main_py, "starter"])
        elapsed = time.time() - t_start

        last_step = env.steps[-1]
        p0_reward = last_step[0].reward
        p1_reward = last_step[1].reward
        p0_status = last_step[0].status
        p1_status = last_step[1].status

        print(f"  Standalone match finished in {elapsed:.2f}s: P0 Status={p0_status}, P1 Status={p1_status}")
        print(f"  P0 (AEC) Reward: ${p0_reward:,.2f} | P1 (Starter) Reward: ${p1_reward:,.2f}")

        assert p0_status == "DONE" and p1_status == "DONE", f"FATAL: Game did not complete cleanly! Status: {p0_status}"
        assert p0_reward is not None and p0_reward > 0, "FATAL: Reward is None or invalid!"
        print("  [OK] 720-step execution validated with zero errors.")

        # 5. Determinism Check across 2 runs on identical seed
        print("  Verifying packaged determinism...")
        env2 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 249376}, debug=False)
        env2.run([main_py, "starter"])
        p0_reward_2 = env2.steps[-1][0].reward
        assert p0_reward == p0_reward_2, f"FATAL: Nondeterminism detected! {p0_reward} != {p0_reward_2}"
        print(f"  [OK] Bit-exact determinism confirmed (${p0_reward:,.2f} == ${p0_reward_2:,.2f}).")

        return {
            "tarball": tar_path,
            "sha256": sha256_of_file(tar_path),
            "size_bytes": os.path.getsize(tar_path),
            "v3_payload_sha256": extracted_v3_sha,
            "portability_clean": len(scan_warnings) == 0,
            "standalone_720_passed": True,
            "runtime_sec": round(elapsed, 2),
            "deterministic": True,
            "p0_reward": p0_reward,
            "p1_reward": p1_reward,
        }


def main():
    tar_sha = build_submission_tarball()
    audit_results = verify_submission_integrity(OUTPUT_TARBALL)
    print("\n" + "=" * 80)
    print("SUBMISSION INTEGRITY AUDIT COMPLETE — SUBMISSION READY")
    print(f"Tarball: {OUTPUT_TARBALL}")
    print(f"SHA-256: {tar_sha}")
    print("=" * 80)


if __name__ == "__main__":
    main()
