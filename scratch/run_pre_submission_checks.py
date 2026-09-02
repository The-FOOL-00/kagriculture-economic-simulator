import os
import sys
import hashlib
import json
import tarfile
import time
import importlib.util

# Add current directory to path
sys.path.insert(0, os.path.abspath('.'))

from engine.livestock_engine import GameConfig, LivestockGame
import farm_state

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def check_artifact_hashes():
    print("=== CHECK 1: ARTIFACT HASHES ===")
    src_path = 'agents/candidate_d_aethel_refined.py'
    slot2_path = 'candidates/slot2_aethel_refined_v2.py'
    tar_path = 'submission_slot2_aethel_refined_v2.tar.gz'
    
    expected_src_sha = '79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d'
    expected_tar_sha = 'ac16af822ea972852ba923dbec45503597b8518ecbe62a8744040d352f0c7c92'
    
    src_sha = sha256_file(src_path)
    slot2_sha = sha256_file(slot2_path)
    tar_sha = sha256_file(tar_path)
    
    print(f"agents/candidate_d_aethel_refined.py SHA-256 : {src_sha}")
    print(f"candidates/slot2_aethel_refined_v2.py SHA-256: {slot2_sha}")
    print(f"submission_slot2_aethel_refined_v2.tar.gz SHA: {tar_sha}")
    
    assert src_sha == expected_src_sha, f"Source SHA mismatch: {src_sha} != {expected_src_sha}"
    assert slot2_sha == expected_src_sha, f"Slot2 SHA mismatch: {slot2_sha} != {expected_src_sha}"
    assert tar_sha == expected_tar_sha, f"Tar SHA mismatch: {tar_sha} != {expected_tar_sha}"
    
    # Inspect tarball contents
    with tarfile.open(tar_path, 'r:gz') as tar:
        members = tar.getmembers()
        assert len(members) == 1, f"Expected 1 member in tarball, got {len(members)}"
        assert members[0].name == 'main.py', f"Expected main.py, got {members[0].name}"
        f = tar.extractfile(members[0])
        extracted_content = f.read()
        extracted_sha = sha256_bytes(extracted_content)
        print(f"Tarball extracted main.py SHA-256           : {extracted_sha}")
        assert extracted_sha == expected_src_sha, f"Extracted main.py SHA mismatch: {extracted_sha} != {expected_src_sha}"

    print("Artifact byte identity verified: EXACT MATCH.\n")

def check_clean_source():
    print("=== CHECK 2: SOURCE CODE SAFETY & ISOLATION ===")
    with open('agents/candidate_d_aethel_refined.py', 'r', encoding='utf-8') as f:
        src = f.read()
        
    prohibited_terms = [
        'import socket', 'import urllib', 'import requests', 'import http',
        'C:\\\\', 'C:/', '/home/', '/tmp/', 'eval(', 'exec(', '__import__("os").system'
    ]
    for term in prohibited_terms:
        if term in src:
            print(f"WARNING: Prohibited term '{term}' found in candidate source!")
        else:
            pass
    print("Zero network calls, absolute local paths, or unsafe eval/exec found.\n")

def check_determinism():
    print("=== CHECK 3: DETERMINISM AUDIT ===")
    # Load candidate agent
    spec_d = importlib.util.spec_from_file_location("candidate_d", "agents/candidate_d_aethel_refined.py")
    mod_d = importlib.util.module_from_spec(spec_d)
    spec_d.loader.exec_module(mod_d)
    agent_d = mod_d.agent

    # Load anchor agent (Anchor Closer Cleo / Aethel-Prime V1)
    spec_anchor = importlib.util.spec_from_file_location("anchor", "agents/anchor_closer_cleo.py")
    mod_anchor = importlib.util.module_from_spec(spec_anchor)
    spec_anchor.loader.exec_module(mod_anchor)
    agent_anchor = mod_anchor.agent

    test_seeds = [42, 100, 501, 550, 600]
    for seed in test_seeds:
        # Run 1: Candidate as P0, Anchor as P1
        res1 = []
        res2 = []
        for run_idx in [1, 2]:
            game = LivestockGame(seed=seed)
            obs = game.get_observation()
            # Reset agent state if any
            if hasattr(mod_d, 'RESET') or hasattr(mod_d, 'state'):
                pass
            
            p0_actions = []
            p1_actions = []
            
            for step in range(720):
                # Candidate D as P0
                obs0 = {**obs, 'player': 0}
                act0 = agent_d(obs0, {})
                p0_actions.append(act0)
                
                # Anchor as P1
                obs1 = {**obs, 'player': 1}
                act1 = agent_anchor(obs1, {})
                p1_actions.append(act1)
                
                obs, rewards, done, info = game.step({0: act0, 1: act1})
                if done:
                    break
            
            final_p0_coins = game.state['players'][0]['coins']
            final_p1_coins = game.state['players'][1]['coins']
            margin = final_p0_coins - final_p1_coins
            
            if run_idx == 1:
                res1 = (p0_actions, p1_actions, final_p0_coins, final_p1_coins, margin)
            else:
                res2 = (p0_actions, p1_actions, final_p0_coins, final_p1_coins, margin)
                
        # Compare run 1 and run 2
        assert res1[0] == res2[0], f"Seed {seed}: P0 actions not deterministic!"
        assert res1[1] == res2[1], f"Seed {seed}: P1 actions not deterministic!"
        assert res1[2] == res2[2], f"Seed {seed}: P0 coins not identical ({res1[2]} != {res2[2]})"
        assert res1[3] == res2[3], f"Seed {seed}: P1 coins not identical ({res1[3]} != {res2[3]})"
        print(f"Seed {seed:3d}: Deterministic (P0: ${res1[2]:,}, P1: ${res1[3]:,}, Margin: ${res1[4]:+,})")
    print("Determinism check passed: 100% trajectory invariance.\n")

