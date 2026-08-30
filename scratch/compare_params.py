import os, importlib.util

def get_mod(path):
    spec = importlib.util.spec_from_file_location("kagg_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

p1327 = os.path.join(r"C:\Users\Sundareswaran\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\kaggle_environments\envs\kaggriculture\kaggriculture.py")
p1301 = r"c:\Users\Sundareswaran\Kagriculture\env_backup_1_30_1\kaggriculture.py"

m1327 = get_mod(p1327)
m1301 = get_mod(p1301)

print("=== MARKET_PARAMS COMPARISON ===")
for item in sorted(set(m1327.MARKET_PARAMS.keys()).union(m1301.MARKET_PARAMS.keys())):
    p0 = m1301.MARKET_PARAMS.get(item, {})
    p1 = m1327.MARKET_PARAMS.get(item, {})
    diff = {k: (p0.get(k), p1.get(k)) for k in set(p0).union(p1) if p0.get(k) != p1.get(k)}
    if diff:
        print(f"Item {item:12s} differs: {diff}")
    else:
        print(f"Item {item:12s} identical: base={p1['base']}, below={p1['below_func']}({p1['below_target']}), above={p1['above_func']}({p1['above_target']})")

print("\n=== ANIMALS SPECS COMPARISON ===")
for k in set(m1327.ANIMALS).union(m1301.ANIMALS):
    if m1327.ANIMALS.get(k) != m1301.ANIMALS.get(k):
        print(f"Animal {k} differs: 1.30.1={m1301.ANIMALS.get(k)} vs 1.32.7={m1327.ANIMALS.get(k)}")
    else:
        print(f"Animal {k} identical: {m1327.ANIMALS.get(k)}")

print("\n=== CROPS SPECS COMPARISON ===")
for k in set(m1327.CROPS).union(m1301.CROPS):
    if m1327.CROPS.get(k) != m1301.CROPS.get(k):
        print(f"Crop {k} differs: 1.30.1={m1301.CROPS.get(k)} vs 1.32.7={m1327.CROPS.get(k)}")
    else:
        print(f"Crop {k} identical: {m1327.CROPS.get(k)}")

print("\n=== SHOPS SPECS COMPARISON ===")
for k in set(m1327.SHOPS).union(m1301.SHOPS):
    if m1327.SHOPS.get(k) != m1301.SHOPS.get(k):
        print(f"Shop {k} differs: 1.30.1={m1301.SHOPS.get(k)} vs 1.32.7={m1327.SHOPS.get(k)}")
    else:
        print(f"Shop {k} identical: {m1327.SHOPS.get(k)}")
