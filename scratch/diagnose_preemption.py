import sys
sys.path.insert(0, ".")
import kagsim
from scripts.run_phase012_group2_qualification import build_configs_for_mechanism
from aec.integration.executor import AECExecutor

ctrl_cfg, trt_cfg = build_configs_for_mechanism('OPPONENT_PREEMPT_SELL')
game = kagsim.Game(249171)
trt = AECExecutor(config=trt_cfg)
ctrl = AECExecutor(config=ctrl_cfg)

while not game.done:
    obs0 = game.observe(0)
    obs1 = game.observe(1)
    act0 = trt.act(obs0)
    act1 = ctrl.act(obs1)
    game.step(act0, act1)

print("Game done! Reward:", game.reward(0), "CtrlReward:", game.reward(1), "Delta:", game.reward(0) - game.reward(1))
for t in trt._telemetry_history:
    if t.decision == 'COMMIT' and getattr(t, 'committed_mechanism', '') == 'OPPONENT_PREEMPT_SELL':
        for c in t.candidates:
            if c.patch_id == t.committed_patch_id:
                m_act = c.candidate_action.get('market') if c.candidate_action else None
                print(f"Step {t.step}: patch={c.patch_id} d_margin={c.delta_margin} d_money={c.delta_money} mkt={m_act}")
