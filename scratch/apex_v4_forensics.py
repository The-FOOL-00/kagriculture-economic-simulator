import os
import json
import re
import numpy as np

def run_apex_forensics():
    apex_dir = r'replays\Apex_v4'
    replay_files = sorted([f for f in os.listdir(apex_dir) if f.endswith('.json') and '-' not in f])
    log_files = sorted([f for f in os.listdir(apex_dir) if f.endswith('.json') and '-' in f])

    print(f"Total Apex Replay JSONs: {len(replay_files)}")
    print(f"Total Apex Action Logs: {len(log_files)}")

    log_map = {}
    for lf in log_files:
        m = re.match(r'(\d+)-(\d+)\.json', lf)
        if m:
            ep_id = m.group(1)
            seat = int(m.group(2))
            log_map[ep_id] = {'filename': lf, 'seat': seat}

    reconciled = []
    
    for rf in replay_files:
        ep_id = rf.replace('.json', '')
        rpath = os.path.join(apex_dir, rf)
        size = os.path.getsize(rpath)
        
        has_log = ep_id in log_map
        log_info = log_map.get(ep_id, None)
        
        with open(rpath, 'r', encoding='utf-8') as f:
            rep = json.load(f)
            
        info = rep.get('info', {})
        agents = info.get('Agents', [{}, {}])
        team_names = info.get('TeamNames', ['', ''])
        engine_ver = rep.get('version', 'unknown') or rep.get('module_version', 'unknown')
            
        seat = log_info['seat'] if log_info else 0
        steps = rep.get('steps', [])
        total_steps = len(steps)
        last_step = steps[-1] if steps else []
        
        rewards = [last_step[0].get('reward', 0), last_step[1].get('reward', 0)] if len(last_step) >= 2 else [0, 0]
        
        our_seat = seat
        opp_seat = 1 - our_seat
        
        p0_name = agents[0].get('Name', team_names[0] if len(team_names) > 0 else 'Unknown')
        p1_name = agents[1].get('Name', team_names[1] if len(team_names) > 1 else 'Unknown')
        
        our_name = p0_name if our_seat == 0 else p1_name
        opp_name = p1_name if our_seat == 0 else p0_name
        
        our_score = rewards[our_seat]
        opp_score = rewards[opp_seat]
        margin = our_score - opp_score
        outcome = 'WIN' if margin > 0 else ('LOSS' if margin < 0 else 'TIE')
        
        reconciled.append({
            'episode_id': ep_id,
            'replay_file': rf,
            'log_file': log_info['filename'] if log_info else None,
            'match_verified': has_log,
            'file_size_bytes': size,
            'engine_version': engine_ver,
            'our_seat': our_seat,
            'our_name': our_name,
            'opp_name': opp_name,
            'our_score': our_score,
            'opp_score': opp_score,
            'margin': margin,
            'outcome': outcome,
            'total_steps': total_steps
        })

    out_path = r'scratch\apex_v4_forensics_reconciled.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(reconciled, f, indent=2)
    print(f"Saved {len(reconciled)} reconciled records to {out_path}")

    wins = [r for r in reconciled if r['outcome'] == 'WIN']
    losses = [r for r in reconciled if r['outcome'] == 'LOSS']
    ties = [r for r in reconciled if r['outcome'] == 'TIE']
    
    print("\n--- APEX V4 LIVE SUMMARY ---")
    print(f"Total Replays: {len(reconciled)}")
    print(f"Wins: {len(wins)} ({len(wins)/len(reconciled)*100:.1f}%)")
    print(f"Losses: {len(losses)} ({len(losses)/len(reconciled)*100:.1f}%)")
    print(f"Ties: {len(ties)} ({len(ties)/len(reconciled)*100:.1f}%)")
    print(f"Average Margin: {np.mean([r['margin'] for r in reconciled]):.1f}")
    print(f"Win Margin Mean: {np.mean([r['margin'] for r in wins]) if wins else 0:.1f}")
    print(f"Loss Margin Mean: {np.mean([r['margin'] for r in losses]) if losses else 0:.1f}")
    print(f"Loss Margin Median: {np.median([r['margin'] for r in losses]) if losses else 0:.1f}")
    print(f"Worst Loss: {min([r['margin'] for r in reconciled]):.1f}")

if __name__ == '__main__':
    run_apex_forensics()
