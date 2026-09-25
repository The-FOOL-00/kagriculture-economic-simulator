import os
import sys
sys.path.insert(0, os.path.abspath("."))
import copy
from kaggle_environments import make
from aec.backbone.v27_ablation_adapters import V27AblationAdapter
from aec.backbone.v3_adapter import snapshot_v3_globals, restore_v3_globals

def test_a7_oracle():
    print("=== TESTING A7 ORACLE ON OFF-DISTRIBUTION / PERTURBED STATES ===")
    adapter = V27AblationAdapter("V27-ABL-A7")
    env = make("kaggriculture", configuration={"seed": 249675})
    obs = env.reset()[0].observation
    
    # Step 0
    a0 = adapter.act(obs)
    print("Step 0 action:", a0)
    
    # Take step with a totally different action: PASS everything!
    env.step([{"farmer": ["PASS"], "hands": [], "market": []}, {"farmer": ["PASS"], "hands": [], "market": []}])
    obs1_perturbed = env.state[0].observation
    
    # Now ask A7 for an action on this perturbed step 1 state
    print("\nCalling A7 on perturbed step 1 (where step 0 was PASS instead of WASH)...")
    try:
        a1 = adapter.act(obs1_perturbed)
        print("A7 produced step 1 action successfully:")
        print("Farmer:", a1.get("farmer"))
        print("Market:", a1.get("market"))
    except Exception as e:
        print("A7 crashed on perturbed step 1:", type(e), e)

    # Let's inspect internal state tracking
    snap = adapter.snapshot_state()
    print("\nSnapshot keys:", list(snap.keys()))
    print("Parent keys:", list(snap.get("parent", {}).keys()))

if __name__ == "__main__":
    test_a7_oracle()
