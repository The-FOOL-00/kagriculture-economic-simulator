#!/usr/bin/env python3
"""V60 — Direct approach: Download our own Sep 22 episodes from CDN to get opponent IDs.

The kaggleusercontent CDN is public - no auth needed.
Our Sep 22 episode IDs are in:
  live_data/episodes_v31r2/v22r1_episodes.json (238 episodes)
  live_data/episodes_v31r2/a7_episodes.json (83 episodes)

We download a sample of these, parse agent submissionIds from the JSON,
then ListEpisodes for each opponent to find their Sep episodes.
Then we ListEpisodes for a wider graph to discover Sep 22 top teams.
"""
import csv, gzip, json, sys, time, requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

OUT_DIR = Path("research/v60/data")
REPLAY_OUT = OUT_DIR / "sep_replays"
REPLAY_OUT.mkdir(parents=True, exist_ok=True)
TMP_DIR = OUT_DIR / "tmp_ep_jsons"
TMP_DIR.mkdir(parents=True, exist_ok=True)

LIST_URL = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{id}.json"

session = requests.Session()
session.headers["User-Agent"] = "kaggriculture-v60-research"

# Target teams
TARGET_TEAMS = {
    "DSM", "Vadim Vasilenko", "Majkel1337", "Unknown Mother-Goose",
    "THIRD FARM CLUB", "M & M & P & Q", "Kaggledew Valley",
    "Yannik Schiffner", "KawattaTaido", "ymg_aq", "Otter Vibe",
    "mtmr_s1", "QQ", "DECEM", "THUNDER THUNDER",
    "Azat Akhtyamov", "Sida Zuo", "Planned Economy", "DeeperNet",
    "Orbital Terraformer", "midnq", "SpaTaro", "Ryo Hasegawa",
    "RS Turley", "Densike", "TheEggman", "kwa"
}

# ===== STEP 1: Download 50 of our Sep 22 episodes to extract opponent sub IDs =====
print("=== STEP 1: Download our Sep 22 episodes from CDN ===")

with open("live_data/episodes_v31r2/v22r1_episodes.json") as f:
    v22_eps = json.load(f)

sample_ep_ids = [ep['id'] for ep in v22_eps[:80]]  # First 80
print(f"Sample episode IDs: {sample_ep_ids[:5]}...")

downloaded_replays = []
opp_sub_ids = set()

for ep_id in sample_ep_ids:
    cache_path = TMP_DIR / f"{ep_id}.json"
    if cache_path.exists():
        with open(cache_path) as f:
            data = json.load(f)
        downloaded_replays.append(data)
    else:
        url = REPLAY_URL.format(id=ep_id)
        try:
            r = session.get(url, timeout=60)
            if r.status_code == 200:
                data = r.json()
                cache_path.write_text(json.dumps(data))
                downloaded_replays.append(data)
                # Extract opponent sub IDs
                info = data.get('info', {})
                agents_info = info.get('Agents', [])
                # Also check configuration
                config = data.get('configuration', {})
                print(f"  ep {ep_id}: got {len(data.get('steps',[]))} steps, "
                      f"teams: {info.get('TeamNames', [])}")
            elif r.status_code == 403:
                print(f"  ep {ep_id}: 403 Forbidden")
                break
            else:
                print(f"  ep {ep_id}: {r.status_code}")
            time.sleep(0.3)
        except Exception as e:
            print(f"  ep {ep_id}: error {e}")

print(f"\nDownloaded: {len(downloaded_replays)} replays")

# ===== STEP 2: Parse team names and look for opponents =====
print("\n=== STEP 2: Extract opponent team names ===")
all_opponents = {}  # team_name -> count
for data in downloaded_replays:
    info = data.get('info', {})
    teams = info.get('TeamNames', [])
    for t in teams:
        if t and t != 'Eldritch':  # Eldritch is our team
            all_opponents[t] = all_opponents.get(t, 0) + 1

print(f"Unique opponents in our Sep 22 replays: {len(all_opponents)}")
top_opps = sorted(all_opponents.items(), key=lambda x: -x[1])
for name, count in top_opps[:30]:
    marker = " *** TARGET ***" if name in TARGET_TEAMS else ""
    print(f"  {count}x {name}{marker}")

# ===== STEP 3: Use ListEpisodes with submission IDs from the georgymamarin state =====
# The state.json has 26,571 submissions. The most recent ones (highest IDs) are Sep submissions.
print("\n=== STEP 3: Query recent submissions from state.json ===")
with open("replays/raw/georgymamarin/state.json") as f:
    state = json.load(f)

