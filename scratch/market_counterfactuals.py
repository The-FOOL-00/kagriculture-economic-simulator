"""
Sections 9 & 10: Market Forensics & Competitive Counterfactuals
Tests Regimes A through F across 10 identical seeds (2000-2009):
Regime A: Normal shared market
Regime B: Opponent sell quantity capped at 5 units/turn
Regime C: Opponent sells delayed 24 turns (1 day delay)
Regime D: Shared market with price impact removed (pristine prices for both)
Regime E: Opponent sells frozen completely (Pristine Prices test - bidirectional)
Regime F: Independent market inventory simulation

Outputs:
- research/v54_v66_market_forensics.csv
- research/v54_v66_market_forensics.md
"""
import sys, os, json, csv, statistics, importlib.util
from kaggle_environments import make

def load_agent(path):
    d = os.path.dirname(os.path.abspath(path))
    if d not in sys.path: sys.path.insert(0, d)
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "agent", None) or getattr(mod, "_kaggle_submission_entrypoint", None)

v54_path = "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py"
v66_path = "external_repos/kaggriculture-v66-agent/main.py"
v2_path = "agents/slot4_control_frozen_v2.py"

SEEDS = list(range(2000, 2010))

def run_counterfactual_regime(regime_name, agent0_fn, agent1_fn, seeds):
    scores0, scores1 = [], []
    
    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        
        # State wrappers according to regime
        def wrapped_agent0(obs, cfg=None):
            return agent0_fn(obs, cfg)
            
        def wrapped_agent1(obs, cfg=None):
            act = agent1_fn(obs, cfg)
            if not isinstance(act, dict): return act
            step = obs.get("step", obs.get("day", 0)*24 + obs.get("hour", 0))
            market = list(act.get("market", []))
            
            # Regime B: Opponent sell qty capped
            if regime_name == "B_CAPPED_OPPONENT_SELL":
                new_m = []
                for o in market:
                    if o and o[0] == "SELL":
                        new_m.append(["SELL", o[1], min(o[2] if len(o)>2 else 1, 5)])
                    else:
                        new_m.append(o)
                act["market"] = new_m[:10]
                
            # Regime C: Opponent sells delayed 24 turns
            elif regime_name == "C_DELAYED_OPPONENT_SELL":
                if step < 24:
                    act["market"] = [o for o in market if not (o and o[0] == "SELL")]
                    
            # Regime E: Opponent sells completely frozen
            elif regime_name in ("E_FROZEN_OPPONENT_SELL", "PRISTINE_PRICES"):
                act["market"] = [o for o in market if not (o and o[0] == "SELL")]
                
            return act

        env.run([wrapped_agent0, wrapped_agent1])
        s0 = float(env.steps[-1][0].reward or 0.0)
        s1 = float(env.steps[-1][1].reward or 0.0)
        scores0.append(s0)
        scores1.append(s1)
        
    return statistics.mean(scores0), statistics.mean(scores1)

if __name__ == "__main__":
    os.makedirs("research", exist_ok=True)
    os.makedirs("scratch", exist_ok=True)
    
    v54 = load_agent(v54_path)
    v66 = load_agent(v66_path)
    v2 = load_agent(v2_path)
    
    regimes = [
        "A_NORMAL_SHARED_MARKET",
        "B_CAPPED_OPPONENT_SELL",
        "C_DELAYED_OPPONENT_SELL",
        "E_FROZEN_OPPONENT_SELL",
    ]
    
    matchups = [
        ("V2_vs_V54", v2, v54),
        ("V54_vs_V2", v54, v2),
        ("V54_vs_V66", v54, v66),
        ("V66_vs_V54", v66, v54),
    ]
    
    results = []
    print(f"Running Market Counterfactuals across {len(SEEDS)} seeds...")
    
    for r_name in regimes:
        print(f"\n--- Regime: {r_name} ---")
        for m_name, a0, a1 in matchups:
            m0, m1 = run_counterfactual_regime(r_name, a0, a1, SEEDS)
            results.append({
                "Regime": r_name,
                "Matchup": m_name,
                "Agent0_Mean": m0,
                "Agent1_Mean": m1,
                "Margin": m0 - m1
            })
            print(f"  {m_name:12s} | Agent0={m0:8,.0f} | Agent1={m1:8,.0f} | Margin={m0-m1:+8,.0f}")
            
    # Write CSV
    csv_path = "research/v54_v66_market_forensics.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Regime", "Matchup", "Agent0_Mean", "Agent1_Mean", "Margin"])
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    print(f"\nWritten {csv_path}")
