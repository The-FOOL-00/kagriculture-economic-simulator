import sys
import os
import shutil
import hashlib
import kaggle_environments

def main():
    print("="*80)
    print("PART 16: SUBMISSION ARTIFACT FINAL VALIDATION")
    print("="*80)

    # 1. Create temporary directory and copy compiled file as main.py
    temp_dir = os.path.abspath("temporary")
    os.makedirs(temp_dir, exist_ok=True)
    
    src_file = os.path.abspath("candidates/compiled_research_b_only_v2.py")
    dest_file = os.path.join(temp_dir, "main.py")
    shutil.copyfile(src_file, dest_file)
    print(f"Copied {src_file} -> {dest_file}")

    # 2. Recompute SHA256 of exact temporary/main.py
    with open(dest_file, "rb") as f:
        main_hash = hashlib.sha256(f.read()).hexdigest()
    print(f"temporary/main.py SHA256: {main_hash}")
    expected_hash = "3fe18be5fad8b4c79fe27c8a50d316c857cecb87545d52a94e91b49e153bc2e6"
    assert main_hash == expected_hash, f"Hash mismatch on main.py! Expected {expected_hash}, got {main_hash}"

    # 3. Clean sys.path to ensure Kagriculture repo is NOT imported
    repo_root = os.path.abspath(".")
    sys.path = [p for p in sys.path if os.path.abspath(p) != repo_root and "Kagriculture" not in p or "site-packages" in p]

    # Change working directory to temporary directory
    orig_cwd = os.getcwd()
    os.chdir(temp_dir)

    try:
        cfg = {"episodeSteps": 720, "seed": 865000}
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        print("Running full 720-step competition episode as main.py...")
        steps = env.run(["main.py", "starter"])

        p0 = steps[-1][0]
        status = p0["status"]
        reward = float(p0["reward"])

        print(f"Final Episode Status: {status}")
        print(f"Final Agent Reward: {reward:.2f}")
        print(f"Total Episode Steps: {len(steps)}")

        assert status == "DONE", f"Episode failed with status: {status}"
        assert reward > 3000.0, f"Reward {reward} indicates failure/passive bot"
        assert len(steps) == 720, f"Expected 720 steps, got {len(steps)}"

        # Validate action schema for every single step
        valid_actions = 0
        for s_idx, st in enumerate(steps):
            act = st[0].get("action")
            if s_idx > 0:
                assert act is not None, f"Step {s_idx} action is None!"
                valid_actions += 1

        print(f"Valid Non-Null Actions: {valid_actions} / {len(steps)-1}")
        assert valid_actions == len(steps) - 1, "Some actions were invalid!"

    finally:
        os.chdir(orig_cwd)

    print("\nPART 16 VALIDATION: 100% SUCCESSFUL SUBMISSION-STYLE RUN.")
    print(f"REPORTED HASH: {main_hash}")

if __name__ == "__main__":
    main()
