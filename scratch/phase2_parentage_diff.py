import ast
import difflib
import inspect
import sys
import os

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import candidates.candidate_cl_fert_gated as m1_module
from scratch.qualification_counterfactual_suite import BaseQ50Agent
import candidates.candidate_cl_labor_minimal_v1 as cand_module

def analyze_parentage():
    print("=== PHASE 2: PARENTAGE & AST AUDIT ===")
    
    # 1. Inspect class hierarchy
    cand_cls = cand_module.ClosedLoopLaborMinimalV1
    m1_cls = m1_module.ClosedLoopEconomicV1
    q50_cls = BaseQ50Agent
    
    print(f"Candidate class: {cand_cls.__name__}")
    print(f"Candidate base classes: {[b.__name__ for b in cand_cls.__bases__]}")
    print(f"Is subclass of M1? {issubclass(cand_cls, m1_cls)}")
    
    # 2. Compare methods defined in candidate vs M1
    cand_methods = {k: v for k, v in cand_cls.__dict__.items() if inspect.isfunction(v)}
    m1_methods = {k: v for k, v in m1_cls.__dict__.items() if inspect.isfunction(v)}
    
    print(f"Methods overridden in Candidate: {list(cand_methods.keys())}")
    
    # Check what each overridden method does
    # Overridden methods: __init__, __call__, _macro_market, _scan_field
    
    # Let's check Q50 methods
    q50_methods = {k: v for k, v in q50_cls.__dict__.items() if inspect.isfunction(v)}
    # And ParameterizedQuotaAgent
    param_cls = q50_cls.__bases__[0]
    param_methods = {k: v for k, v in param_cls.__dict__.items() if inspect.isfunction(v)}
    print(f"Methods in ParameterizedQuotaAgent: {list(param_methods.keys())}")
    
    # Diff against Q50:
    # Q50 implements: __init__, __call__, _macro_market, and clamps res["plant_w"] in _scan_field (or in candidate)
    # Let's inspect source of _macro_market in Candidate vs ParameterizedQuotaAgent
    q50_mm = inspect.getsource(param_cls._macro_market)
    cand_mm = inspect.getsource(cand_cls._macro_market)
    
    mm_diff = "".join(difflib.unified_diff(
        q50_mm.splitlines(keepends=True),
        cand_mm.splitlines(keepends=True),
        fromfile="BaseQ50._macro_market",
        tofile="Candidate._macro_market"
    ))
    print(f"_macro_market diff between Q50 and Candidate:\n{mm_diff if mm_diff else 'IDENTICAL'}")

    q50_call = inspect.getsource(param_cls.__call__)
    cand_call = inspect.getsource(cand_cls.__call__)
    call_diff = "".join(difflib.unified_diff(
        q50_call.splitlines(keepends=True),
        cand_call.splitlines(keepends=True),
        fromfile="BaseQ50.__call__",
        tofile="Candidate.__call__"
    ))
    print(f"__call__ diff between Q50 and Candidate:\n{call_diff if call_diff else 'IDENTICAL'}")

    # Now let's check _scan_field
    q50_sf = inspect.getsource(param_cls._scan_field)
    cand_sf = inspect.getsource(cand_cls._scan_field)
    sf_diff = "".join(difflib.unified_diff(
        q50_sf.splitlines(keepends=True),
        cand_sf.splitlines(keepends=True),
        fromfile="BaseQ50._scan_field",
        tofile="Candidate._scan_field"
    ))
    print(f"_scan_field diff between Q50 and Candidate:\n{sf_diff}")

    # Textual diff between candidate_cl_labor_minimal_v1.py and candidate_cl_fert_gated.py
    # Since candidate_cl_labor_minimal_v1.py is an inheritance-based module importing candidate_cl_fert_gated.py,
    # let's verify what is added or changed in candidate_cl_labor_minimal_v1.py!

if __name__ == "__main__":
    analyze_parentage()
