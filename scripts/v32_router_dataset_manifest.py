# SPDX-License-Identifier: MIT
"""V32 R1 dataset manifest: per-file counts/hashes + split coverage.

Pure analysis (reads label files only). Writes results/v32_router_manifest.json
and prints the table for V32_ROUTER_DATASET.md.
"""

import hashlib
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from v32.router.dataset import load_rows  # noqa: E402

FILES = ["v32_router_full_a.jsonl", "v32_router_full_b.jsonl",
         "v32_router_full_c.jsonl", "v32_router_cont_a.jsonl",
         "v32_router_cont_b.jsonl", "v32_router_cont_c.jsonl",
         "v32_router_full_locked.jsonl", "v32_router_cont_locked.jsonl"]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--locked", action="store_true")
    args = ap.parse_args()
    res = os.path.join(REPO_ROOT, "results")
    files = {}
    for fn in FILES:
        p = os.path.join(res, fn)
        if not os.path.exists(p):
            continue
        n = sum(1 for _ in open(p))
        files[fn] = {"legs": n, "sha256": sha(p)}
        print("%-32s legs=%5d sha=%s" % (fn, n, files[fn]["sha256"][:16]))
    rf, rc = load_rows(include_locked=args.locked)
    cov = {}
    for mode, rows in (("b1", rf), ("b2", rc)):
        by_split = {}
        for r in rows:
            by_split.setdefault(r["split"], set()).add(r["seed"])
        cov[mode] = {"rows": len(rows),
                     "seeds": {k: sorted(v) for k, v in by_split.items()}}
        print("%s: rows=%d %s" % (mode, len(rows),
                                  {k: len(v) for k, v in by_split.items()}))
    man = {"files": files, "coverage": cov}
    man["dataset_hash"] = hashlib.sha256(
        json.dumps(files, sort_keys=True).encode()).hexdigest()
    with open(os.path.join(res, "v32_router_manifest.json"), "w") as f:
        json.dump(man, f, indent=1, sort_keys=True)
    print("dataset_hash=%s" % man["dataset_hash"])


if __name__ == "__main__":
    main()
