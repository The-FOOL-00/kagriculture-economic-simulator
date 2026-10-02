#!/usr/bin/env python3
"""V60 — Discover September submission IDs through episode opponent graph expansion.

Strategy:
1. Start from our most recent V22R1 episodes (Sep 22 date)
2. Find opponent submission IDs in those episodes via ListEpisodes 
3. For each opponent, look up their episode history to find Sep dates
4. Identify which teams are the Sep 22 3000+ players
5. Download their Sep replays from kaggleusercontent CDN

Our Sep 22 episodes are from live_data/episodes_v31r2/v22r1_episodes.json (238 episodes).
We also have a7_episodes.json (83 episodes).
These are our own episodes from Sep 22, so opponents in them ARE active Sep 22 players.
"""
import csv, gzip, json, sys, time, requests
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

GEORGYMAMARIN = Path("replays/raw/georgymamarin")
OUT_DIR = Path("research/v60/data")
REPLAY_OUT = OUT_DIR / "sep_replays"
REPLAY_OUT.mkdir(parents=True, exist_ok=True)

LIST_URL = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{id}.json"

# Sep 22 top teams
TARGET_TEAMS_BY_NAME = {
    "DSM", "Vadim Vasilenko", "Majkel1337", "Unknown Mother-Goose",
    "THIRD FARM CLUB", "M & M & P & Q", "Kaggledew Valley",
    "Yannik Schiffner", "KawattaTaido", "ymg_aq", "Otter Vibe",
    "mtmr_s1", "QQ", "DECEM", "THUNDER THUNDER",
    "Azat Akhtyamov", "Sida Zuo", "Planned Economy", "DeeperNet",
    "Orbital Terraformer", "midnq", "SpaTaro", "Ryo Hasegawa",
    "RS Turley", "Densike", "TheEggman", "kwa"
}

session = requests.Session()
session.headers["User-Agent"] = "kaggriculture-v60-research"

# ===== STEP 1: Load our Sep 22 episode manifests to get opponent sub IDs =====
print("=== STEP 1: Get opponent submission IDs from Sep 22 episodes ===")
our_sep_eps = []
for fname in ["live_data/episodes_v31r2/v22r1_episodes.json", 
              "live_data/episodes_v31r2/a7_episodes.json"]:
    if Path(fname).exists():
        with open(fname) as f:
            eps = json.load(f)
        our_sep_eps.extend(eps)
        print(f"  Loaded {len(eps)} from {fname}")

print(f"Total our Sep 22 episodes: {len(our_sep_eps)}")

# Get all ep IDs from our Sep 22 episodes
our_ep_ids = [ep['id'] for ep in our_sep_eps]
print(f"  Date range: {min(ep.get('createTime','')[:10] for ep in our_sep_eps)} - {max(ep.get('createTime','')[:10] for ep in our_sep_eps)}")

# ===== STEP 2: For each Sep 22 episode, get the full replay to find opponent sub IDs =====
# Actually we need to use ListEpisodes. But our sub IDs already return these episodes.
# We need the OPPONENT's submission ID.
# The v22r1_episodes.json contains episode metadata including agents.
print("\n=== STEP 2: Extract opponent sub IDs from episode metadata ===")
opp_sub_ids = set()
our_sub_id = None

for ep in our_sep_eps:
    agents = ep.get('agents', [])
    for a in agents:
        sub_id = a.get('submissionId')
        if sub_id:
            # We need to figure out which is ours and which is opp
            # One way: check teamId from teams.csv
            opp_sub_ids.add(sub_id)

print(f"Sub IDs from Sep 22 episode metadata: {len(opp_sub_ids)}")

# Also: query ListEpisodes for our most recent known sub IDs to get NEW Sep episodes
# From a7_episodes.json + v22r1_episodes.json, what sub IDs are involved?
# Load the state.json submissions list
with open(GEORGYMAMARIN / "state.json") as f:
    state = json.load(f)
our_latest_subs = state['submissions'][-50:]  # Last 50 from August crawl

# For the actual SEP22 submissions, we need to look at what the dl_replays script fetched.
# The a7 episodes are from submission "a7" and v22r1 from "v22r1".
# But we need the actual Kaggle submission IDs, not labels.

# ===== STEP 3: Use all opponent sub IDs from Sep 22 to crawl episodes =====
print("\n=== STEP 3: Query ListEpisodes for Sep 22 opponent submissions ===")

# Combine: our Aug subs + opponents from Sep 22 episodes
all_sub_ids_to_try = set()
for ep in our_sep_eps:
    agents = ep.get('agents', [])
    for a in agents:
        sub_id = a.get('submissionId')
        if sub_id:
            all_sub_ids_to_try.add(sub_id)

# Also try our own Sep 22 sub IDs by checking recently modified local state
print(f"Unique sub IDs from Sep 22 episodes: {len(all_sub_ids_to_try)}")
print(f"Sample: {sorted(all_sub_ids_to_try)[-10:]}")

# These subs are from Sep 22 episodes - query them for Sep episodes
sep_episodes_found = {}
all_new_sub_ids = set(all_sub_ids_to_try)
team_to_sub = {}  # sub_id -> list of episode data

