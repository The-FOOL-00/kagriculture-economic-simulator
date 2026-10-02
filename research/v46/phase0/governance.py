# SPDX-License-Identifier: MIT
"""V46 Absolute Governance and Holdout Quarantine Enforcement Module.

Enforces cryptographic hashes of protected baseline artifacts and installs
hard runtime guards against quarantined holdout seed ranges.
"""

from __future__ import annotations
import hashlib
import logging
import os
import sys
from typing import Dict, List, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Cryptographically protected baseline artifacts and their canonical SHA256 hashes
PROTECTED_FILES: Dict[str, str] = {
    "candidates/v35_a7_opening/main.py": "1959021BDB1AEFF720732AEC866F5C9F3C9FA0B259EE0AB25982BDA367593249",
    "candidates/v30_a7_standalone/main.py": "51C1D25245F68DD8DE66B355F2AD6CA1D79DE8AF02EFED521A5A82F7BE69CE3F",
    "candidates/v42_alpha_residual/main.py": "0B90784AFC8CFC66D3A947448E99CE796E5286C3E0D70F4A85B593141B24F296",
    "candidates/v43_compositional_alpha/main.py": "281ACD6961CC4172133483014FC2A47AA51341102B02FFBDCA9598CB44A92D02",
    "candidates/v44_economic_portfolio/main.py": "58FDE86583A64689994AE26CDA8DD050B0A05ACE769C173042FCD76FB9BA34DF",
    "submission_aec_v22r1.tar.gz": "6B879B3E499D2CF43B76884F6EF433479468B5C316F92CF4A8CC5119586FB3F5",
}

# Quarantined holdout seed ranges (permanently forbidden from training/tuning/evaluation/forensics)
FORBIDDEN_HOLDOUT_RANGES: List[Tuple[int, int]] = [
    (214200, 214249),
    (340090, 340199),
    (249695, 249734),
]

logger = logging.getLogger("V46_GOVERNANCE")


class HoldoutQuarantineViolation(Exception):
    """Raised when an execution attempts to access a quarantined holdout seed."""
    pass


class BaselineIntegrityViolation(Exception):
    """Raised when a protected baseline artifact has been modified."""
    pass


def assert_protected_artifacts() -> Dict[str, str]:
    """Asserts that all protected artifacts exist and match their exact SHA256 hashes."""
    current_hashes = {}
    for rel_path, expected_hash in PROTECTED_FILES.items():
        abs_path = os.path.join(REPO_ROOT, rel_path)
        if not os.path.exists(abs_path):
            msg = f"FATAL GOVERNANCE ERROR: Protected artifact missing: {rel_path}"
            logger.critical(msg)
            raise BaselineIntegrityViolation(msg)

        with open(abs_path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest().upper()

        current_hashes[rel_path] = digest
        if digest != expected_hash:
            msg = (
                f"FATAL GOVERNANCE ERROR: Hash mismatch for {rel_path}!\n"
                f"  Expected: {expected_hash}\n"
                f"  Actual:   {digest}"
            )
            logger.critical(msg)
            raise BaselineIntegrityViolation(msg)

    return current_hashes


def assert_seed_safe(seed: int) -> bool:
    """Hard runtime guard against forbidden holdout seed ranges."""
    for low, high in FORBIDDEN_HOLDOUT_RANGES:
        if low <= seed <= high:
            msg = (
                f"FATAL HOLDOUT QUARANTINE VIOLATION: Seed {seed} is inside forbidden range [{low}..{high}]!\n"
                f"Termination enforced immediately."
            )
            logger.critical(msg)
            raise HoldoutQuarantineViolation(msg)
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("Executing V46 Governance Invariant Check...")
    hashes = assert_protected_artifacts()
    print("SUCCESS: All 6 protected baseline artifacts verified bit-for-bit unchanged:")
    for path, h in hashes.items():
        print(f"  {path}: {h}")

    print("\nVerifying holdout quarantine assertion...")
    assert_seed_safe(249685)  # Safe DEV seed
    try:
        assert_seed_safe(214220)  # Forbidden
        print("FAIL: Holdout guard did not fire!")
    except HoldoutQuarantineViolation:
        print("SUCCESS: Holdout quarantine guard properly fired on forbidden seed 214220.")
