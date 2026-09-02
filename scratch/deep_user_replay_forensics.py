import json
import os
import glob
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def deep_forensics():
    files = glob.glob("replays/episode-*.json")
    print(f"Deep analyzing {len(files)} user replay matches...")
    
    match_reports = []
    
    for fpath in sorted(files):
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        ep_id = data.get("id")
        num_ep_id = data.get("info", {}).get("EpisodeId")
        module_version = data.get("module_version")
        team_names = data.get("info", {}).get("TeamNames", ["Unknown", "Unknown"])
        seed = data.get("info", {}).get("seed")
        rewards = data.get("rewards", [0, 0])
        statuses = data.get("statuses", ["", ""])
        steps = data.get("steps", [])
        
        user_idx = 1
        opp_idx = 0
        user_name = "Sundareswaran Rajaguru"
        for idx, name in enumerate(team_names):
            if user_name.lower() in name.lower():
                user_idx = idx
                opp_idx = 1 - idx
                break
                
        user_score = rewards[user_idx]
        opp_score = rewards[opp_idx]
        opp_name = team_names[opp_idx]
        won = user_score > opp_score
        draw = user_score == opp_score
        margin = user_score - opp_score
        
        # Action aggregations
        user_animals = {"COW": 0, "SHEEP": 0, "GOOSE": 0}
        opp_animals = {"COW": 0, "SHEEP": 0, "GOOSE": 0}
        user_seeds = {}
        opp_seeds = {}
        user_land_buys = 0
        opp_land_buys = 0
        user_hires = 0
        opp_hires = 0
        
        day_snapshots = {}
        
        for step_i, step in enumerate(steps):
            day = step_i // 24
            hour = step_i % 24
            
            u_obs = step[user_idx].get("observation", {})
            o_obs = step[opp_idx].get("observation", {})
            
            u_act = step[user_idx].get("action", {})
            o_act = step[opp_idx].get("action", {})
            
            # Parse market actions
            if u_act and isinstance(u_act, dict):
                for m_act in u_act.get("market", []):
                    if isinstance(m_act, list) and len(m_act) > 0:
                        cmd = m_act[0]
                        if cmd == "HIRE":
                            user_hires += 1
                        elif cmd == "BUY_LAND":
                            user_land_buys += 1
                        elif cmd == "BUY_ANIMAL" and len(m_act) >= 3:
                            atype = m_act[1]
                            acnt = m_act[2]
                            user_animals[atype] = user_animals.get(atype, 0) + acnt
                        elif cmd == "BUY_SEED" and len(m_act) >= 3:
                            stype = m_act[1]
                            scnt = m_act[2]
                            user_seeds[stype] = user_seeds.get(stype, 0) + scnt
            
            if o_act and isinstance(o_act, dict):
                for m_act in o_act.get("market", []):
                    if isinstance(m_act, list) and len(m_act) > 0:
                        cmd = m_act[0]
                        if cmd == "HIRE":
                            opp_hires += 1
                        elif cmd == "BUY_LAND":
                            opp_land_buys += 1
                        elif cmd == "BUY_ANIMAL" and len(m_act) >= 3:
                            atype = m_act[1]
                            acnt = m_act[2]
                            opp_animals[atype] = opp_animals.get(atype, 0) + acnt
                        elif cmd == "BUY_SEED" and len(m_act) >= 3:
                            stype = m_act[1]
                            scnt = m_act[2]
                            opp_seeds[stype] = opp_seeds.get(stype, 0) + scnt
            
            # Record snapshot at end of day
            if hour == 23 or step_i == len(steps) - 1:
                u_cash = None
                o_cash = None
                if "farms" in u_obs and len(u_obs["farms"]) > user_idx:
                    u_cash = u_obs["farms"][user_idx].get("money")
                if "farms" in o_obs and len(o_obs["farms"]) > opp_idx:
                    o_cash = o_obs["farms"][opp_idx].get("money")
                    
                day_snapshots[f"Day_{day}"] = {
                    "user_cash": u_cash,
                    "opp_cash": o_cash
                }
        
        # Loss / Win forensic classification
        classification = "UNKNOWN"
        root_cause = ""
        
        if not won:
            # Loss analysis
            if opp_animals.get("COW", 0) + opp_animals.get("SHEEP", 0) > 0 and user_animals.get("COW", 0) + user_animals.get("SHEEP", 0) == 0:
                classification = "LIVESTOCK"
                root_cause = "Opponent scaled livestock while user had zero"
            elif opp_land_buys > user_land_buys + 1:
                classification = "LAND"
                root_cause = f"Opponent bought {opp_land_buys} land vs user {user_land_buys}"
            elif opp_hires > user_hires:
                classification = "WORKERS"
                root_cause = f"Opponent hired {opp_hires} workers vs user {user_hires}"
            elif user_animals.get("COW", 0) > 0 and user_score < 15000:
                classification = "FEED / STARVATION"
                root_cause = "User bought cows but cash collapsed / feed starved"
            elif sum(opp_seeds.values()) > sum(user_seeds.values()) * 1.5:
                classification = "CROP MIX / THROUGHPUT"
                root_cause = f"Opponent bought {sum(opp_seeds.values())} seeds vs user {sum(user_seeds.values())}"
            else:
                classification = "ECONOMIC EXECUTION"
                root_cause = "General velocity / town sales / market timing advantage"
        else:
            # Win analysis
            if user_animals.get("COW", 0) > 0 and opp_animals.get("COW", 0) == 0:
                classification = "LIVESTOCK DOMINANCE"
                root_cause = "User cow/milk engine outscaled opponent"
            elif user_score > 50000:
                classification = "HIGH THROUGHPUT HARVEST"
                root_cause = "Massive harvest and town liquidation"
            else:
                classification = "OPPONENT BLUNDER"
                root_cause = f"Opponent failed to scale ({opp_score} pts)"
                
        report = {
            "file": os.path.basename(fpath),
            "ep_id": num_ep_id or ep_id,
            "seed": seed,
            "user_seat": f"P{user_idx}",
            "opp_name": opp_name,
            "user_score": user_score,
            "opp_score": opp_score,
            "margin": margin,
            "won": won,
            "user_animals": user_animals,
            "opp_animals": opp_animals,
            "user_seeds": user_seeds,
            "opp_seeds": opp_seeds,
            "user_land": user_land_buys,
            "opp_land": opp_land_buys,
            "user_hires": user_hires,
            "opp_hires": opp_hires,
            "classification": classification,
            "root_cause": root_cause,
            "day_snapshots": day_snapshots
        }
        match_reports.append(report)
        
    print(f"\nAnalyzed {len(match_reports)} matches.")
    
    losses = [m for m in match_reports if not m["won"]]
    wins = [m for m in match_reports if m["won"]]
    
    print("\n==========================================")
    print(f"=== LOSS FORENSICS BREAKDOWN ({len(losses)} Losses) ===")
    print("==========================================")
    loss_classes = {}
    for l in losses:
        c = l["classification"]
        loss_classes[c] = loss_classes.get(c, 0) + 1
        print(f"Match vs {l['opp_name']:<25} | Score: {l['user_score']:6.0f} vs {l['opp_score']:6.0f} ({l['margin']:+7.0f}) | Seat: {l['user_seat']} | Class: {l['classification']:<22} | Cause: {l['root_cause']}")
        
    print("\nLoss Category Frequency:")
    for k, v in sorted(loss_classes.items(), key=lambda x: -x[1]):
        print(f"  {k:<25}: {v} ({v/len(losses)*100:.1f}%)")
        
    print("\n==========================================")
    print(f"=== WIN FORENSICS BREAKDOWN ({len(wins)} Wins) ===")
    print("==========================================")
    win_classes = {}
    for w in wins:
        c = w["classification"]
        win_classes[c] = win_classes.get(c, 0) + 1
        print(f"Match vs {w['opp_name']:<25} | Score: {w['user_score']:6.0f} vs {w['opp_score']:6.0f} ({w['margin']:+7.0f}) | Seat: {w['user_seat']} | Class: {w['classification']:<22} | Cause: {w['root_cause']}")
        
    print("\nWin Category Frequency:")
    for k, v in sorted(win_classes.items(), key=lambda x: -x[1]):
        print(f"  {k:<25}: {v} ({v/len(wins)*100:.1f}%)")

    os.makedirs("scratch", exist_ok=True)
    with open("scratch/deep_user_match_reports.json", "w", encoding="utf-8") as f:
        json.dump(match_reports, f, indent=2)

if __name__ == "__main__":
    deep_forensics()
