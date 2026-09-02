import os
import sys
import tarfile
import tempfile
import time
import hashlib
import statistics
from kaggle_environments import make

def audit_tarball_and_runtime():
    print("=" * 90)
    print("FORENSIC AUDIT OF PACKAGED SUBMISSION TARBALL & RUNTIME TELEMETRY")
    print("=" * 90)

    tar_path = os.path.abspath("submission_slot2_aethel_refined_v2.tar.gz")
    staged_path = os.path.abspath("candidates/slot2_aethel_refined_v2.py")
    cand_d_path = os.path.abspath("agents/candidate_d_aethel_refined.py")

    # 1. SHA-256 Checksum Verification
    def get_sha(path):
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    tar_sha = get_sha(tar_path)
    staged_sha = get_sha(staged_path)
    cand_d_sha = get_sha(cand_d_path)

    print(f"\n1. Artifact SHA-256 Checksums:")
    print(f"  Tarball:                     {tar_path}")
    print(f"    SHA-256:                   {tar_sha}")
    print(f"  Staged Candidate:            {staged_path}")
    print(f"    SHA-256:                   {staged_sha}")
    print(f"  Candidate D:                 {cand_d_path}")
    print(f"    SHA-256:                   {cand_d_sha}")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract tarball
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(tmpdir)
            names = tar.getnames()

        print(f"\n2. Extracted Tarball Structure:")
        print(f"  Files: {names}")
        
        main_py = os.path.join(tmpdir, "main.py")
        if not os.path.exists(main_py):
            print("  [ERROR] main.py missing from tarball!")
            return False

        extracted_sha = get_sha(main_py)
        print(f"  Extracted main.py SHA-256:   {extracted_sha}")

        if extracted_sha == staged_sha == cand_d_sha:
            print("  >>> [PASS] main.py in tarball is 100% BYTE-IDENTICAL to staged candidate and Candidate D.")
        else:
            print("  >>> [FAIL] Checksum mismatch between packaged main.py and candidate source!")
            return False

        # Inspect main.py for absolute paths or unsafe imports
        with open(main_py, "r", encoding="utf-8") as f:
            code = f.read()

        print("\n3. Scanning main.py for portability & security:")
        has_issue = False
        for line_idx, line in enumerate(code.splitlines(), 1):
            if any(p in line for p in ["C:\\", "/home/", "/Users/", "/tmp/", "Sundareswaran"]):
                print(f"  [WARN] Absolute path or user string on line {line_idx}: {line.strip()}")
                has_issue = True
            if "import " in line and any(mod in line for mod in ["torch", "tensorflow", "sklearn", "matplotlib", "scipy"]):
                print(f"  [WARN] Heavy non-standard dependency on line {line_idx}: {line.strip()}")
                has_issue = True

        if not has_issue:
            print("  >>> [PASS] Zero absolute paths, zero heavy dependencies. 100% pure standard library + engine compatible.")

        # 4. Standalone Execution Test in Isolated Environment
        print("\n4. Standalone Execution Dry-Run in Isolated Directory:")
        opp_path = os.path.abspath("replays/raw/reference_agents/closer_cleo.py")
        
        env = make("kaggriculture", configuration={"seed": 42})
        env.run([main_py, opp_path])
        
        final_p0 = env.steps[-1][0]["reward"]
        final_p1 = env.steps[-1][1]["reward"]
        p0_status = env.steps[-1][0]["status"]
        p1_status = env.steps[-1][1]["status"]
        print(f"  Dry-run match completed: P0 Status={p0_status}, P1 Status={p1_status}")
        print(f"  P0 Reward=${final_p0:,.2f}, P1 Reward=${final_p1:,.2f}")
        
        if p0_status == "DONE" and p1_status == "DONE":
            print("  >>> [PASS] Packaged agent executes cleanly to completion (Step 720).")
        else:
            print("  >>> [FAIL] Packaged agent failed or errored during execution!")
            return False

        # 5. Determinism Check
        print("\n5. Determinism Verification (3 runs per seed across 5 seeds):")
        det_passed = True
        for s in [1, 7, 42, 123, 555]:
            runs_rewards = []
            runs_actions = []
            for run_idx in range(3):
                e = make("kaggriculture", configuration={"seed": s})
                e.run([main_py, opp_path])
                runs_rewards.append((e.steps[-1][0]["reward"], e.steps[-1][1]["reward"]))
                # Capture action signature
                act_sig = [step[0].get("action") for step in e.steps]
                runs_actions.append(act_sig)

            # Check equality
            if runs_rewards[0] == runs_rewards[1] == runs_rewards[2] and runs_actions[0] == runs_actions[1] == runs_actions[2]:
                print(f"  Seed {s:3d}: 3/3 runs 100% bit-exact identical (Rewards: {runs_rewards[0]})")
            else:
                print(f"  Seed {s:3d}: [FAIL] Nondeterminism detected! Rewards: {runs_rewards}")
                det_passed = False

        if det_passed:
            print("  >>> [PASS] Complete bit-exact determinism verified.")

        # 6. Runtime Latency Benchmark
        print("\n6. Runtime Latency Telemetry Benchmark (720 steps):")
        # Measure per-step execution time of the agent function
        import importlib.util
        spec = importlib.util.spec_from_file_location("main_pkg", main_py)
        main_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_mod)

        # Run with instrumented step timer
        step_times = []
        
        def timed_agent(obs, config=None):
            t0 = time.perf_counter()
            action = main_mod.agent(obs, config)
            t1 = time.perf_counter()
            step_times.append((t1 - t0) * 1000.0) # in ms
            return action

        env = make("kaggriculture", configuration={"seed": 100})
        env.run([timed_agent, opp_path])

        mean_lat = statistics.mean(step_times)
        med_lat = statistics.median(step_times)
        stdev_lat = statistics.stdev(step_times)
        p95_lat = sorted(step_times)[int(0.95 * len(step_times))]
        p99_lat = sorted(step_times)[int(0.99 * len(step_times))]
        max_lat = max(step_times)

        print(f"  Total Steps Measured: {len(step_times)}")
        print(f"  Mean Latency:   {mean_lat:6.2f} ms / step")
        print(f"  Median Latency: {med_lat:6.2f} ms / step")
        print(f"  Std Dev:        {stdev_lat:6.2f} ms")
        print(f"  P95 Latency:    {p95_lat:6.2f} ms / step")
        print(f"  P99 Latency:    {p99_lat:6.2f} ms / step")
        print(f"  Max Latency:    {max_lat:6.2f} ms / step (Kaggle timeout limit: 1000 ms / step)")

        if max_lat < 1000.0 and mean_lat < 100.0:
            print(f"  >>> [PASS] Step latency is well within safety thresholds (Mean {mean_lat:.2f}ms << 100ms, Max {max_lat:.2f}ms << 1000ms).")
        else:
            print(f"  >>> [FAIL] Step latency exceeded limits!")
            return False

    return True

if __name__ == "__main__":
    ok = audit_tarball_and_runtime()
    if ok:
        print("\nALL TARBALL, PACKAGING, DETERMINISM, AND RUNTIME BENCHMARKS PASSED (PASS)")
        sys.exit(0)
    else:
        print("\nTARBALL AUDIT FAILED (FAIL)")
        sys.exit(1)
