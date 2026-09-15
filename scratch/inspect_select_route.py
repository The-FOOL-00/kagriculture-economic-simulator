import os, sys, importlib.util, inspect
spec = importlib.util.spec_from_file_location('base_check', 'candidates/compiled_v54_plus_residual.py')
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)

print(inspect.getsource(base_mod._select_route))
