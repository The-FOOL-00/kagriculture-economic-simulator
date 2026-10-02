import os
import sys
import json
import time
import tempfile
import tarfile
import importlib.util
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def run_four_arm_match(match_spec):
    arm_name = match_spec['arm_name']
    seed = match_spec['seed']
    seat = match_spec['seat']
    v3_tarball = match_spec['v3_tarball']
    v22r1_tarball = match_spec['v22r1_tarball']
    p3_path = match_spec['p3_path']

    # Isolated temp dir
    workdir = tempfile.mkdtemp(prefix=f"arm_{arm_name}_{seed}_{seat}_")
    try:
        # Extract V3
        v3_dir = os.path.join(workdir, "v3")
        os.makedirs(v3_dir, exist_ok=True)
        with tarfile.open(v3_tarball, "r:gz") as tar:
            tar.extractall(v3_dir)
        spec_v3 = importlib.util.spec_from_file_location(f"v3_{seed}_{seat}_{time.time_ns()}", os.path.join(v3_dir, "main.py"))
        mod_v3 = importlib.util.module_from_spec(spec_v3)
        spec_v3.loader.exec_module(mod_v3)
        v3_agent = mod_v3.agent

        # Extract V22R1
        v22_dir = os.path.join(workdir, "v22")
        os.makedirs(v22_dir, exist_ok=True)
        with tarfile.open(v22r1_tarball, "r:gz") as tar:
            tar.extractall(v22_dir)

        # Load P3
        spec_p3 = importlib.util.spec_from_file_location(f"p3_{seed}_{seat}_{time.time_ns()}", p3_path)
        mod_p3 = importlib.util.module_from_spec(spec_p3)
        spec_p3.loader.exec_module(mod_p3)
        p3_agent = mod_p3.agent

        # Build Arm Agent
        if arm_name == "ARM1_V3_STANDALONE":
            arm_agent = v3_agent
        elif arm_name == "ARM2_V3_PLUS_AEC":
            sys.path.insert(0, v22_dir)
            spec_v22 = importlib.util.spec_from_file_location(f"v22_{seed}_{seat}_{time.time_ns()}", os.path.join(v22_dir, "main.py"))
            mod_v22 = importlib.util.module_from_spec(spec_v22)
            spec_v22.loader.exec_module(mod_v22)
            arm_agent = mod_v22.agent
        elif arm_name == "ARM3_V25_P3_STANDALONE":
            arm_agent = p3_agent
        elif arm_name == "ARM4_V25_P3_PLUS_AEC":
            sys.path.insert(0, v22_dir)
            from aec.config import build_robust_qualified_config
            from aec.integration.executor import AECExecutor
            from aec.integration.backbone_adapter import BackboneAdapter

            cfg = build_robust_qualified_config()
            cfg.v3_tarball_path = os.path.join(v22_dir, "submission_Vj_kc_v3.tar.gz")
            adapter = BackboneAdapter(agent_fn=p3_agent, config=cfg)
            executor = AECExecutor(backbone_adapter=adapter, config=cfg)

            def wrapped_p3_aec(obs, conf=None):
                return executor.act(obs, conf)
            arm_agent = wrapped_p3_aec
        else:
            raise ValueError(f"Unknown arm: {arm_name}")

        from kaggle_environments import make
        env = make("kaggriculture", configuration={"seed": seed})

        if seat == 0:
            agents = [arm_agent, v3_agent]
        else:
            agents = [v3_agent, arm_agent]

        t0 = time.time()
        env.run(agents)
        dur = time.time() - t0

        r0 = env.steps[-1][0]['reward']
        r1 = env.steps[-1][1]['reward']
        cand_reward = r0 if seat == 0 else r1
        baseline_reward = r1 if seat == 0 else r0
        delta = cand_reward - baseline_reward

        return {
            "arm": arm_name,
            "seed": seed,
            "seat": seat,
            "candidate_reward": cand_reward,
            "baseline_reward": baseline_reward,
            "single_delta": delta,
            "duration_sec": dur,
            "status": "COMPLETED"
        }
    finally:
        import shutil
        shutil.rmtree(workdir, ignore_errors=True)

def main():
    workdir = os.path.abspath(r"..\Kagriculture-v25")
    results_dir = os.path.join(workdir, "results")
    os.makedirs(results_dir, exist_ok=True)
    checkpoint_file = os.path.join(results_dir, "v25_aec_transfer_matches.jsonl")

    v3_tarball = os.path.abspath("submission_Vj_kc_v3.tar.gz")
    v22r1_tarball = os.path.abspath("submission_aec_v22r1.tar.gz")
    p3_path = os.path.join(workdir, "candidates", "v25_p3_unified.py")

    manifest_path = os.path.join(workdir, "V25_COHORT_MANIFEST.json")
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    # Use first 10 seeds from confirmation cohort (20 matches per arm = 80 matches)
    test_seeds = manifest["v25_confirmation_cohort"]["seeds"][:10]
    arms = [
        "ARM1_V3_STANDALONE",
        "ARM2_V3_PLUS_AEC",
        "ARM3_V25_P3_STANDALONE",
        "ARM4_V25_P3_PLUS_AEC"
    ]

    completed_keys = set()
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        rec = json.loads(line)
                        completed_keys.add((rec['arm'], rec['seed'], rec['seat']))
                    except Exception:
                        pass

    queue = []
    for arm in arms:
        for seed in test_seeds:
            for seat in [0, 1]:
                key = (arm, seed, seat)
                if key not in completed_keys:
                    queue.append({
                        "arm_name": arm,
                        "seed": seed,
                        "seat": seat,
                        "v3_tarball": v3_tarball,
                        "v22r1_tarball": v22r1_tarball,
                        "p3_path": p3_path
                    })

    print(f"Total 4-arm matches to execute: {len(queue)}")
    if not queue:
        print("All matches completed.")
        return

    MAX_WORKERS = 9
    print(f"Executing with MAX_WORKERS = {MAX_WORKERS}...")
    t_start = time.time()
    completed_count = 0

    with open(checkpoint_file, 'a', encoding='utf-8') as f_out:
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_spec = {executor.submit(run_four_arm_match, spec): spec for spec in queue}
            for future in as_completed(future_to_spec):
                spec = future_to_spec[future]
                try:
                    res = future.result()
                    f_out.write(json.dumps(res) + "\n")
                    f_out.flush()
                    completed_count += 1
                    print(f"[{completed_count}/{len(queue)}] {res['arm']} | Seed {res['seed']} | Seat {res['seat']} | Delta: {res['single_delta']:+.0f}")
                except Exception as e:
                    print(f"ERROR in arm match: {e}")

    print(f"4-Arm Tournament completed in {time.time() - t_start:.1f}s.")

if __name__ == '__main__':
    main()
