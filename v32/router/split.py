# SPDX-License-Identifier: MIT
"""R1 split registry. Single source of truth; mirrors V32_ROUTER_SPLITS.json."""

import json
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

ROUTER_CLASSES = ["E0_V3", "E2_A7", "E3_V25P3", "E6_W72", "E7_W2015"]
OPP_PANEL = ["E0_V3", "E2_A7", "E3_V25P3", "E6_W72", "E7_W2015", "E8_DMITRII"]
WASH_MICRO = ("E6_W72", "E7_W2015")
SHORT = {"E0_V3": "V3", "E2_A7": "A7", "E3_V25P3": "V25P3",
         "E6_W72": "W72", "E7_W2015": "W2015", "E8_DMITRII": "DMIT"}

_cache = {}


def load_splits():
    if "splits" not in _cache:
        with open(os.path.join(REPO_ROOT, "V32_ROUTER_SPLITS.json")) as f:
            _cache["splits"] = json.load(f)
    return _cache["splits"]


def split_of(seed):
    seed = int(seed)
    sp = load_splits()
    for name in ("train", "val", "test", "locked", "spare"):
        if seed in sp[name]:
            return name
    return None


SPLIT_OF = {s: "train" for s in range(249635, 249644 + 1)}
SPLIT_OF.update({s: "val" for s in range(249645, 249649 + 1)})
SPLIT_OF.update({s: "test" for s in range(249650, 249672 + 1)})
SPLIT_OF.update({s: "test" for s in range(249675, 249683 + 1)})
SPLIT_OF.update({s: "locked" for s in range(249684, 249691 + 1)})
SPLIT_OF.update({s: "spare" for s in range(249692, 249694 + 1)})
# Commissioning 249673-249674 deliberately absent (never in batches).
