import os
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
CPPSIM = os.path.join(REPO_ROOT, "external_repos", "kaggriculture-cppsim")
if CPPSIM not in sys.path:
    sys.path.insert(0, CPPSIM)

import kagsim
from aec.config import build_robust_qualified_config
from aec.integration.executor import AECExecutor
from aec.opportunities.diagnostic_transformations import (
    DiagnosticTransformationGenerator,
    DiagnosticEvaluator,
)

print("Testing single-match diagnostic census speed...")
t0 = time.time()
game = kagsim.Game(249356)
executor = AECExecutor(config=build_robust_qualified_config())
opp_executor = AECExecutor(config=build_robust_qualified_config())

gen = DiagnosticTransformationGenerator()
evaluator = DiagnosticEvaluator()

probed_candidates_count = 0
step_count = 0

while not game.done and step_count < 100:
    o0, o1 = game.observe(0), game.observe(1)
    a0 = executor.act(o0)
    a1 = opp_executor.act(o1)
    
    econ_state = getattr(executor, "_prev_econ_state", None)
    if econ_state is not None:
        # Sample every 5 steps
        if step_count % 5 == 0:
            cands = gen.generate_candidates(econ_state, a0)
            for c in cands:
                evaluator.evaluate_stage1_local(econ_state, c, a0)
                evaluator.evaluate_stage2_long_horizon(
                    econ_state, c, a0,
                    v3_agent_callable=getattr(executor.backbone, "_agent_fn", None)
                )
                probed_candidates_count += 1
    
    game.step(a0, a1)
    step_count += 1

elapsed = time.time() - t0
print(f"Completed {step_count} steps, {probed_candidates_count} candidates probed in {elapsed:.2f}s ({elapsed/step_count*1000:.1f}ms/step)")