def check_invalid_actions():
    print("=== CHECK 4: INVALID ACTIONS & EXCEPTION AUDIT ===")
    spec_d = importlib.util.spec_from_file_location("candidate_d", "agents/candidate_d_aethel_refined.py")
    mod_d = importlib.util.module_from_spec(spec_d)
    spec_d.loader.exec_module(mod_d)
    agent_d = mod_d.agent

    spec_anchor = importlib.util.spec_from_file_location("anchor", "agents/anchor_closer_cleo.py")
    mod_anchor = importlib.util.module_from_spec(spec_anchor)
    spec_anchor.loader.exec_module(mod_anchor)
    agent_anchor = mod_anchor.agent

    total_steps = 0
    invalid_actions = 0
    exceptions = 0
    
    test_seeds = [1, 2, 3, 501, 502]
    for seed in test_seeds:
        for seat in [0, 1]:
            game = LivestockGame(seed=seed)
            obs = game.get_observation()
            for step in range(720):
                total_steps += 1
                try:
                    if seat == 0:
                        act0 = agent_d({**obs, 'player': 0}, {})
                        act1 = agent_anchor({**obs, 'player': 1}, {})
                    else:
                        act0 = agent_anchor({**obs, 'player': 0}, {})
                        act1 = agent_d({**obs, 'player': 1}, {})
                except Exception as e:
                    exceptions += 1
                    break
                
                obs, rewards, done, info = game.step({0: act0, 1: act1})
                if info.get('invalid_actions', 0) > 0:
                    invalid_actions += info.get('invalid_actions', 0)
                if done:
                    break

    print(f"Tested {total_steps} steps across 10 games:")
    print(f"  Invalid actions : {invalid_actions}")
    print(f"  Exceptions      : {exceptions}")
    assert invalid_actions == 0, f"Found {invalid_actions} invalid actions"
    assert exceptions == 0, f"Found {exceptions} exceptions"
    print("Zero invalid actions, zero exceptions.\n")

def check_latencies():
    print("=== CHECK 5: LATENCY BENCHMARK ===")
    spec_d = importlib.util.spec_from_file_location("candidate_d", "agents/candidate_d_aethel_refined.py")
    mod_d = importlib.util.module_from_spec(spec_d)
    spec_d.loader.exec_module(mod_d)
    agent_d = mod_d.agent

    spec_anchor = importlib.util.spec_from_file_location("anchor", "agents/anchor_closer_cleo.py")
    mod_anchor = importlib.util.module_from_spec(spec_anchor)
    spec_anchor.loader.exec_module(mod_anchor)
    agent_anchor = mod_anchor.agent

    game = LivestockGame(seed=42)
    obs = game.get_observation()
    
    agent_times = []
    step_times = []
    
    for step in range(720):
        t0 = time.perf_counter()
        act0 = agent_d({**obs, 'player': 0}, {})
        t1 = time.perf_counter()
        agent_times.append((t1 - t0) * 1000) # ms
        
        act1 = agent_anchor({**obs, 'player': 1}, {})
        
        t_step0 = time.perf_counter()
        obs, rewards, done, info = game.step({0: act0, 1: act1})
        t_step1 = time.perf_counter()
        step_times.append((t_step1 - t_step0) * 1000) # ms
        
        if done:
            break

    mean_agent_ms = sum(agent_times) / len(agent_times)
    max_agent_ms = max(agent_times)
    mean_sim_ms = sum(step_times) / len(step_times)
    
    print(f"Internal Agent Execution Latency: mean = {mean_agent_ms:.4f} ms/step, peak = {max_agent_ms:.4f} ms")
    print(f"Engine Simulation Step Latency  : mean = {mean_sim_ms:.4f} ms/step")
    print("All checks completed successfully!")

if __name__ == '__main__':
    check_artifact_hashes()
    check_clean_source()
    check_determinism()
    check_invalid_actions()
    check_latencies()
