import os, sys, importlib.util
spec = importlib.util.spec_from_file_location('base_check', 'candidates/compiled_v54_plus_residual.py')
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)

yarn_route = base_mod._V56_YARN_ROUTE
print("Type of yarn_route:", type(yarn_route))
if isinstance(yarn_route, dict):
    print("Keys:", yarn_route.keys())
else:
    print("Dir:", dir(yarn_route))

# Let's inspect differences between backbone route and yarn route
for attr in dir(base_mod):
    if 'ROUTE' in attr:
        print(attr, type(getattr(base_mod, attr)))