all_state_subs = state['submissions']
# The most recent submissions will have the highest IDs
# Sort by sub ID descending to get most recent
recent_subs = sorted(set(all_state_subs), reverse=True)[:200]
print(f"Most recent 200 submission IDs: {recent_subs[:5]}...{recent_subs[-5:]}")

# Query these for Sep episodes
print(f"\nQuerying {len(recent_subs)} recent submissions for Sep episodes...")
sep_episodes_found = {}
target_sub_ids_with_sep = []

for i, sub_id in enumerate(recent_subs):
    if i % 20 == 0:
        print(f"  Progress: {i}/{len(recent_subs)}, sep found: {len(sep_episodes_found)}")
    
    try:
        r = session.post(LIST_URL, json={"submissionId": int(sub_id)}, timeout=30)
        if r.status_code == 200:
            eps = r.json().get("episodes", [])
            sep_eps = [e for e in eps if (e.get('endTime') or '').startswith('2026-09')]
            if sep_eps:
                print(f"  *** Sub {sub_id}: {len(sep_eps)} Sep episodes! (total: {len(eps)})")
                target_sub_ids_with_sep.append(sub_id)
                for e in sep_eps:
                    eid = str(e.get('id', ''))
                    if eid:
                        sep_episodes_found[eid] = e
                        # Discover new opponent sub IDs
                        for a in e.get('agents', []):
                            new_sid = a.get('submissionId')
                            if new_sid and new_sid not in recent_subs:
                                recent_subs.append(new_sid)
            time.sleep(0.6)
        elif r.status_code == 429:
            print(f"  Rate limited at sub {sub_id}, sleeping 10s...")
            time.sleep(10)
        else:
            pass  # Skip silent failures
    except Exception as e:
        print(f"  Sub {sub_id}: {e}")
        time.sleep(1)

print(f"\n=== Results from state.json subs ===")
print(f"Sep episodes found: {len(sep_episodes_found)}")
print(f"Submission IDs with Sep activity: {target_sub_ids_with_sep}")

# ===== STEP 4: Download Sep elite replays =====
if sep_episodes_found:
    print(f"\n=== STEP 4: Download {min(100, len(sep_episodes_found))} Sep replays ===")
    downloaded = 0
    for ep_id in list(sep_episodes_found.keys())[:100]:
        out_path = REPLAY_OUT / f"sep_{ep_id}.json.gz"
        if out_path.exists():
            downloaded += 1
            continue
        try:
            r = session.get(REPLAY_URL.format(id=ep_id), timeout=60)
            if r.status_code == 200:
                out_path.write_bytes(gzip.compress(r.content, 6))
                size = len(r.content) // 1024
                ep = sep_episodes_found[ep_id]
                agents = ep.get('agents', [])
                end = (ep.get('endTime','') or '')[:16]
                print(f"  [OK] ep {ep_id}: {size}KB | {end}")
                downloaded += 1
            else:
                print(f"  [{r.status_code}] ep {ep_id}")
            time.sleep(0.4)
        except Exception as e:
            print(f"  [ERR] {e}")
    print(f"Downloaded: {downloaded}")
else:
    print("\nStill no Sep episodes. Checking date ranges of recent subs...")
    # Sample 5 of the most recent submissions and print their date ranges
    for sub_id in recent_subs[:5]:
        try:
            r = session.post(LIST_URL, json={"submissionId": int(sub_id)}, timeout=30)
            if r.status_code == 200:
                eps = r.json().get("episodes", [])
                if eps:
                    dates = sorted(e.get('endTime','') or '' for e in eps)
                    print(f"  Sub {sub_id}: {len(eps)} eps, range {dates[0][:10]} - {dates[-1][:10]}")
            time.sleep(1)
        except Exception as e:
            print(f"  Sub {sub_id}: {e}")

# Save results
with open(OUT_DIR / 'sep_discovery_v2.json', 'w') as f:
    json.dump({
        'sep_episodes_count': len(sep_episodes_found),
        'target_subs_with_sep': target_sub_ids_with_sep,
        'opponents_in_our_sep22': dict(top_opps[:50]),
    }, f, indent=2)
print(f"\nSaved to {OUT_DIR}/sep_discovery_v2.json")
print(f"Replays in REPLAY_OUT: {len(list(REPLAY_OUT.glob('*.json.gz')))}")
