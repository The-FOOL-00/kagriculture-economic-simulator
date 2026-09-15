import zlib, base64, re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/unwrap_lineage.py', 'r', encoding='utf-8') as f:
    pass

import importlib.util
spec = importlib.util.spec_from_file_location('v54', 'external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Let's execute v51 to get v50
v51_globals = {}
exec(mod._V51_BASE_SOURCE, v51_globals)
print('v51 executed! keys:', [k for k in v51_globals if not k.startswith('__')])

if '_V50_BASE_SOURCE' in v51_globals:
    v50_src = v51_globals['_V50_BASE_SOURCE']
    print('v50 source length:', len(v50_src))
    print('v50 lines:', len(v50_src.splitlines()))
    v50_globals = {}
    exec(v50_src, v50_globals)
    print('v50 executed! keys:', [k for k in v50_globals if not k.startswith('__')])
    for k in v50_globals:
        if 'BASE_SOURCE' in k:
            print('Found nested source:', k)
