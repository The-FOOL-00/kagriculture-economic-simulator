# SPDX-License-Identifier: MIT
"""
Incumbent Wrapper for A7.
Ensures A7 remains strictly untouched, read-only, and identical outside the terminal window.
"""
import os
import sys

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.v32_common import load_agent

class A7Incumbent:
    def __init__(self):
        self.agent = load_agent("E9_AST")
        
    def act(self, obs, config=None):
        return self.agent.act(obs, config)
