import os
import sys
import importlib.util

project_root = r"c:\Users\Sundareswaran\Kagriculture"
strat_dir = os.path.join(project_root, "scratch", "strategy_candidates")
os.makedirs(strat_dir, exist_ok=True)

# Base template is slot4_control_frozen_v2.py with parameters injected
with open(os.path.join(project_root, "agents", "slot4_control_frozen_v2.py"), "r", encoding="utf-8") as f:
    base_code = f.read()

def generate_candidate_file(filename, cows=8, sheep=4, geese=0, melons=15, secondary="CARROT", secondary_target=8, batch=24, emergency=True):
    # Create customized agent code
    # We replace the class instantiation at the bottom
    custom_inst = f"""
_control_instance = FrozenControlSlot4(
    target_cows={cows},
    target_sheep={sheep},
    target_geese={geese},
    target_melons={melons},
    sell_batch={batch}
)
def agent(obs, configuration=None):
    return _control_instance(obs, configuration)
"""
    # Replace default instantiation
    lines = base_code.splitlines()
    # Find `_control_instance = `
    cut_idx = 0
    for i, l in enumerate(lines):
        if l.startswith("_control_instance ="):
            cut_idx = i
            break
    
    new_code = "\n".join(lines[:cut_idx]) + "\n" + custom_inst
    
    # If emergency is enabled, inject emergency liquidity into market logic
    if emergency:
        # In section 7: Liquidation, add emergency override
        emergency_code = """
            # Emergency Liquidity Injection
            wheat_in_shed = shed.get("WHEAT", 0)
            feed_critical = (wheat_in_shed < total_active_animals * 2) if total_active_animals > 0 else False
            labor_critical = (hour == 0 and money < 20)
            if (feed_critical or labor_critical) and len(orders) < 10:
                for prod in ["MELON", "WOOL", "MILK", "CARROT", "FERTILIZER"]:
                    qty = shed.get(prod, 0)
                    if qty > 0 and len(orders) < 10:
                        orders.append(["SELL", prod, min(qty, 10)])
                        break
"""
        new_code = new_code.replace("# 7. Liquidation Market Execution", emergency_code + "\n            # 7. Liquidation Market Execution")

    fpath = os.path.join(strat_dir, filename)
    with open(fpath, "w", encoding="utf-8") as out_f:
        out_f.write(new_code)
    return fpath

# Generate all 9 strategy families as clean standalone candidate files
candidates = [
    ("s1_control_exact.py", {"cows": 8, "sheep": 4, "geese": 0, "melons": 15, "batch": 14, "emergency": False}),
    ("s2_pure_crop.py", {"cows": 0, "sheep": 0, "geese": 0, "melons": 25, "batch": 14, "emergency": False}),
    ("s3_pure_livestock.py", {"cows": 10, "sheep": 5, "geese": 0, "melons": 0, "batch": 14, "emergency": False}),
    ("s4_cow_heavy.py", {"cows": 10, "sheep": 2, "geese": 0, "melons": 15, "batch": 24, "emergency": True}),
    ("s5_sheep_heavy.py", {"cows": 4, "sheep": 8, "geese": 0, "melons": 15, "batch": 24, "emergency": True}),
    ("s6_synthesis_peak.py", {"cows": 8, "sheep": 4, "geese": 0, "melons": 15, "batch": 24, "emergency": True}),
    ("s7_high_melon.py", {"cows": 8, "sheep": 4, "geese": 0, "melons": 20, "batch": 24, "emergency": True}),
    ("s8_fast_hybrid.py", {"cows": 6, "sheep": 3, "geese": 0, "melons": 10, "batch": 24, "emergency": True}),
    ("s9_batch18_synthesis.py", {"cows": 8, "sheep": 4, "geese": 0, "melons": 15, "batch": 18, "emergency": True}),
]

for fname, kwargs in candidates:
    p = generate_candidate_file(fname, **kwargs)
    print(f"Generated clean candidate: {p}")
