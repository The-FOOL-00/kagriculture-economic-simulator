"""
scratch/audit_fertilizer_autarky.py
Inspect how much Fertilizer is produced internally via manure collection vs bought from the market.
"""
import json
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DMITRII_DIR = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800")

with open(os.path.join(DMITRII_DIR, "actions.json"), "r", encoding="utf-8") as f:
    tapes = json.load(f)

print("=" * 80)
print("FERTILIZER SOURCES IN DMITRII LB2800 TAPES")
print("=" * 80)
for t_idx, tape in enumerate(tapes):
    fert_actions = 0
    fert_collected = 0
    fert_bought = 0
    fert_sold = 0
    for act in tape:
        for w in ([act.get("farmer")] + act.get("hands", [])):
            if not w: continue
            if w[0] == "FERTILIZE": fert_actions += 1
            elif w[0] == "COLLECT_FERTILIZER": fert_collected += 1
        for o in act.get("market", []):
            if not o: continue
            if o[0] == "BUY_PRODUCT" and len(o) > 1 and o[1] == "FERTILIZER":
                fert_bought += o[2] if len(o) > 2 else 1
            elif o[0] == "SELL" and len(o) > 1 and o[1] == "FERTILIZER":
                fert_sold += o[2] if len(o) > 2 else 1
    print(f"Tape {t_idx:2d} | FERTILIZE Actions: {fert_actions:2d} | COLLECT_FERTILIZER: {fert_collected:3d} | Bought: {fert_bought:2d} | Sold: {fert_sold:3d}")
print("=" * 80)
