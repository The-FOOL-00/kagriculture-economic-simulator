import os, sys, importlib.util
spec = importlib.util.spec_from_file_location('base_check', 'candidates/compiled_v54_plus_residual.py')
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)

backbone = base_mod._V56_BACKBONE_ROUTE
yarn = base_mod._V56_YARN_ROUTE

print("--- BACKBONE BUY ACTIONS ---")
for step, act in enumerate(backbone):
    for m in act.get('market', []):
        if m[0].startswith('BUY'):
            print(f"Step {step} (Day {step//24}, Hour {step%24}): {m}")

print("\n--- YARN BUY ACTIONS ---")
for step, act in enumerate(yarn):
    for m in act.get('market', []):
        if m[0].startswith('BUY'):
            print(f"Step {step} (Day {step//24}, Hour {step%24}): {m}")
