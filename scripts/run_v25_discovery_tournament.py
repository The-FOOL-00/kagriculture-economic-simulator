import os
import sys
import json
import time
import hashlib
from concurrent.futures import ProcessPoolExecutor, as_completed

# Set utf-8 encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))
from run_v25_parallel import run_single_match, compute_code_hash

def main():
    workdir = os.path.abspath(r"..\Kagriculture-v25")
    candidates_dir = os.path.join(workdir, "candidates")
    results_dir = os.path.join(workdir, "results")
    os.makedirs(results_dir, exist_ok=True)
    checkpoint_file = os.path.join(results_dir, "v25_backbone_matches.jsonl")

    # Load cohort manifest
    manifest_path = os.path.join(workdir, "V25_COHORT_MANIFEST.json")
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    discovery_seeds = manifest["v25_discovery_cohort"]["seeds"]
    v3_tarball = os.path.abspath("submission_Vj_kc_v3.tar.gz")

    candidates = [
        {"name": "V25_P1_MACRO", "file": "v25_p1_macro.py"},
        {"name": "V25_P2_PRODUCTION", "file": "v25_p2_production.py"},
        {"name": "V25_P3_UNIFIED", "file": "v25_p3_unified.py"}
    ]

    # Load existing checkpoints
    completed_keys = set()
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        rec = json.loads(line)
                        completed_keys.add((rec['candidate'], rec['seed'], rec['seat']))
                    except Exception:
                        pass
    print(f"Loaded {len(completed_keys)} existing completed matches from checkpoint.")

    # Build queue of match specs
    queue = []
    for cand in candidates:
        cand_path = os.path.join(candidates_dir, cand["file"])
        if not os.path.exists(cand_path):
            print(f"WARNING: Candidate file not found: {cand_path}")
            continue
        c_hash = compute_code_hash(cand_path)
        for seed in discovery_seeds:
            for seat in [0, 1]:
                key = (cand["name"], seed, seat)
                if key not in completed_keys:
                    queue.append({
                        "cand_name": cand["name"],
                        "cand_path": cand_path,
                        "v3_tarball": v3_tarball,
                        "seed": seed,
                        "cand_seat": seat,
                        "engine_version": "1.32.7",
                        "code_hash": c_hash
                    })

    print(f"Total matches to execute: {len(queue)}")
    if not queue:
        print("All matches already completed.")
        return

    MAX_WORKERS = 9
    print(f"Launching parallel execution with MAX_WORKERS = {MAX_WORKERS}...")
    t_start = time.time()
    completed_count = 0

    with open(checkpoint_file, 'a', encoding='utf-8') as f_out:
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_spec = {executor.submit(run_single_match, spec): spec for spec in queue}
            for future in as_completed(future_to_spec):
                spec = future_to_spec[future]
                try:
                    res = future.result()
                    f_out.write(json.dumps(res) + "\n")
                    f_out.flush()
                    completed_count += 1
                    print(f"[{completed_count}/{len(queue)}] {res['candidate']} | Seed {res['seed']} | Seat {res['seat']} | Cand: {res['candidate_reward']:.0f} | V3: {res['baseline_reward']:.0f} | Delta: {res['single_delta']:+.0f}")
                except Exception as e:
                    print(f"ERROR executing match {spec['cand_name']} seed={spec['seed']} seat={spec['cand_seat']}: {e}")

    total_dur = time.time() - t_start
    print(f"Tournament completed in {total_dur:.1f}s ({total_dur/max(1, completed_count):.2f}s per match).")

if __name__ == '__main__':
    main()
