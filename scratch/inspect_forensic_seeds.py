import sys, os
sys.path.insert(0, os.path.abspath("."))
import json, tarfile, copy
import kagsim
from aec.integration.executor import AECExecutor
from aec.integration.backbone_adapter import BackboneAdapter
from aec.config import AECConfig
from aec.counterfactual.simulator import CounterfactualSimulator, ShadowRolloutState
from aec.ir.economic_state import EconomicState
from aec.counterfactual.opponent_pressure import OpponentPressureModel
from aec.patches.patch import CoupledPatch
from config import compute_market_price

# Load frozen V3 control callable
with tarfile.open("submission_Vj_kc_v3.tar.gz", "r:gz") as tar:
    code = tar.extractfile("main.py").read().decode("utf-8")

def make_v3():
    ns = {}
    exec(compile(code, "v3_main.py", "exec"), ns)
    return ns["agent"]

def make_aec():
    cfg = AECConfig()
    adapter = BackboneAdapter(config=cfg)
    return AECExecutor(backbone_adapter=adapter, config=cfg)

def inspect_seed(seed):
    print(f"\n=======================================================")
    print(f"FORENSIC RECONSTRUCTION FOR SEED {seed}")
    print(f"=======================================================")
    
    aec_agent = make_aec()
    v3_agent = make_v3()
    
    # We will run Match A: Seat 0 = AEC, Seat 1 = V3
    game = kagsim.Game(seed)
    
    affected_turns = []
    
    while not game.done:
        step = game.step_count
        obs0 = game.observe(0)
        obs1 = game.observe(1)
        
        # Get baseline action that AEC's backbone produced
        # and AEC's final action
        # In AECExecutor: act(obs) calls backbone_adapter, checks opportunities, etc.
        act0 = aec_agent.act(obs0)
        act1 = v3_agent(obs1)
        
        # Check if AEC modified the baseline action
        # In AEC, telemetry records commits
        if aec_agent._telemetry_history:
            last_tel = aec_agent._telemetry_history[-1]
            if last_tel.decision == "COMMIT" and last_tel.step == step and step not in [t["step"] for t in affected_turns]:
                affected_turns.append({
                    "step": step,
                    "obs0_before": copy.deepcopy(obs0),
                    "obs1_before": copy.deepcopy(obs1),
                    "act0_committed": copy.deepcopy(act0),
                    "act1": copy.deepcopy(act1),
                    "commit_info": last_tel.to_dict()
                })
        
        game.step(act0, act1)
        
    print(f"Found {len(affected_turns)} affected turns for seed {seed}:")
    for t in affected_turns:
        step = t["step"]
        cinfo = t["commit_info"]
        obs = t["obs0_before"]
        print(f"\n--- AFFECTED TURN STEP {step} ---")
        comm_cand = next((c for c in cinfo.get("candidates", []) if c.get("commit_decision")), {})
        base_act = comm_cand.get("baseline_action") or {}
        cand_act = comm_cand.get("candidate_action") or {}
        print(f"Mechanism: {comm_cand.get('family')}, Patch ID: {cinfo.get('patch_id')}")
        print(f"CF predicted delta_money: {comm_cand.get('delta_money')}, delta_margin: {comm_cand.get('delta_margin')}")
        print(f"Baseline market orders:  {base_act.get('market')}")
        print(f"Candidate market orders: {cand_act.get('market')}")
        print(f"Opponent market orders:  {t['act1'].get('market')}")
        
        m_inv = obs["market"]["inventory"]
        m_prices = obs["market"]["prices"]
        farm_money = obs["farms"][0]["money"]
        shed = obs["private"]["shed"]
        print(f"Pre-turn Market Inv:   WHEAT={m_inv.get('WHEAT')}, FERT={m_inv.get('FERTILIZER')}")
        print(f"Pre-turn Prices:       WHEAT={m_prices.get('WHEAT')}, FERT={m_prices.get('FERTILIZER')}")
        print(f"Pre-turn Farm Money:   ${farm_money}")
        print(f"Pre-turn Shed:         WHEAT={shed.get('WHEAT', 0)}, FERT={shed.get('FERTILIZER', 0)}")
        
        # Now let's trace EXACT quote/commit under REAL engine for Baseline vs Candidate
        # We can replay this single turn from obs0_before in an isolated game or simulated interpreter
        reconstruct_turn(seed, step, base_act, cand_act, t["act1"])

def reconstruct_turn(seed, step, base_act, cand_act, opp_act):
    # Setup two fresh games advanced to 'step' using the same history
    # One takes base_act, one takes cand_act
    
    # Path A: Baseline up to step
    g_base = kagsim.Game(seed)
    v3_0 = make_v3()
    v3_1 = make_v3()
    while g_base.step_count < step:
        g_base.step(v3_0(g_base.observe(0)), v3_1(g_base.observe(1)))
        
    g_cand = kagsim.Game(seed)
    v3_c0 = make_v3()
    v3_c1 = make_v3()
    while g_cand.step_count < step:
        g_cand.step(v3_c0(g_cand.observe(0)), v3_c1(g_cand.observe(1)))
        
    pre_money_b = g_base.observe(0)["farms"][0]["money"]
    pre_money_c = g_cand.observe(0)["farms"][0]["money"]
    
    g_base.step(base_act, opp_act)
    g_cand.step(cand_act, opp_act)
    
    post_money_b = g_base.observe(0)["farms"][0]["money"]
    post_money_c = g_cand.observe(0)["farms"][0]["money"]
    
    post_shed_b = g_base.observe(0)["private"]["shed"]
    post_shed_c = g_cand.observe(0)["private"]["shed"]
    
    delta_b = post_money_b - pre_money_b
    delta_c = post_money_c - pre_money_c
    realized_diff = post_money_c - post_money_b
    
    print(f"\n[REAL ENGINE REALIZATION]")
    print(f"Baseline Net Cash Delta:  ${delta_b:+.1f} (End Money: ${post_money_b:.1f})")
    print(f"Candidate Net Cash Delta: ${delta_c:+.1f} (End Money: ${post_money_c:.1f})")
    print(f"REALIZED ECONOMIC DIFFERENCE (Cand - Base): ${realized_diff:+.1f}")
    print(f"Baseline Post Shed WHEAT: {post_shed_b.get('WHEAT', 0)}, FERT: {post_shed_b.get('FERTILIZER', 0)}")
    print(f"Candidate Post Shed WHEAT: {post_shed_c.get('WHEAT', 0)}, FERT: {post_shed_c.get('FERTILIZER', 0)}")

if __name__ == "__main__":
    for s in [340214, 340224]:
        inspect_seed(s)
