# SPDX-License-Identifier: MIT
"""V37: Build final submission archive V35_FINAL_SUBMISSION.tar.gz."""

import hashlib
import json
import os
import shutil
import tarfile
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STAGING_DIR = os.path.join(REPO_ROOT, "submission_final_v35")
FINAL_DIR = os.path.join(REPO_ROOT, "final_submission")
ARCHIVE_PATH = os.path.join(FINAL_DIR, "V35_FINAL_SUBMISSION.tar.gz")

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def build_archive():
    os.makedirs(FINAL_DIR, exist_ok=True)
    if os.path.exists(ARCHIVE_PATH):
        os.remove(ARCHIVE_PATH)

    staged_main = os.path.join(STAGING_DIR, "main.py")
    assert os.path.exists(staged_main), f"Missing staged file: {staged_main}"
    staged_sha = sha256_file(staged_main)
    staged_size = os.path.getsize(staged_main)

    # 1. Build tar.gz
    with tarfile.open(ARCHIVE_PATH, "w:gz") as tar:
        tar.add(staged_main, arcname="main.py")

    archive_size = os.path.getsize(ARCHIVE_PATH)
    archive_sha = sha256_file(ARCHIVE_PATH)

    # 2. Inspect archive contents
    with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
        members = tar.getnames()
        assert members == ["main.py"], f"Unexpected members: {members}"

    # 3. Test clean extraction
    with tempfile.TemporaryDirectory() as tmpdir:
        with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
            tar.extractall(tmpdir)
        extracted_main = os.path.join(tmpdir, "main.py")
        assert os.path.exists(extracted_main), "Extraction failed to yield main.py"
        extracted_sha = sha256_file(extracted_main)
        assert extracted_sha == staged_sha, f"Extracted hash drift: {extracted_sha} != {staged_sha}"

    res = {
        "archive_filename": "V35_FINAL_SUBMISSION.tar.gz",
        "archive_path": ARCHIVE_PATH,
        "archive_format": "POSIX tar.gz (gzip-compressed)",
        "archive_size_bytes": archive_size,
        "archive_sha256": archive_sha,
        "members": members,
        "staged_sha256": staged_sha,
        "staged_size_bytes": staged_size,
        "extracted_sha256": extracted_sha,
        "roundtrip_exact_match": True,
        "status": "PASS"
    }

    print("ARCHIVE_BUILD_RESULTS:", json.dumps(res, indent=2))

if __name__ == "__main__":
    build_archive()
