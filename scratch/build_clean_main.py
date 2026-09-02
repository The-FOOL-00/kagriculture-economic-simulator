import os
import ast

with open("replays/raw/reference_agents/closer_cleo.py", "r", encoding="utf-8") as f:
    code = f.read()

# Verify code compiles
ast.parse(code)
print("closer_cleo.py parsed cleanly!")

# Let's inspect what makes closer_cleo.py so strong and ensure our main.py includes both:
# 1. Exact closer_cleo trace and market-controller overlay
# 2. kaggle_agent and agent entrypoints
# 3. Active weed guard
# 4. Engine 1.32.7 calibrated pricing constants

# Let's check how agent entrypoints are exported in closer_cleo.py
with open("main.py", "w", encoding="utf-8") as f:
    f.write(code)
    f.write("\n\ndef kaggle_agent(obs, config=None):\n    return agent(obs, config)\n")

print("main.py written successfully!")
ast.parse(open("main.py", "r", encoding="utf-8").read())
print("main.py syntax verified!")
