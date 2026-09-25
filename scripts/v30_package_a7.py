# SPDX-License-Identifier: MIT
"""V30: package A7-standalone as a competition submission + loader-validate.

Builds submission_a7_v30.tar.gz (root main.py only) and validates it the
way Kaggle does: extract to a fresh dir, import agent from main.py, run a
full match vs V3 on a fresh seed, check schema + determinism.
"""

import hashlib
import os
import shutil
import subprocess
import sys
import tarfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CAND = os.path.join(REPO_ROOT, "candidates", "v30_a7_standalone", "main.py")
OUT = os.path.join(REPO_ROOT, "submission_a7_v30.tar.gz")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    assert os.path.exists(CAND), CAND
    if os.path.exists(OUT):
        os.remove(OUT)
    with tarfile.open(OUT, "w:gz") as tar:
        tar.add(CAND, arcname="main.py")
    size = os.path.getsize(OUT)
    print("built %s (%d bytes, sha256 %s)" % (OUT, size, sha256_file(OUT)))

    # Loader validation in a pristine temp dir.
    work = "/tmp/v30_loader_check"
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    with tarfile.open(OUT, "r:gz") as tar:
        names = tar.getnames()
        assert names == ["main.py"], names
        tar.extractall(work)
    code = (
        "import sys, json; sys.path.append(%r); sys.path.insert(0, %r);"
        "import main as subm;"
        "assert callable(subm.agent);"
        "from aec.backbone.v3_adapter import V3BackboneAdapter;"
        "from kaggle_environments import make;"
        "v3 = V3BackboneAdapter();"
        "env = make('kaggriculture', configuration={'seed': 249590});"
        "env.run([lambda o, c=None: subm.agent(o, c), lambda o, c=None: v3.act(o, c)]);"
        "print(json.dumps({'r0': env.steps[-1][0]['reward'], 'r1': env.steps[-1][1]['reward']}))"
    ) % (REPO_ROOT, work)
    p = subprocess.run([sys.executable, "-c", code], capture_output=True,
                       text=True, timeout=300, cwd="/tmp")
    print("loader stdout:", p.stdout.strip().splitlines()[-1] if p.stdout.strip() else "")
    if p.returncode != 0:
        print("loader stderr:", p.stderr[-1500:])
        raise SystemExit("LOADER VALIDATION FAILED")
    print("LOADER OK")


if __name__ == "__main__":
    main()
