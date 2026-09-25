# SPDX-License-Identifier: MIT
import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v32_p11_terminal.main import V32P11TerminalAgent

class TestP11Terminal(unittest.TestCase):
    def test_purity_steps_0_711(self):
        """Verify actions on steps 0-711 are 100% identical to baseline A7."""
        a7 = load_agent("E9_AST")
        p11 = V32P11TerminalAgent()
        
        env_a7 = make("kaggriculture", configuration={"seed": 249677})
        dmit = load_agent("E8_DMITRII")
        env_a7.run([lambda o, c=None: a7.act(o, c), lambda o, c=None: dmit.act(o, c)])
        
        env_p11 = make("kaggriculture", configuration={"seed": 249677})
        dmit2 = load_agent("E8_DMITRII")
        env_p11.run([lambda o, c=None: p11.act(o, c), lambda o, c=None: dmit2.act(o, c)])
        
        for step in range(712):
            act_a7 = env_a7.steps[step][0]["action"]
            act_p11 = env_p11.steps[step][0]["action"]
            self.assertEqual(act_a7, act_p11, f"Mismatch at step {step}")

    def test_execution_against_dmitrii(self):
        """Run full match on seed 249677 and check reward stability."""
        p11 = V32P11TerminalAgent()
        dmit = load_agent("E8_DMITRII")
        
        env = make("kaggriculture", configuration={"seed": 249677})
        env.run([lambda o, c=None: p11.act(o, c), lambda o, c=None: dmit.act(o, c)])
        
        rew_p11 = env.steps[-1][0]["reward"]
        rew_dmit = env.steps[-1][1]["reward"]
        
        # Baseline A7 reward on seed 249677 is exactly 92,592.0
        self.assertEqual(rew_p11, 92592.0, f"P11 reward mismatch: {rew_p11} != 92592.0")
        self.assertEqual(rew_dmit, 93759.0, f"Dmitrii reward mismatch: {rew_dmit} != 93759.0")
        self.assertEqual(rew_p11 - rew_dmit, -1167.0, f"Gap mismatch: {rew_p11 - rew_dmit} != -1167.0")

if __name__ == "__main__":
    unittest.main()
