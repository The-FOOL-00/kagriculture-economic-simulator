import os, sys, importlib.util
spec = importlib.util.spec_from_file_location('base_check', 'candidates/compiled_v54_plus_residual.py')
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)

backbone = base_mod._V56_BACKBONE_ROUTE
yarn = base_mod._V56_YARN_ROUTE

print("--- BACKBONE vs YARN BUY ACTIONS (Steps 72 to 240) ---")
for step in range(72, 240):
    b_buys = [m for m in backbone[step].get('market', []) if m[0].startswith('BUY')]
    y_buys = [m for m in yarn[step].get('market', []) if m[0].startswith('BUY')]
    if b_buys or y_buys:
        print(f"Step {step:3d} (Day {step//24:2d}): Backbone={b_buys} | Yarn={y_buys}")
