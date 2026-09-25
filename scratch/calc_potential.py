# SPDX-License-Identifier: MIT
import os, sys
sys.path.insert(0, os.path.abspath("."))
from kaggle_environments import make
from scripts.v32_common import load_agent

a7 = load_agent("E9_AST")
dmitrii = load_agent("E8_DMITRII")
env = make("kaggriculture", configuration={"seed": 249677})
env.run([lambda o, c=None: a7.act(o, c), lambda o, c=None: dmitrii.act(o, c)])

s712 = env.steps[712][0]["observation"]
farm = s712["farms"][0]
priv = s712["private"]
mkt = s712["market"]
prices = mkt["prices"]

carried_counts = {}
for inv in priv["inventories"]:
    for k, v in inv.items():
        if v > 0:
            carried_counts[k] = carried_counts.get(k, 0) + v
carried_val = sum(carried_counts.get(k, 0) * prices.get(k, 0) for k in carried_counts)

shed_counts = {k: v for k, v in priv["shed"].items() if v > 0}
shed_val = sum(shed_counts.get(k, 0) * prices.get(k, 0) for k in shed_counts)

ripe_counts = {}
for r in farm["tiles"]:
    for t in r:
        if isinstance(t, dict):
            yu = t.get("yield_units", 0)
            kind = t.get("kind")
            c = t.get("crop")
            a = t.get("animal")
            f = t.get("fertilizer_available")
            if yu > 0:
                item = c if kind == "PLANT" else ("MILK" if a == "COW" else ("WOOL" if a == "SHEEP" else ("EGG" if a == "GOOSE" else None)))
                if item:
                    ripe_counts[item] = ripe_counts.get(item, 0) + yu
            if f:
                ripe_counts["FERTILIZER"] = ripe_counts.get("FERTILIZER", 0) + 1
ripe_val = sum(ripe_counts.get(k, 0) * prices.get(k, 0) for k in ripe_counts)

total_potential = carried_val + shed_val + ripe_val
actual_cash_gained = env.steps[-1][0]["observation"]["farms"][0]["money"] - farm["money"]

print(f"Carried at 712: {carried_counts} -> ${carried_val}")
print(f"Shed at 712: {shed_counts} -> ${shed_val}")
print(f"Field ripe at 712: {ripe_counts} -> ${ripe_val}")
print(f"Total potential inventory value at 712: ${total_potential}")
print(f"Actual cash gained by A7 712-719: ${actual_cash_gained}")
print(f"Difference (Unrealized theoretical value): ${total_potential - actual_cash_gained}")