for sub_id in sorted(all_sub_ids_to_try, reverse=True)[:100]:
    try:
        r = session.post(LIST_URL, json={"submissionId": int(sub_id)}, timeout=30)
        if r.status_code == 200:
            eps = r.json().get("episodes", [])
            # Check if any are in September
            sep_eps = [e for e in eps if (e.get('endTime') or '') >= '2026-09-01']
            if sep_eps:
                print(f"  Sub {sub_id}: {len(eps)} total, {len(sep_eps)} Sep episodes!")
                for e in sep_eps:
                    eid = str(e.get('id', ''))
                    sep_episodes_found[eid] = e
                    # Get opponent sub IDs
                    for a in e.get('agents', []):
                        new_sid = a.get('submissionId')
                        if new_sid and new_sid not in all_new_sub_ids:
                            all_new_sub_ids.add(new_sid)
            else:
                last_date = max((e.get('endTime','') or '') for e in eps) if eps else '?'
                print(f"  Sub {sub_id}: {len(eps)} eps, latest {last_date[:10]}")
            time.sleep(0.8)
        elif r.status_code == 429:
            print(f"  Sub {sub_id}: rate limited, waiting...")
            time.sleep(10)
        else:
            print(f"  Sub {sub_id}: {r.status_code}")
    except Exception as e:
        print(f"  Sub {sub_id}: error {e}")

print(f"\nSep episodes found in first pass: {len(sep_episodes_found)}")
print(f"New sub IDs discovered: {len(all_new_sub_ids) - len(all_sub_ids_to_try)}")

# ===== STEP 4: If we found Sep episodes, get team info =====
# Load teams.csv for team name lookup
teams_lookup = {}
with open(GEORGYMAMARIN / "teams.csv", encoding='utf-8') as f:
    for row in csv.DictReader(f):
        teams_lookup[str(row['team_id'])] = row['team_name']

if sep_episodes_found:
    print("\n=== Sep Episodes Found ===")
    for eid, ep in sorted(sep_episodes_found.items(), key=lambda x: x[1].get('endTime',''))[:30]:
        agents = ep.get('agents', [])
        team_names = [teams_lookup.get(str(a.get('teamId','')), f"tid:{a.get('teamId')}") for a in agents]
        end = (ep.get('endTime','') or '')[:16]
        print(f"  ep {eid} | {end} | {' vs '.join(team_names)}")
    
    # ===== STEP 5: Download Sep elite replays =====
    print(f"\n=== STEP 5: Download {len(sep_episodes_found)} Sep replays ===")
    downloaded = 0
    for ep_id in list(sep_episodes_found.keys())[:100]:
        out_path = REPLAY_OUT / f"sep_elite_{ep_id}.json.gz"
        if out_path.exists():
            downloaded += 1
            continue
        url = REPLAY_URL.format(id=ep_id)
        try:
            r = session.get(url, timeout=60)
            if r.status_code == 200:
                out_path.write_bytes(gzip.compress(r.content, 6))
                print(f"  [OK] ep {ep_id}: {len(r.content)//1024:,} KB")
                downloaded += 1
            else:
                print(f"  [{r.status_code}] ep {ep_id}")
            time.sleep(0.5)
        except Exception as e:
            print(f"  [ERR] ep {ep_id}: {e}")
    
    print(f"\nDownloaded: {downloaded}")
else:
    print("\nNO September episodes found in first pass.")
    print("Trying to query newly discovered sub IDs...")
    
    # Try the newly discovered sub IDs
    new_only = all_new_sub_ids - all_sub_ids_to_try
    print(f"New sub IDs to try: {len(new_only)}")
    for sub_id in sorted(new_only, reverse=True)[:30]:
        try:
            r = session.post(LIST_URL, json={"submissionId": int(sub_id)}, timeout=30)
            if r.status_code == 200:
                eps = r.json().get("episodes", [])
                sep_eps = [e for e in eps if (e.get('endTime') or '') >= '2026-09-01']
                if sep_eps:
                    print(f"  Sub {sub_id}: FOUND {len(sep_eps)} Sep episodes!")
                    for e in sep_eps[:3]:
                        agents = e.get('agents', [])
                        tn = [teams_lookup.get(str(a.get('teamId','')), '?') for a in agents]
                        print(f"    ep {e.get('id')} | {(e.get('endTime','') or '')[:10]} | {tn}")
                        sep_episodes_found[str(e['id'])] = e
                else:
                    last = max((e.get('endTime','') or '') for e in eps) if eps else '?'
                    print(f"  Sub {sub_id}: {len(eps)} eps, latest {last[:10]}")
                time.sleep(0.8)
            elif r.status_code == 429:
                time.sleep(10)
        except Exception as e:
            print(f"  Sub {sub_id}: {e}")

print(f"\n=== FINAL: Sep episodes discovered: {len(sep_episodes_found)} ===")
print(f"Files downloaded: {len(list(REPLAY_OUT.glob('*.json.gz')))}")

# Save summary
with open(OUT_DIR / 'sep_discovery_result.json', 'w') as f:
    json.dump({
        'sep_episodes_count': len(sep_episodes_found),
        'sep_episodes': list(sep_episodes_found.values()),
        'sub_ids_tried': len(all_sub_ids_to_try),
        'new_sub_ids_discovered': len(all_new_sub_ids - all_sub_ids_to_try),
    }, f, indent=2)
