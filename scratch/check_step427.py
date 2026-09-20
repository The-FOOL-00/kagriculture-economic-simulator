import sys
sys.path.insert(0, ".")
import kagsim
from scripts.run_phase012_group2_qualification import build_configs_for_mechanism
from aec.integration.executor import AECExecutor

ctrl_cfg, trt_cfg = build_configs_for_mechanism('TOWN_CYCLE')
game = kagsim.Game(249171)
trt = AECExecutor(config=trt_cfg)
ctrl = AECExecutor(config=ctrl_cfg)

step = 0
while not game.done:
    obs0 = game.observe(0)
    obs1 = game.observe(1)
    act0 = trt.act(obs0)
    act1 = ctrl.act(obs1)
    if step == 427:
        print("Step 427 Trt Act:", act0)
        print("Step 427 Ctrl Act:", act1)
        # Find telemetry
        for c in trt._telemetry_history[-1].candidates:
            if "427" in c.patch_id:
                print("Candidate 427:", c.to_dict())
        break
    game.step(act0, act1)
    step += 1
