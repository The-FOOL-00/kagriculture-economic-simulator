#!/usr/bin/env python3
"""V60 — Analyze keep replay index. Forces UTF-8 output."""
import json
import sys
from collections import Counter
from pathlib import Path

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

with open('research/v60/data/keep_replay_index.json') as f:
    idx = json.load(f)

valid = [r for r in idx if 'error' not in r]
print(f"Valid replays: {len(valid)}")

# Get all unique opponents
opps = {}
for r in valid:
    opp = r.get('opp_team')
    if opp and opp != 'Eldritch':
        opps[opp] = opps.get(opp, 0) + 1

print(f"Unique opponents (non-Eldritch): {len(opps)}")

# Episode ID range
ep_ids = sorted(r['ep_id'] for r in valid if r.get('ep_id'))
print(f"Episode ID range: {ep_ids[0]} - {ep_ids[-1]}")

# Seeds
seeds = sorted(set(r['seed'] for r in valid if r.get('seed') is not None))
print(f"Seeds: {len(seeds)} unique, range {min(seeds)}-{max(seeds)}")

# Module versions
versions = set(r.get('module_version') for r in valid)
print(f"Module versions: {versions}")

# Prefix breakdown
by_prefix = {}
for r in valid:
    p = r.get('prefix', 'unknown')
    by_prefix.setdefault(p, []).append(r)
print(f"\nPrefix breakdown:")
for p, recs in sorted(by_prefix.items()):
    print(f"  {p}: {len(recs)} replays")

# Top opponents
print(f"\nTop 50 most frequent opponents:")
for opp, count in sorted(opps.items(), key=lambda x: -x[1])[:50]:
    print(f"  {count}x  {opp}")

# Sep 22 top teams check
TOP_TEAMS = {
    "DSM", "Vadim Vasilenko", "Majkel1337", "Unknown Mother-Goose",
    "THIRD FARM CLUB", "M & M & P & Q", "Kaggledew Valley",
    "Yannik Schiffner", "KawattaTaido", "ymg_aq", "Otter Vibe",
    "mtmr_s1", "QQ", "DECEM", "THUNDER THUNDER",
    "Azat Akhtyamov", "Sida Zuo", "Planned Economy", "DeeperNet",
    "Orbital Terraformer", "midnq", "SpaTaro", "Ryo Hasegawa",
    "RS Turley", "Densike", "TheEggman", "kwa"
}

found_elite = set(opps.keys()) & TOP_TEAMS
print(f"\nElite Sep 22 teams found in local replays: {found_elite}")

missing_elite = TOP_TEAMS - set(opps.keys())
print(f"Missing elite teams: {len(missing_elite)}")
for t in sorted(missing_elite):
    print(f"  - {t}")

# Determine episode IDs in range to show where Sep starts
# Episodes 111295878 - 112016921
# What is the date of the first and last?
# From the a7_episodes.json, a7 episodes are from Sep 22 (createTime 2026-09-22)
# From the v22r1 prefix, let's look at the range of IDs
a7_eps = [r for r in valid if r.get('prefix') == 'a7']
v22_eps = [r for r in valid if r.get('prefix') == 'v22r1']
a7_ids = sorted(r['ep_id'] for r in a7_eps if r.get('ep_id'))
v22_ids = sorted(r['ep_id'] for r in v22_eps if r.get('ep_id'))
print(f"\na7 episode IDs: {a7_ids[0]} - {a7_ids[-1]}" if a7_ids else "no a7")
print(f"v22r1 episode IDs: {v22_ids[0]} - {v22_ids[-1]}" if v22_ids else "no v22r1")
