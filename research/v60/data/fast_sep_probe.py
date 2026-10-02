#!/usr/bin/env python3
"""V60 — Fast Sep submission ID probe. NO CSV LOADING.
Directly probes submission IDs above the Aug ceiling via ListEpisodes.
Stops immediately when Sep episodes are found and downloads them.
"""
import gzip, json, sys, time, requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

OUT_DIR = Path("research/v60/data")
REPLAY_OUT = OUT_DIR / "sep_replays"
REPLAY_OUT.mkdir(parents=True, exist_ok=True)

LIST_URL = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{id}.json"

session = requests.Session()
session.headers["User-Agent"] = "kaggriculture-v60-research"

MAX_AUG_SUB = 55924458  # Highest known Aug submission ID

# Probe strategy: scan dense around and just above the Aug ceiling
# Sep submissions will appear right after the last Aug ones

sep_episodes = {}
sep_sub_ids = []

# Dense probe: IDs from 55924459 to 55974459 in steps of 50 (faster, finer resolution)
probe_ids = list(range(MAX_AUG_SUB + 1, MAX_AUG_SUB + 50001, 50))
print(f"Probing {len(probe_ids)} IDs from {probe_ids[0]} to {probe_ids[-1]}, step=50")
print(f"Timeout per request: 10s (fast fail)")

found = 0
hits = 0
for i, sub_id in enumerate(probe_ids):
    if i % 50 == 0:
        print(f"  [{i}/{len(probe_ids)}] sub={sub_id}  sep_found={found}  valid_subs={hits}", flush=True)
    
    try:
        r = session.post(LIST_URL, json={"submissionId": int(sub_id)}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            eps = data.get("episodes", [])
            if eps:
                hits += 1
                sep_eps = [e for e in eps if (e.get('endTime') or '').startswith('2026-09')]
                last_ep = max((e.get('endTime','') or '') for e in eps)
                if sep_eps:
                    print(f"  *** SEP FOUND: sub {sub_id} -> {len(sep_eps)} Sep eps (latest: {last_ep[:10]})")
                    sep_sub_ids.append(sub_id)
                    found += len(sep_eps)
                    for e in sep_eps:
                        eid = str(e.get('id', ''))
                        if eid:
                            sep_episodes[eid] = e
                    # Discover more sub IDs from opponent agents
                    for e in sep_eps:
                        for a in e.get('agents', []):
                            new_sid = a.get('submissionId')
                            if new_sid and new_sid not in probe_ids:
                                probe_ids.append(new_sid)
                else:
                    pass  # Has eps but not Sep
            time.sleep(0.25)
        elif r.status_code == 429:
            print(f"  Rate limited at sub {sub_id}, sleeping 20s...")
            time.sleep(20)
        # 404 = sub doesn't exist, skip instantly
    except requests.exceptions.Timeout:
        pass  # 10s timeout, skip
    except Exception as e:
        print(f"  Sub {sub_id}: {e}")
        time.sleep(0.5)

print(f"\n=== SCAN COMPLETE ===")
print(f"Probed: {len(probe_ids)} IDs")
print(f"Valid submissions found: {hits}")
print(f"Sep sub IDs: {sep_sub_ids}")
print(f"Sep episodes: {len(sep_episodes)}")

if sep_episodes:
    # Show team names - get from CDN
    print(f"\nDownloading {min(30, len(sep_episodes))} Sep replays to identify teams...")
    TARGET_TEAMS = {
        "DSM", "Vadim Vasilenko", "Majkel1337", "Unknown Mother-Goose",
        "THIRD FARM CLUB", "M & M & P & Q", "Kaggledew Valley",
        "Yannik Schiffner", "KawattaTaido", "ymg_aq", "Otter Vibe",
        "mtmr_s1", "QQ", "DECEM", "DeeperNet", "Orbital Terraformer",
    }
    
    teams_found = set()
    for ep_id in list(sep_episodes.keys())[:30]:
        out = REPLAY_OUT / f"sep_{ep_id}.json.gz"
        if not out.exists():
            try:
                r = session.get(REPLAY_URL.format(id=ep_id), timeout=30)
                if r.status_code == 200:
                    out.write_bytes(gzip.compress(r.content, 6))
                    data = r.json()
                    teams = data.get('info', {}).get('TeamNames', [])
                    ep = sep_episodes[ep_id]
                    end = (ep.get('endTime','') or '')[:10]
                    elite = [t for t in teams if t in TARGET_TEAMS]
                    print(f"  ep {ep_id} | {end} | {teams} {'*** ELITE: ' + str(elite) if elite else ''}")
                    teams_found.update(teams)
                time.sleep(0.3)
            except Exception as e:
                print(f"  {ep_id}: {e}")
    
    print(f"\nAll teams in Sep replays: {teams_found}")
    elite_present = teams_found & TARGET_TEAMS
    print(f"Elite teams present: {elite_present}")

with open(OUT_DIR / 'sep_scan_result.json', 'w') as f:
    json.dump({
        'max_aug_sub': MAX_AUG_SUB,
        'probe_range': [probe_ids[0], probe_ids[-1]],
        'valid_subs_hit': hits,
        'sep_sub_ids': sep_sub_ids,
        'sep_episodes_count': len(sep_episodes),
        'sep_episodes': list(sep_episodes.values()),
    }, f, indent=2)
print(f"\nSaved to sep_scan_result.json")
print(f"Files in sep_replays: {len(list(REPLAY_OUT.glob('*.json.gz')))}")
