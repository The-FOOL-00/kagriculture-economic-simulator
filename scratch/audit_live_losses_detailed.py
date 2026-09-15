import json
import os
import glob

def main():
    manifest = json.load(open("scratch/live_episodes_manifest.json", encoding="utf-8"))
    
    replay_files = {
        os.path.basename(f).replace("episode_", "").replace(".json", ""): f
        for f in glob.glob("replays/live_tournament/*.json")
    }
    
    losses = []
    all_matches = []
    
    for sid, eps in manifest.items():
        for ep in eps:
            ep_id = str(ep["id"])
            agents = ep["agents"]
            us = next((a for a in agents if a.get("submissionId") == int(sid)), None)
            them = next((a for a in agents if a.get("submissionId") != int(sid)), None)
            if not us or not them:
                continue
            rew_us = us.get("reward") or 0
            rew_them = them.get("reward") or 0
            margin = rew_us - rew_them
            
            opp_sub = them.get("submissionId")
            opp_score = them.get("initialScore")
            
            entry = {
                "sub_id": sid,
                "ep_id": ep_id,
                "us_cash": rew_us,
                "them_cash": rew_them,
                "margin": margin,
                "opp_sub": opp_sub,
                "opp_score": opp_score,
                "has_replay": ep_id in replay_files,
                "replay_path": replay_files.get(ep_id)
            }
            all_matches.append(entry)
            if margin < 0:
                losses.append(entry)
                
    losses.sort(key=lambda x: x["margin"])
    print(f"Total Matches: {len(all_matches)}")
    print(f"Total Losses: {len(losses)}")
    print(f"Losses with downloaded replays: {sum(1 for l in losses if l['has_replay'])}")
    
    print("\n" + "="*90)
    print("TOP 20 WORST LOSSES IN MANIFEST:")
    print("="*90)
    for i, l in enumerate(losses[:20]):
        replay_str = "[REPLAY READY]" if l["has_replay"] else "[NO REPLAY]"
        print(f"{i+1:2d}. Ep {l['ep_id']} | Sub {l['sub_id']} | Us: ${l['us_cash']:7,.0f} vs Opp {l['opp_sub']}: ${l['them_cash']:7,.0f} | Margin: ${l['margin']:+8,.0f} | OppRating: {l['opp_score']} | {replay_str}")

    # Check opponent breakdown among losses
    from collections import defaultdict
    opp_loss_count = defaultdict(int)
    opp_loss_margin = defaultdict(float)
    for l in losses:
        opp_loss_count[l["opp_sub"]] += 1
        opp_loss_margin[l["opp_sub"]] += l["margin"]
        
    print("\n" + "="*90)
    print("OPPONENTS CAUSING MOST LOSSES:")
    print("="*90)
    opp_sorted = sorted(opp_loss_count.items(), key=lambda x: opp_loss_margin[x[0]])
    for opp, count in opp_sorted[:10]:
        print(f"Opponent {opp}: {count} losses, Total Margin: ${opp_loss_margin[opp]:+,.0f}, Avg Margin: ${opp_loss_margin[opp]/count:+,.0f}")

if __name__ == "__main__":
    main()
