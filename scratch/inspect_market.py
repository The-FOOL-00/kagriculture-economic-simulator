import sys, os
sys.path.insert(0, os.path.abspath("."))
import kaggle_environments.envs.kaggriculture.kaggriculture as kg
import inspect

source = inspect.getsource(kg)

lines = source.split("\n")
print("=== MARKET INITIALIZATION ===")
for i, line in enumerate(lines):
    if "market = " in line or '"market"' in line:
        print(f"Line {i+1}: {line}")

print("\n=== TOWN INITIALIZATION ===")
for i, line in enumerate(lines):
    if "town = " in line or '"town"' in line:
        print(f"Line {i+1}: {line}")

print("\n=== FARMS INITIALIZATION ===")
for i, line in enumerate(lines):
    if "farms = " in line or '"farms"' in line:
        print(f"Line {i+1}: {line}")
