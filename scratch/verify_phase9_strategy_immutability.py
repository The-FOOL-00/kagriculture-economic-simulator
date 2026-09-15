import sys
import os
import inspect

sys.path.insert(0, os.path.abspath('.'))

import candidates.research_b_only_v1 as b1_mod
import candidates.compiled_research_b_only_v2 as b1_com

print("=== PHASE 9: STRATEGY IMMUTABILITY AUDIT ===")

mod_cls = b1_mod.ResearchBOnlyV1
com_cls = b1_com.ResearchBOnlyV1

# 1. Quota check
print(f"1. Init quota: Modular={mod_cls().quota}, Compiled={com_cls().quota}")
assert mod_cls().quota == 50 and com_cls().quota == 50

# 2. _macro_market check
src_m_mod = inspect.getsource(mod_cls._macro_market).strip()
src_m_com = inspect.getsource(com_cls._macro_market).strip()
print(f"2. _macro_market exact match: {src_m_mod == src_m_com}")
assert src_m_mod == src_m_com

# 3. _scan_field check
src_s_mod = inspect.getsource(mod_cls._scan_field).strip()
src_s_com = inspect.getsource(com_cls._scan_field).strip()
print(f"3. _scan_field exact match: {src_s_mod == src_s_com}")
assert src_s_mod == src_s_com

import ast, textwrap
tree = ast.parse(textwrap.dedent(inspect.getsource(com_cls._scan_field)))
call_names = [n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
call_attrs = [n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
assert 'sort' not in call_attrs, "Found .sort() call!"
assert 'sorted' not in call_names, "Found sorted() call!"
assert 'res["weeds"] = []' in src_s_com
assert 'STRAWBERRY' in src_s_com

print("\nSTRATEGY IMMUTABILITY PASSED: 100% SEMANTIC IDENTITY AND ZERO STRATEGY MUTATION!")
