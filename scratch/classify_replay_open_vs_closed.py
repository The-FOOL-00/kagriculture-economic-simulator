import os
import glob
import json

def test_action_tape_uniformity():
    # Let's find episodes for Whyme, Yuan800, MtN, Crop Dusta, Kawatta
    replays = glob.glob("replays/**/*.json", recursive=True) + glob.glob("scratch/**/*.json", recursive=True)
    
    agent_episodes = {
        "Crop Dusta": [],
        "Whyme Labs": [],
        "Yuan800": [],
        "MtN": [],
        "KawattaTaido": [],
        "Eldritch": []
    }
    
    for r in replays:
        if any(x in r for x in ["manifest", "results", "scoreboard", "summary", "crosscheck", "audit", "leaderboard", "holdout"]):
            continue
        try:
            if os.path.getsize(r) < 10000 or os.path.getsize(r) > 40000000:
                continue
            with open(r, "r", encoding="utf-8") as f:
                data = json.load(f)
            steps = data.get("steps")
            if not steps or len(steps) < 100:
                continue
            agents = data.get("agents") or data.get("info", {}).get("Agents") or []
            
            for idx, ag in enumerate(agents):
                name = ag.get("name") if isinstance(ag, dict) else str(ag)
                for target in agent_episodes.keys():
                    if target.lower() in str(name).lower() or target.lower() in r.lower():
                        # Extract first 50 actions
                        actions = []
                        for s in steps[:100]:
                            if isinstance(s, list) and len(s) > idx:
                                act = s[idx].get("action")
                                actions.append(str(act))
                        agent_episodes[target].append({
                            "file": os.path.basename(r),
                            "p_idx": idx,
                            "actions_sample": actions[:50]
                        })
        except Exception as e:
            pass
            
    print("Action Uniformity Analysis:")
    for ag, eps in agent_episodes.items():
        print(f"\n--- {ag} ({len(eps)} episodes found) ---")
        if len(eps) < 2:
            print(f"  Only {len(eps)} episode found; cannot compare across seeds.")
            continue
        # Compare first 30 actions between episode 0 and episode 1..N
        ref_actions = eps[0]["actions_sample"]
        identical_count = 0
        for ep in eps[1:]:
            diffs = sum(1 for a1, a2 in zip(ref_actions, ep["actions_sample"]) if a1 != a2)
            if diffs == 0:
                identical_count += 1
        print(f"  Identical action sequences in first 50 steps: {identical_count} / {len(eps)-1}")
        if identical_count == len(eps) - 1:
            print(f"  -> CLASSIFICATION: OPEN-LOOP REPLAY TAPE (100% deterministic / static across seeds)")
        else:
            print(f"  -> CLASSIFICATION: CLOSED-LOOP or ADAPTIVE (Diverges across matches/opponents)")

if __name__ == "__main__":
    test_action_tape_uniformity()
