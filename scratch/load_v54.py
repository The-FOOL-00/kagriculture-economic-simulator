import sys, types, os
sys.stdout.reconfigure(encoding='utf-8')

import importlib.util
spec = importlib.util.spec_from_file_location("v54", "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py")
mod = importlib.util.module_from_spec(spec)
# Let's inspect what symbols get loaded
spec.loader.exec_module(mod)
print('Loaded successfully!')
print('Symbols in mod:', [k for k in dir(mod) if not k.startswith('__')])
if hasattr(mod, '_V51_BASE_SOURCE'):
    src = mod._V51_BASE_SOURCE.decode('utf-8', errors='ignore')
    print('Length of _V51_BASE_SOURCE:', len(src))
    print('Header of _V51_BASE_SOURCE:')
    print(src[:2000])
