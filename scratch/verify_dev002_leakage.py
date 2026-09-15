import sys
import os

base_dir = os.path.abspath(".")
sys.path.insert(0, os.path.join(base_dir, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(base_dir, "candidates", "closed_loop_architecture"))
sys.path.insert(0, os.path.join(base_dir, "scratch"))

from verify_agent_zero_leakage import (
    ActiveContainmentSandbox,
    LeakageViolationError,
    audit_agent_ast,
    run_runtime_leakage_audit,
)
from dev_002_hedged_portfolio import Dev002HedgedPortfolioAgent
from run_gate_0_3_leakage_verification import run_adversarial_suite

print("=== 1. AUDITING 14 ADVERSARIAL VECTORS ===")
rows = run_adversarial_suite()
all_passed = True
for name, expected, actual, status, err in rows:
    print(f"{name:<35} | {status:<12} | {actual}")
    if "FAIL" in status:
        all_passed = False

print(f"\n14-Vector Suite 100% Interception: {all_passed}")

print("\n=== 2. AUDITING DEV-002 TREATMENT AGENT ===")
ast_violations = audit_agent_ast("candidates/closed_loop_architecture/dev_002_hedged_portfolio.py")
print(f"AST Audit Clean: {len(ast_violations) == 0}, Violations: {ast_violations}")

runtime_result = run_runtime_leakage_audit(Dev002HedgedPortfolioAgent(), seed=50000)
print(f"Runtime Sandbox Audit: Status={runtime_result['status']}, Steps={runtime_result['steps']}, Reward={runtime_result['final_reward']}")

if all_passed and len(ast_violations) == 0 and runtime_result['status'] == 'PASS':
    print("\nOVERALL LEAKAGE VERIFICATION: 100% PASS — ZERO LEAKAGE DETECTED")
else:
    print("\nOVERALL LEAKAGE VERIFICATION: FAILED")
