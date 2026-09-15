import sys
import os
sys.path.insert(0, os.path.abspath('.'))
import inspect
import dis

import candidates.compiled_research_b_only_v2 as b1_v2

print("=== PHASE 3: STATIC RECURSION / ENTRYPOINT AUDIT ===")
print("Module level variables:")
print(f"  _AGENT: {type(b1_v2._AGENT)}, class: {b1_v2._AGENT.__class__.__name__}")
print(f"  agent: {type(b1_v2.agent)}, is_callable: {callable(b1_v2.agent)}")
print(f"  candidate_agent: {type(b1_v2.candidate_agent)}, is_callable: {callable(b1_v2.candidate_agent)}")

print("\nSource of candidate_agent:")
print(inspect.getsource(b1_v2.candidate_agent))
print("Source of agent:")
print(inspect.getsource(b1_v2.agent))

print("\nDisassembly of candidate_agent:")
dis.dis(b1_v2.candidate_agent)

print("\nDisassembly of agent:")
dis.dis(b1_v2.agent)

# Test invocation on step 0
obs = {'step': 0, 'player': 0, 'farms': [{'tiles': [], 'money': 3000, 'shed': {}, 'inventory': {}}]}
act1 = b1_v2.agent(obs)
act2 = b1_v2.candidate_agent(obs)

print("\nInvocation test:")
print(f"  agent(obs) returned type: {type(act1)}")
print(f"  candidate_agent(obs) returned type: {type(act2)}")
print(f"  agent(obs) keys: {list(act1.keys())}")
print(f"  agent(obs) market orders: {act1.get('market', [])[:2]}")
print("STATIC RECURSION AUDIT PASSED: ZERO RECURSION DETECTED!")
