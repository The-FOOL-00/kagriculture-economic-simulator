import os
import json
import glob
import re
import numpy as np

def run_aethel_forensics():
    aethel_dir = r'replays\Aethel_prime_v1'
    replay_files = sorted([f for f in os.listdir(aethel_dir) if f.endswith('.json') and '-' not in f])
    log_files = sorted([f for f in os.listdir(aethel_dir) if f.endswith('.json') and '-' in f])

    print(f"Total Aethel Replay JSONs: {len(replay_files)}")
    print(f"Total Aethel Action Logs: {len(log_files)}")

    # Map logs by episode_id
    log_map = {}
    for lf in log_files:
        # e.g., 104580097-1.json -> ep: 104580097, seat: 1
        m = re.match(r'(\d+)-(\d+)\.json', lf)
        if m:
            ep_id = m.group(1)
            seat = int(m.group(2))
            log_map[ep_id] = {'filename': lf, 'seat': seat}

    reconciled = []
    
    for rf in replay_files:
        ep_id = rf.replace('.json', '')
        rpath = os.path.join(aethel_dir, rf)
        size = os.path.getsize(rpath)
        
        has_log = ep_id in log_map
        log_info = log_map.get(ep_id, None)
        
        # Load replay
        with open(rpath, 'r', encoding='utf-8') as f:
            rep = json.load(f)
            
        info = rep.get('info', {})
        agents = info.get('Agents', [{}, {}])
        team_names = info.get('TeamNames', ['', ''])
        engine_ver = rep.get('version', 'unknown')
        if not engine_ver or engine_ver == 'unknown':
            engine_ver = rep.get('module_version', 'unknown')
            
        # Determine our player seat
        # In Kaggle replays, agents/TeamNames or log seat tells us.
        # If log exists, seat is known. If not, we check team name or agent behavior.
        seat = log_info['seat'] if log_info else None
        
        # Determine submission IDs / agent names
        # Check rewards at last step
        steps = rep.get('steps', [])
        total_steps = len(steps)
        last_step = steps[-1] if steps else []
        
        rewards = [last_step[0].get('reward', 0), last_step[1].get('reward', 0)] if len(last_step) >= 2 else [0, 0]
        
        # Let's verify who is who
        # If seat is None, let's look at log or agents
        # Also check stdout in logs for signature if available
        log_matched = False
        log_records = []
        if has_log:
            lpath = os.path.join(aethel_dir, log_info['filename'])
            log_size = os.path.getsize(lpath)
            try:
                with open(lpath, 'r', encoding='utf-8') as lf:
                    log_records = json.load(lf)
                log_matched = (len(log_records) > 0)
            except Exception as e:
                log_matched = False
                
        # Let's inspect agents / names
        p0_name = agents[0].get('Name', team_names[0] if len(team_names) > 0 else 'Unknown')
        p1_name = agents[1].get('Name', team_names[1] if len(team_names) > 1 else 'Unknown')
        
        # If seat is known
        our_seat = seat if seat is not None else 0 # fallback
        opp_seat = 1 - our_seat
        
        our_name = p0_name if our_seat == 0 else p1_name
        opp_name = p1_name if our_seat == 0 else p0_name
        
        our_score = rewards[our_seat]
        opp_score = rewards[opp_seat]
        margin = our_score - opp_score
        
        outcome = 'WIN' if margin > 0 else ('LOSS' if margin < 0 else 'TIE')
        
        # Trajectory extraction at turns 20, 50, 100, 200, 400, 720 (or end)
        traj_points = [20, 50, 100, 200, 400, 719]
        metrics_by_turn = {}
        
        # Detailed turn-by-turn analysis
        # Track: cash, workers, land, cows, sheep, geese, crops, market trades, farm inventory
        turn_traces = []
        
        first_divergence_turn = None
        divergence_reason = None
        
        for t_idx, step_data in enumerate(steps):
            if len(step_data) < 2:
                continue
            obs0 = step_data[0].get('observation', {})
            obs1 = step_data[1].get('observation', {})
            
            our_obs = obs0 if our_seat == 0 else obs1
            opp_obs = obs1 if our_seat == 0 else obs0
            
            our_farm = our_obs.get('farms', [{}])[our_seat] if 'farms' in our_obs and len(our_obs['farms']) > our_seat else {}
            opp_farm = opp_obs.get('farms', [{}])[opp_seat] if 'farms' in opp_obs and len(opp_obs['farms']) > opp_seat else {}
            
            our_money = our_farm.get('money', 0)
            opp_money = opp_farm.get('money', 0)
            
            our_hands = len(our_farm.get('hands', []))
            opp_hands = len(opp_farm.get('hands', []))
            
            our_quads = len(our_farm.get('unlocked_quadrants', []))
            opp_quads = len(opp_farm.get('unlocked_quadrants', []))
            
            # Count livestock and crops from tiles
            def count_farm_assets(farm_dict):
                tiles = farm_dict.get('tiles', [])
                cows, sheep, geese, crops, plowed = 0, 0, 0, 0, 0
                for r in tiles:
                    for c in r:
                        if isinstance(c, dict):
                            t = c.get('type') or c.get('crop') or ''
                            if 'COW' in str(c): cows += 1
                            elif 'SHEEP' in str(c): sheep += 1
                            elif 'GOOSE' in str(c) or 'GEESE' in str(c): geese += 1
                            elif c.get('crop') is not None or c.get('stage') is not None: crops += 1
                            elif c.get('plowed'): plowed += 1
                return cows, sheep, geese, crops, plowed
            
            our_c, our_s, our_g, our_cr, our_pl = count_farm_assets(our_farm)
            opp_c, opp_s, opp_g, opp_cr, opp_pl = count_farm_assets(opp_farm)
            
            # Record snapshots
            if t_idx in traj_points or t_idx == total_steps - 1:
                metrics_by_turn[str(t_idx)] = {
                    'our_money': our_money,
                    'opp_money': opp_money,
                    'our_workers': our_hands + 1,
                    'opp_workers': opp_hands + 1,
                    'our_land': our_quads,
                    'opp_land': opp_quads,
                    'our_cows': our_c,
                    'opp_cows': opp_c,
                    'our_sheep': our_s,
                    'opp_sheep': opp_s,
                    'our_geese': our_g,
                    'opp_geese': opp_g,
                    'our_crops': our_cr,
                    'opp_crops': opp_cr
                }
            
            # Detect first strategic divergence (where opp builds asset lead or economic divergence occurs)
            if outcome == 'LOSS' and first_divergence_turn is None:
                # E.g. opponent buys cow earlier, or hires worker earlier, or unlocks land earlier, or gets ahead on cash by > 500
                if opp_c > our_c and opp_c >= 2:
                    first_divergence_turn = t_idx
                    divergence_reason = f"Opponent reached {opp_c} cows vs our {our_c} cows"
                elif opp_hands > our_hands and opp_hands >= 2:
                    first_divergence_turn = t_idx
                    divergence_reason = f"Opponent reached {opp_hands+1} workers vs our {our_hands+1} workers"
                elif opp_quads > our_quads:
                    first_divergence_turn = t_idx
                    divergence_reason = f"Opponent unlocked quadrant {opp_quads} earlier"
                elif (opp_money - our_money > 1000) and t_idx > 50:
                    first_divergence_turn = t_idx
                    divergence_reason = f"Opponent accumulated liquidity lead: {opp_money:.0f} vs {our_money:.0f}"

        # If still None for a loss, set default to turn 100 divergence
        if outcome == 'LOSS' and first_divergence_turn is None:
            first_divergence_turn = 100
            divergence_reason = "Gradual macro efficiency / throughput divergence"

        # Log forensics: parse log text (stdout / stderr) to extract planned actions, retries, fallbacks, etc.
        log_forensics = {
            'total_log_steps': len(log_records),
            'exceptions': 0,
            'fallback_count': 0,
            'idle_worker_warnings': 0,
            'pathing_blocks': 0,
            'avg_duration_ms': 0.0
        }
        
        durations = []
        if log_records:
            for rec in log_records:
                # rec is list of agent responses for step
                if isinstance(rec, list) and len(rec) > 0:
                    r0 = rec[0]
                    dur = r0.get('duration', 0)
                    durations.append(dur)
                    stderr = r0.get('stderr', '')
                    stdout = r0.get('stdout', '')
                    if 'Exception' in stderr or 'Traceback' in stderr or 'Error' in stderr:
                        log_forensics['exceptions'] += 1
                    if 'fallback' in stderr.lower() or 'fallback' in stdout.lower():
                        log_forensics['fallback_count'] += 1
                    if 'idle' in stderr.lower() or 'blocked' in stderr.lower():
                        log_forensics['idle_worker_warnings'] += 1
                        
            if durations:
                log_forensics['avg_duration_ms'] = float(np.mean(durations) * 1000)

        entry = {
            'episode_id': ep_id,
            'replay_file': rf,
            'log_file': log_info['filename'] if log_info else None,
            'match_verified': log_matched,
            'file_size_bytes': size,
            'engine_version': engine_ver,
            'our_seat': our_seat,
            'our_name': our_name,
            'opp_name': opp_name,
            'our_score': our_score,
            'opp_score': opp_score,
            'margin': margin,
            'outcome': outcome,
            'total_steps': total_steps,
            'first_divergence_turn': first_divergence_turn,
            'divergence_reason': divergence_reason,
            'metrics_by_turn': metrics_by_turn,
            'log_forensics': log_forensics
        }
        reconciled.append(entry)

    # Save to json
    out_path = r'scratch\aethel_full_forensics_reconciled.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(reconciled, f, indent=2)
    print(f"Saved {len(reconciled)} reconciled records to {out_path}")

    # Summary statistics
    wins = [r for r in reconciled if r['outcome'] == 'WIN']
    losses = [r for r in reconciled if r['outcome'] == 'LOSS']
    ties = [r for r in reconciled if r['outcome'] == 'TIE']
    
    print("\n--- AETHEL-PRIME V1 LIVE SUMMARY ---")
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
    run_aethel_forensics()
