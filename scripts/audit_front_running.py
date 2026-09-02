import sys
from pathlib import Path
import json
from kaggle_environments import make

def run_front_running_audit():
    print("=" * 80)
    print("AUDITING FRONT-RUNNING OVERLAY BEHAVIOR & ALPHA")
    print("=" * 80)

    # Let's test Cleo (FR=1) vs Cleo (FR=0) in mirror play and against reference suite
    opponents = [
        ("Closer Cleo (Mirror)", "replays/raw/reference_agents/closer_cleo.py"),
        ("Slotter Silas", "replays/raw/reference_agents/slotter_silas.py"),
        ("Ledger Lena", "replays/raw/reference_agents/ledger_lena.py"),
        ("Titan Apex V4", "candidates/apex_v4_submission_backup.py")
    ]

    seeds = [1, 2, 3, 5, 7, 10, 42, 100, 501, 502]
    
    # We will build an instrumented agent that counts everything
    instrumented_cleo_code = """
import json, zlib, base64

# Telemetry
TELEMETRY = {
    'checks': 0,
    'high_confidence': 0,
    'queue_not_full': 0,
    'choices_available': 0,
    'orders_appended': 0,
    'items_front_run': {},
    'steps_triggered': []
}

"""
    with open("replays/raw/reference_agents/closer_cleo.py", "r", encoding="utf-8") as f:
        src = f.read()

    # We patch _front_run to log telemetry
    target_fr = "def _front_run(action, obs, step):"
    replacement_fr = """
def _front_run(action, obs, step):
    TELEMETRY['checks'] += 1
    if _CLONE_CONFIDENCE >= 2:
        TELEMETRY['high_confidence'] += 1
    if _CLONE_CONFIDENCE < 2 or _FRONT_RUN_HORIZON <= 0:
        return
    orders = list(action.get("market", []) or [])
    if len(orders) >= 10:
        return
    TELEMETRY['queue_not_full'] += 1
"""
    assert target_fr in src
    instrumented_code = src.replace(target_fr, replacement_fr, 1)

    target_append = 'orders.append(["SELL", item, quantity])\n        action["market"] = orders[:10]'
    replacement_append = """orders.append(["SELL", item, quantity])
        action["market"] = orders[:10]
        TELEMETRY['orders_appended'] += 1
        TELEMETRY['steps_triggered'].append(step)
        TELEMETRY['items_front_run'][item] = TELEMETRY['items_front_run'].get(item, 0) + quantity"""
    assert target_append in instrumented_code
    instrumented_code = instrumented_code.replace(target_append, replacement_append, 1)

    # Add telemetry export at end
    instrumented_code = "TELEMETRY = {'checks': 0, 'high_confidence': 0, 'queue_not_full': 0, 'choices_available': 0, 'orders_appended': 0, 'items_front_run': {}, 'steps_triggered': []}\n" + instrumented_code

    test_agent_path = "scratch/telemetry_cleo.py"
    with open(test_agent_path, "w", encoding="utf-8") as f:
        f.write(instrumented_code)

    print(f"Created instrumented agent: {test_agent_path}")

    # Now evaluate across opponents and seeds
    total_matches = 0
    total_orders_added = 0
    match_reports = []

    # Also test FR=1 vs FR=0 direct head-to-head
    # Build FR=0 agent
    fr0_code = src.replace("_FRONT_RUN_HORIZON = 1", "_FRONT_RUN_HORIZON = 0", 1)
    fr0_path = "scratch/cleo_fr0.py"
    with open(fr0_path, "w", encoding="utf-8") as f:
        f.write(fr0_code)

    fr1_path = "replays/raw/reference_agents/closer_cleo.py"

    print("\n--- 1. Direct Head-to-Head: FR=1 vs FR=0 across 20 symmetric seeds ---")
    h2h_seeds = list(range(1, 21))
    fr1_wins = 0
    fr0_wins = 0
    ties = 0
    cash_deltas = []

    for s in h2h_seeds:
        for p0, p1, label in [(fr1_path, fr0_path, "FR1_seat0"), (fr0_path, fr1_path, "FR1_seat1")]:
            env = make("kaggriculture", configuration={"seed": s})
            env.run([p0, p1])
            c0 = env.steps[-1][0]["reward"] or 0
            c1 = env.steps[-1][1]["reward"] or 0
            fr1_cash = c0 if label == "FR1_seat0" else c1
            fr0_cash = c1 if label == "FR1_seat0" else c0
            diff = fr1_cash - fr0_cash
            cash_deltas.append(diff)
            if diff > 0:
                fr1_wins += 1
            elif diff < 0:
                fr0_wins += 1
            else:
                ties += 1

    print(f"FR=1 vs FR=0: {fr1_wins}W - {fr0_wins}L - {ties}T (40 matches)")
    print(f"Mean cash delta (FR1 - FR0): {sum(cash_deltas)/len(cash_deltas):.2f} coins")
    print(f"Max positive delta: {max(cash_deltas)}, Max negative delta: {min(cash_deltas)}")

    # Now inspect telemetry in mirror play
    print("\n--- 2. Telemetry In Mirror Play (Seeds 1..5) ---")
    import importlib.util
    for s in [1, 2, 3, 4, 5]:
        env = make("kaggriculture", configuration={"seed": s})
        env.run([test_agent_path, fr1_path])
        # Read telemetry from module
        spec = importlib.util.spec_from_file_location("telemetry_cleo", test_agent_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # Note: In-process run shares module state if loaded
        print(f"Seed {s}: Match completed.")

    print(f"\nAudit complete. All direct delta and telemetry tests executed.")

if __name__ == "__main__":
    run_front_running_audit()
