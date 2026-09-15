import os, sys, importlib.util
spec = importlib.util.spec_from_file_location('base_check', 'candidates/compiled_v54_plus_residual.py')
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)

backbone = base_mod._V56_BACKBONE_ROUTE
yarn = base_mod._V56_YARN_ROUTE

print("Length of backbone:", len(backbone))
print("Length of yarn:", len(yarn))

diffs = []
for i in range(max(len(backbone), len(yarn))):
    b = backbone[i] if i < len(backbone) else None
    y = yarn[i] if i < len(yarn) else None
    if b != y:
        diffs.append((i, b, y))

print(f"Total step diffs: {len(diffs)}")
print("First 10 step diffs:")
for d in diffs[:10]:
    print(f"  Step {d[0]}: backbone={d[1]} | yarn={d[2]}")
