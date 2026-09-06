import json

def trace_yuyajk(fpath):
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    steps = data.get("steps")
    print(f"\n=======================================================")
    print(f"YUTAJK vs V2 MELON WAVE (Steps 240-270): {fpath}")
    print(f"=======================================================")
    for s in range(240, 271):
        step = steps[s]
        d = s // 24
        h = s % 24
        for p in [0, 1]:
            act = step[p].get("action", {})
            m_acts = act.get("market", []) if isinstance(act, dict) else []
            farm = step[p].get("observation", {}).get("farms", [{}])[p]
            money = farm.get("money", 0) if isinstance(farm, dict) else 0
            if m_acts:
                print(f"Step {s:3d} (D{d:02d}:H{h:02d}) | P{p} (Cash: ${money:7.1f}) -> {m_acts}")

trace_yuyajk("scratch/replays/V2_Loss_vs_Yuyajk_104810879.json")
