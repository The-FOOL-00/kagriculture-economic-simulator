import kagsim
from aec.integration.executor import AECExecutor
from scripts.run_phase017_attribution_audit import build_phase015_treatment_config, build_robust_qualified_config

class LoggingExecutor(AECExecutor):
    def act(self, observation, configuration=None):
        step = int(observation.get("step", 0) or 0)
        if step == 649:
            print(f"=== STEP 649 LOGGING (Config: asset_holding={self.config.enable_asset_holding_trigger}) ===")
        res = super().act(observation, configuration)
        if step == 649:
            t = self._telemetry_history[-1]
            print(f"Decision: {t.decision}")
            print(f"Abstain reason: {t.abstain_reason}")
            print(f"Events: {t.events_detected}")
            print(f"Opportunities detected count: {t.opportunities_count}")
            print(f"Patches generated count: {t.patches_generated_count}")
            print(f"Patches pruned count: {t.patches_pruned_count}")
            print(f"Candidates count: {t.candidates_count}")
            print(f"Simulations run: {t.simulations_run}")
            print(f"Candidates list:")
            for c in t.candidates:
                print(f"  cand: {c.patch_id} ({c.mechanism_family}) sim={c.simulation_run} pruned={c.patch_pruned} safety={c.safety_pass} econ_rej={c.economic_rejection_reason} commit={c.commit_decision}")
        return res

trt_cfg = build_phase015_treatment_config()
ctrl_cfg = build_robust_qualified_config()

game = kagsim.Game(249288)
trt_exec = LoggingExecutor(config=trt_cfg)
ctrl_exec = LoggingExecutor(config=ctrl_cfg)

while game.step_count < 650:
    o0 = game.observe(0)
    o1 = game.observe(1)
    a0 = trt_exec.act(o0)
    a1 = ctrl_exec.act(o1)
    game.step(a0, a1)
