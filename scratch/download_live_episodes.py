import requests
import json
import os
import sys

sub_ids = [56146971, 56146947]
LIST_URL = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"

all_data = {}

for sid in sub_ids:
    print(f"Fetching episodes for submission {sid}...")
    r = requests.post(LIST_URL, json={"submissionId": sid}, timeout=30)
    if r.status_code == 200:
        data = json.loads(r.content.decode("utf-8"))
        episodes = data.get("episodes", [])
        print(f"  Found {len(episodes)} episodes for submission {sid}")
        all_data[str(sid)] = episodes
    else:
        print(f"  Error: {r.status_code}")

out_file = "scratch/live_episodes_manifest.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=2)

print(f"Saved manifest to {out_file}")

# Summarize matches
for sid, eps in all_data.items():
    print(f"\n==========================================")
    print(f"SUBMISSION {sid} (Total: {len(eps)} matches)")
    print(f"==========================================")
    wins = 0
    losses = 0
    ties = 0
    total_margin = 0
    rewards_us = []
    rewards_them = []
    
    for ep in eps:
        ep_id = ep["id"]
        agents = ep["agents"]
        # Determine our agent and opponent agent
        us = None
        them = None
        for a in agents:
            if a.get("submissionId") == int(sid):
                us = a
            else:
                them = a
        if not us or not them:
            continue
        
        rew_us = us.get("reward", 0)
        rew_them = them.get("reward", 0)
        if rew_us is None: rew_us = 0
        if rew_them is None: rew_them = 0
        
        rewards_us.append(rew_us)
        rewards_them.append(rew_them)
        
        margin = rew_us - rew_them
        total_margin += margin
        
        opp_sub = them.get("submissionId")
        opp_team = them.get("teamId")
        opp_score = them.get("initialScore", 0)
        
        result = "WIN" if margin > 0 else ("LOSS" if margin < 0 else "TIE")
        if margin > 0: wins += 1
        elif margin < 0: losses += 1
        else: ties += 1
        
        print(f"Ep {ep_id} | {result:4} | Us: ${rew_us:6,d} vs Opp: ${rew_them:6,d} (Margin ${margin:+7,d}) | OppSub: {opp_sub} (Rating: {opp_score:.1f})")

    n = len(rewards_us)
    if n > 0:
        mean_us = sum(rewards_us) / n
        mean_them = sum(rewards_them) / n
        mean_margin = total_margin / n
        wr = (wins / n) * 100
        print(f"\nSummary for {sid}:")
        print(f"  Record: {wins}W / {losses}L / {ties}T (Win Rate: {wr:.1f}%)")
        print(f"  Mean Cash Us:   ${mean_us:,.2f}")
        print(f"  Mean Cash Opp:  ${mean_them:,.2f}")
        print(f"  Mean Margin:    ${mean_margin:+,.2f}")
