import inspect
import kaggle_environments.envs.kaggriculture.kaggriculture as engine

lines, _ = inspect.getsourcelines(engine)

def print_range(start, end, title):
    print(f"\n{'='*80}\n{title} (Lines {start}-{end})\n{'='*80}")
    for idx in range(start-1, min(end, len(lines))):
        print(f"{idx+1:4d}: {lines[idx]}", end="")

# CROPS definition
print_range(11, 45, "CROPS CONFIGURATION")

# Planting initialization
print_range(215, 240, "PLANTING INITIALIZATION")

# Crop growth & unwatered decay
print_range(760, 825, "CROP GROWTH, WATERING & WEED TRANSITION")

# Harvest logic
for i, l in enumerate(lines):
    if "def _do_harvest" in l or "def harvest" in l.lower() and "def " in l:
        print_range(i+1, i+65, f"HARVEST FUNCTION ({l.strip()})")
