# SPDX-License-Identifier: MIT
"""V37: Security and leakage safety scan of production submission artifacts."""

import json
import os
import re
import sys
import tarfile
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARCHIVE_PATH = os.path.join(REPO_ROOT, "final_submission", "V35_FINAL_SUBMISSION.tar.gz")
STAGED_DIR = os.path.join(REPO_ROOT, "submission_final_v35")

PROTECTED_RANGES = [
    (214200, 214249),
    (340090, 340199),
    (249695, 249734),
]

SUSPICIOUS_PATTERNS = [
    r"(?i)api[_-]?key",
    r"(?i)access[_-]?token",
    r"(?i)secret[_-]?key",
    r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}",
    r"-----BEGIN [A-Z ]+ PRIVATE KEY-----",
    r"-----BEGIN CERTIFICATE-----",
    r"ssh-rsa AAAA",
    r"c:[\\/][Uu]sers[\\/]",
    r"/home/[a-zA-Z0-9_-]+",
]

def scan_text(content: str, filename: str):
    findings = []
    
    # 1. Suspicious credentials / paths
    for pattern in SUSPICIOUS_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            findings.append({"type": "credential_or_path_pattern", "pattern": pattern, "count": len(matches)})

    # 2. Protected holdouts check
    for lo, hi in PROTECTED_RANGES:
        for seed in range(lo, hi + 1):
            if str(seed) in content:
                findings.append({"type": "protected_holdout_seed", "seed": seed, "range": f"{lo}-{hi}"})

    return findings

def main_scan():
    report = {
        "staged_directory": STAGED_DIR,
        "archive_path": ARCHIVE_PATH,
        "findings": {},
        "overall_status": "PASS"
    }

    # Scan staged files
    for root, dirs, files in os.walk(STAGED_DIR):
        for f in files:
            p = os.path.join(root, f)
            with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                text = fp.read()
            f_findings = scan_text(text, f)
            if f_findings:
                report["findings"][f"staged/{f}"] = f_findings

    # Scan archive contents
    with tempfile.TemporaryDirectory() as tmpdir:
        with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
            members = tar.getnames()
            tar.extractall(tmpdir)
        for m in members:
            p = os.path.join(tmpdir, m)
            if os.path.isfile(p):
                with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                    text = fp.read()
                m_findings = scan_text(text, m)
                if m_findings:
                    report["findings"][f"archive/{m}"] = m_findings

    if report["findings"]:
        report["overall_status"] = "FAIL"
        print("SECURITY FINDINGS DETECTED:", json.dumps(report, indent=2))
        sys.exit(1)
    else:
        print("SECURITY SCAN CLEAN: 0 FINDINGS.")
        print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main_scan()
