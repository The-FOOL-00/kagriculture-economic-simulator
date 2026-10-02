#!/usr/bin/env python3
"""V60 — Fixed replay parser. Extracts all team names from all keep/ files.
The Kaggle replay format uses info.TeamNames and info.Agents.
Also extracts opening actions (first 72 steps) for strategy analysis.
"""
import json
import os
from pathlib import Path

KEEP_DIR = Path("live_data/episodes_v31r2/keep")
OUT_DIR = Path("research/v60/data")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Sep 22 leaderboard top teams (2900+)
TOP_TEAMS = {
    "DSM", "Vadim Vasilenko", "Majkel1337", "Unknown Mother-Goose",
    "THIRD FARM CLUB", "M & M & P & Q", "Kaggledew Valley",
    "Yannik Schiffner", "KawattaTaido", "ymg_aq", "Otter Vibe",
    "mtmr_s1", "QQ", "DECEM", "???????", "THUNDER THUNDER",
    "Azat Akhtyamov", "Sida Zuo", "Planned Economy", "DeeperNet",
    "Orbital Terraformer", "midnq", "SpaTaro", "Ryo Hasegawa",
    "RS Turley", "Densike", "??seek inspiration??", "TheEggman", "kwa"
}

OUR_TEAM = "Eldritch"

replay_index = []
elite_encounters = []
all_team_names = set()
opponent_actions = {}  # opponent_team -> first 72 market actions

files = sorted(KEEP_DIR.glob("*.json"))
print(f"Total keep/ files: {len(files)}")

for i, fpath in enumerate(files):
    if i % 20 == 0:
        print(f"Processing {i+1}/{len(files)}: {fpath.name}")
    
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            replay = json.load(f)
        
        info = replay.get('info', {})
        team_names = info.get('TeamNames', [])
        agents = info.get('Agents', [])
        if not team_names and agents:
            team_names = [a.get('Name', '?') for a in agents]
        
        seed = info.get('seed', None)
        episode_id_num = info.get('EpisodeId', None)
        rewards = replay.get('rewards', [])
        statuses = replay.get('statuses', [])
        module_ver = replay.get('module_version', '?')
        steps = replay.get('steps', [])
        n_steps = len(steps)
        
        # Determine our seat and opponent
        our_seat = None
        for idx, tn in enumerate(team_names):
            if tn == OUR_TEAM:
                our_seat = idx
                break
        
        opp_seat = None
        opp_team = None
        if our_seat is not None:
            opp_seat = 1 - our_seat
            if opp_seat < len(team_names):
                opp_team = team_names[opp_seat]
        
        # Final cash from last step
        final_cash = []
        if steps and len(steps) > 0:
            last_step = steps[-1]
            for agent_obs in last_step:
                if isinstance(agent_obs, dict):
                    obs = agent_obs.get('observation', {})
                    pl = obs.get('player', obs)  # sometimes 'player' is a dict, sometimes obs IS the player
                    cash = pl.get('cash', None) if isinstance(pl, dict) else None
                    if cash is None:
                        # Try direct
                        cash = obs.get('money', obs.get('cash', None))
                    final_cash.append(cash)
        
        # Extract opponent's opening actions (market actions in first 72 steps)
        opp_opening_actions = []
        if opp_seat is not None and n_steps > 0:
            for step_idx in range(min(72, n_steps)):
                step = steps[step_idx]
                if isinstance(step, list) and opp_seat < len(step):
                    agent_data = step[opp_seat]
                    if isinstance(agent_data, dict):
                        action = agent_data.get('action', {})
                        market_actions = action.get('market', [])
                        opp_opening_actions.append({
                            'step': step_idx,
                            'market': market_actions
                        })
        
        prefix = fpath.name.split('-episode-')[0] if '-episode-' in fpath.name else 'unknown'
        
        record = {
            'file': fpath.name,
            'prefix': prefix,
            'ep_id': episode_id_num,
            'seed': seed,
            'team_names': team_names,
            'our_seat': our_seat,
            'opp_seat': opp_seat,
            'opp_team': opp_team,
            'module_version': module_ver,
            'n_steps': n_steps,
            'rewards': rewards,
            'statuses': statuses,
            'final_cash': final_cash,
            'file_size_mb': round(fpath.stat().st_size / 1e6, 1),
        }
        replay_index.append(record)
        
        for tn in team_names:
            if tn:
                all_team_names.add(tn)
        
        # Check for elite encounters
        if opp_team and opp_team in TOP_TEAMS:
            elite_encounters.append({
                'file': fpath.name,
                'prefix': prefix,
                'elite_team': opp_team,
                'all_teams': team_names,
                'ep_id': episode_id_num,
                'seed': seed,
                'our_seat': our_seat,
                'rewards': rewards,
                'final_cash': final_cash,
                'opp_opening_actions': opp_opening_actions[:24],  # first 24 for storage
            })
            
            # Store full opening for this opponent
            if opp_team not in opponent_actions:
                opponent_actions[opp_team] = {
                    'team': opp_team,
                    'episodes': [],
                }
            opponent_actions[opp_team]['episodes'].append({
                'ep_id': episode_id_num,
                'seed': seed,
                'our_seat': our_seat,
                'rewards': rewards,
                'opening_72': opp_opening_actions,
            })
                
    except Exception as e:
        import traceback
        print(f"  ERROR {fpath.name}: {e}")
        replay_index.append({'file': fpath.name, 'error': str(e)})

# Save outputs
with open(OUT_DIR / 'keep_replay_index.json', 'w') as f:
    json.dump(replay_index, f, indent=2)

with open(OUT_DIR / 'elite_encounters.json', 'w') as f:
    json.dump(elite_encounters, f, indent=2)

with open(OUT_DIR / 'opponent_opening_actions.json', 'w') as f:
    json.dump(opponent_actions, f, indent=2)

print(f"\n=== SUMMARY ===")
print(f"Total replays: {len(replay_index)}")
print(f"Errors: {sum(1 for r in replay_index if 'error' in r)}")
print(f"Valid: {sum(1 for r in replay_index if 'error' not in r)}")
print(f"Total unique teams: {len(all_team_names)}")
print(f"Elite encounters: {len(elite_encounters)}")
print(f"\nAll unique team names (non-Eldritch):")
for tn in sorted(all_team_names):
    if tn != OUR_TEAM:
        print(f"  '{tn}'")

print(f"\nElite encounters:")
for enc in elite_encounters:
    our_r = enc['rewards'][enc['our_seat']] if enc['our_seat'] is not None else '?'
    opp_r = enc['rewards'][1-enc['our_seat']] if enc['our_seat'] is not None else '?'
    result = 'W' if our_r > opp_r else ('L' if our_r < opp_r else 'T')
    print(f"  [{result}] {enc['elite_team']} | ep {enc['ep_id']} | {enc['file']}")

print(f"\nPrefix breakdown:")
by_prefix = {}
for r in replay_index:
    if 'error' not in r:
        p = r['prefix']
        by_prefix.setdefault(p, {'count': 0, 'opponents': set()})
        by_prefix[p]['count'] += 1
        if r.get('opp_team'):
            by_prefix[p]['opponents'].add(r['opp_team'])
for prefix, info in sorted(by_prefix.items()):
    print(f"  {prefix}: {info['count']} replays, {len(info['opponents'])} unique opponents")
    for opp in sorted(info['opponents'])[:10]:
        print(f"    - {opp}")
