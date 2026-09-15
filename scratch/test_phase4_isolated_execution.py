import sys
import os
import shutil
import tempfile
import kaggle_environments

def main():
    test_seeds = [865000, 865001, 865010, 865050, 865100]
    print("=== PHASE 4: ISOLATED KAGGLE FILE EXECUTION AUDIT ===")
    print(f"Testing seeds: {test_seeds}")

    # 1. Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="kagg_isolated_test_")
    print(f"Created temporary directory: {temp_dir}")
    
    src_file = os.path.abspath("candidates/compiled_research_b_only_v2.py")
    dest_file = os.path.join(temp_dir, "main.py")
    shutil.copyfile(src_file, dest_file)
    print(f"Copied {src_file} -> {dest_file}")

    # 2. Strip Kagriculture repository from sys.path
    repo_root = os.path.abspath(".")
    sys.path = [p for p in sys.path if os.path.abspath(p) != repo_root and "Kagriculture" not in p or "site-packages" in p]
    print(f"Cleaned sys.path (repo removed). Working dir changing to: {temp_dir}")

    orig_cwd = os.getcwd()
    os.chdir(temp_dir)

    all_passed = True
    try:
        for seed in test_seeds:
            print(f"\n--- Running Isolated Execution on Seed {seed} ---")
            cfg = {"episodeSteps": 720, "seed": seed}
            env = kaggle_environments.make("kaggriculture", configuration=cfg)
            steps = env.run(["main.py", "starter"])
            
            p0 = steps[-1][0]
            status = p0["status"]
            rew = float(p0["reward"])
            
            first_step_action = steps[1][0].get("action")
            action_count = sum(1 for st in steps if st[0].get("action") is not None)
            
            print(f"Seed {seed}:")
            print(f"  Final Status: {status}")
            print(f"  Final Reward: {rew}")
            print(f"  Populated First Action: {first_step_action}")
            print(f"  Total Non-Null Action Steps: {action_count} / {len(steps)}")
            
            assert status == "DONE", f"Status failed: {status}"
            assert rew > 3000.0, f"Reward {rew} indicates default passive behavior / failure!"
            assert first_step_action is not None, "First action is None!"
            assert action_count >= 715, f"Too many missing actions: {action_count}"
            
    finally:
        os.chdir(orig_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "="*80)
    print("PHASE 4 ISOLATED KAGGLE FILE EXECUTION: 100% PASS ON ALL 5 SEEDS!")
    print("="*80)

if __name__ == "__main__":
    main()
