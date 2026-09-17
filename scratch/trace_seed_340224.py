import sys, os
sys.path.insert(0, os.path.abspath("."))
import copy, tarfile
import kagsim
from aec.integration.executor import AECExecutor
from aec.integration.backbone_adapter import BackboneAdapter
from aec.config import AECConfig

seed = 340224

# Setup AEC vs V3
cfg = AECConfig()
adapter = BackboneAdapter(config=cfg)
aec = AECExecutor(backbone_adapter=adapter, config=cfg)

# Setup V3
with tarfile.open("submission_Vj_kc_v3.tar.gz", "r:gz") as tar:
    code = tar.extractfile("main.py").read().decode("utf-8")
ns = {}
exec(compile(code, "v3_main.py", "exec"), ns)
v3_ctrl = ns["agent"]

game = kagsim.Game(seed)

diff_steps = []
while not game.done:
    s = game.step_count
    obs0 = game.observe(0)
    obs1 = game.observe(1)
    
    act0 = aec.act(obs0)
    act1 = v3_ctrl(obs1)
    
    if act0 != act1:
        diff_steps.append((s, copy.deepcopy(act0), copy.deepcopy(act1)))
        
    game.step(act0, act1)
    
    # Check money
    r0 = game.reward(0)
    r1 = game.reward(1)
    if s in (574, 575, 576, 646, 647, 648, 715, 716, 717, 718):
        print(f"Step {s}: Reward0 (AEC)={r0}, Reward1 (V3)={r1}, Diff={r0 - r1}")

print(f"\nTotal steps with action difference: {len(diff_steps)}")
for s, a0, a1 in diff_steps:
    print(f"Diff Step {s}:")
    print(f"  AEC market: {a0.get('market')}")
    print(f"  V3  market: {a1.get('market')}")
