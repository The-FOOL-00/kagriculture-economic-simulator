# SPDX-License-Identifier: MIT
import os, sys
sys.path.insert(0, os.path.abspath("."))
from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v32_p11_terminal.main import V32P11TerminalAgent

def diagnose():
    p11 = V32P11TerminalAgent()
    dmit = load_agent("E8_DMITRII")
    
    env = make("kaggriculture", configuration={"seed": 249677})
    env.run([lambda o, c=None: p11.act(o, c), lambda o, c=None: dmit.act(o, c)])
    
    # Check telemetry from p11 planner
    summary = p11.planner.telemetry.summary()
    print("Telemetry summary:", summary)
    for evt in p11.planner.telemetry.events:
        print("Event:", evt)
        
    print(f"\nFinal Reward: {env.steps[-1][0]['reward']}")

if __name__ == "__main__":
    diagnose()
