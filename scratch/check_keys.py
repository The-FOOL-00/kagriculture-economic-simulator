import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))

import kagsim

g = kagsim.Game(50018)
o = g.observe(0)
print("farms[0] keys:", o["farms"][0].keys())
print("private keys:", o["private"].keys())
