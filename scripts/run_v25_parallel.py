import os
import sys
import json
import time
import hashlib
import tempfile
import tarfile
import importlib.util
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def compute_code_hash(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def run_single_match(match_spec):
    """Worker function executed in parallel subprocess or serially."""
    cand_path = match_spec['cand_path']
    v3_tarball = match_spec['v3_tarball']
    seed = match_spec['seed']
    cand_seat = match_spec['cand_seat']
    cand_name = match_spec['cand_name']
    engine_ver = match_spec.get('engine_version', '1.32.7')
    code_hash = match_spec.get('code_hash', '')

    # Extract V3 in isolated temp dir
    v3_work = tempfile.mkdtemp(prefix=f"v3_p_{seed}_{cand_seat}_")
    try:
        with tarfile.open(v3_tarball, "r:gz") as tar:
            tar.extractall(v3_work)
        
        # Load V3
        spec_v3 = importlib.util.spec_from_file_location(f"v3_{seed}_{cand_seat}_{time.time_ns()}", os.path.join(v3_work, "main.py"))
        mod_v3 = importlib.util.module_from_spec(spec_v3)
        spec_v3.loader.exec_module(mod_v3)
        v3_agent = mod_v3.agent

        # Load Candidate
        spec_cand = importlib.util.spec_from_file_location(f"cand_{seed}_{cand_seat}_{time.time_ns()}", cand_path)
        mod_cand = importlib.util.module_from_spec(spec_cand)
        spec_cand.loader.exec_module(mod_cand)
        cand_agent = mod_cand.agent

        from kaggle_environments import make
        env = make("kaggriculture", configuration={"seed": seed})

        if cand_seat == 0:
            agents = [cand_agent, v3_agent]
        else:
            agents = [v3_agent, cand_agent]

        t0 = time.time()
        env.run(agents)
        dur = time.time() - t0

        r0 = env.steps[-1][0]['reward']
        r1 = env.steps[-1][1]['reward']

        cand_reward = r0 if cand_seat == 0 else r1
        v3_reward = r1 if cand_seat == 0 else r0
        delta = cand_reward - v3_reward

        # Action digest
        actions = [s[cand_seat].get('action') for s in env.steps]
        action_digest = hashlib.sha256(json.dumps(actions, sort_keys=True).encode('utf-8')).hexdigest()

        # Telemetry / metrics
        early_idle = 0
        early_total = 0
        for s_idx in range(min(100, len(env.steps))):
            a = env.steps[s_idx][cand_seat].get('action') or {}
            f = a.get('farmer') or ['PASS']
            h = a.get('hands') or []
            if f and f[0] == 'PASS': early_idle += 1
            early_idle += sum(1 for x in h if x and x[0] == 'PASS')
            early_total += (1 + len(h))

        return {
            "candidate": cand_name,
            "baseline": "V3_STANDALONE",
            "seed": seed,
            "seat": cand_seat,
            "engine_version": engine_ver,
            "code_hash": code_hash,
            "config_hash": hashlib.sha256(str(seed).encode()).hexdigest(),
            "candidate_reward": cand_reward,
            "baseline_reward": v3_reward,
            "single_delta": delta,
            "action_digest": action_digest,
            "early_idle_rate": early_idle / max(1, early_total),
            "duration_sec": dur,
            "completion_status": "COMPLETED"
        }
    finally:
        import shutil
        shutil.rmtree(v3_work, ignore_errors=True)

if __name__ == '__main__':
    print("V25 Parallel Runner ready.")
