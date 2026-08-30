import os, json, glob

root = r"c:\Users\Sundareswaran\Kagriculture"
replays = [f for f in os.listdir(root) if f.endswith("_replay.json")]

print(f"Found {len(replays)} replay files:")

summary = []

for rf in sorted(replays):
    fp = os.path.join(root, rf)
    size_mb = os.path.getsize(fp) / (1024 * 1024)
    try:
        with open(fp, 'r') as f:
            data = json.load(f)
        
        # Extract basic info
        steps = data.get("steps", [])
        num_steps = len(steps)
        if num_steps > 0:
            final_step = steps[-1]
            r0 = final_step[0].get("reward")
            r1 = final_step[1].get("reward")
            
            # Farm 0 and Farm 1 final states
            f0 = final_step[0].get("observation", {}).get("farms", [{}])[0]
            f1 = final_step[0].get("observation", {}).get("farms", [{}, {}])[1]
            
            summary.append({
                "file": rf,
                "size_mb": round(size_mb, 2),
                "steps": num_steps,
                "reward_p0": r0,
                "reward_p1": r1,
                "winner": "P0" if (r0 or 0) > (r1 or 0) else ("P1" if (r1 or 0) > (r0 or 0) else "TIE"),
                "f0_money": f0.get("money"),
                "f1_money": f1.get("money"),
                "f0_land": f0.get("unlocked_quadrants"),
                "f1_land": f1.get("unlocked_quadrants"),
                "f0_hands": len(f0.get("hands", [])),
                "f1_hands": len(f1.get("hands", [])),
            })
    except Exception as e:
        summary.append({"file": rf, "size_mb": round(size_mb, 2), "error": str(e)})

print(json.dumps(summary, indent=2))
